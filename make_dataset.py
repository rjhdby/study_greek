#!/usr/bin/env python3
"""
Script for generating audio files from a list of words/numbers using edge-tts.
Supports voice selection (male/female), trims silence at the end to 0.02 seconds.
"""

import argparse
import asyncio
from pathlib import Path

import edge_tts
from pydub import AudioSegment
from pydub.silence import detect_silence


VOICES = {
    "male": "el-GR-NestorasNeural",
    "female": "el-GR-AthinaNeural",
}
SILENCE_TAIL_MS = 20  # Keep 0.02 seconds of silence at the end
SILENCE_THRESHOLD = -40


def trim_silence(audio: AudioSegment, tail_ms: int = SILENCE_TAIL_MS, threshold: int = SILENCE_THRESHOLD) -> AudioSegment:
    """
    Trims the long silence tail at the end of audio, keeping tail_ms milliseconds.
    """
    # Use min_silence_len=100 to find real silence segments (like ffmpeg with d=0.1)
    silence_ranges = detect_silence(audio, min_silence_len=100, silence_thresh=threshold)
    
    if not silence_ranges:
        return audio
    
    # Check if there is silence at the end
    last_silence_start, last_silence_end = silence_ranges[-1]
    audio_length = len(audio)
    
    # If the last silence segment ends at the end of audio
    if last_silence_end >= audio_length - 10:  # 10 ms tolerance
        silence_duration = last_silence_end - last_silence_start
        
        if silence_duration > tail_ms:
            # Trim to silence start + tail_ms
            trim_point = last_silence_start + tail_ms
            return audio[:trim_point]
    
    return audio


async def generate_audio(text: str, output_path: Path, raw_dir: Path, voice: str) -> bool:
    """
    Generates an audio file for the given text using edge-tts.
    Saves raw file to raw_dir, trimmed file to output_path.
    """
    try:
        communicate = edge_tts.Communicate(text, voice)
        
        # Path for raw (untrimmed) file
        raw_path = raw_dir / f"{text}.mp3"
        
        # Save raw file from edge-tts
        await communicate.save(str(raw_path))
        
        # Load audio and trim silence
        audio = AudioSegment.from_mp3(str(raw_path))
        trimmed_audio = trim_silence(audio)
        
        # Save trimmed result
        trimmed_audio.export(output_path, format="mp3")
        
        return True
    except Exception as e:
        print(f"Error processing '{text}': {e}")
        return False


def trim_existing_file(file_path: Path) -> bool:
    """
    Trims silence in an existing audio file.
    """
    try:
        audio = AudioSegment.from_mp3(file_path)
        trimmed_audio = trim_silence(audio)
        trimmed_audio.export(file_path, format="mp3")
        return True
    except Exception as e:
        print(f"Error trimming silence in '{file_path}': {e}")
        return False


async def process_file(input_file: Path, output_dir: Path, gender: str) -> None:
    """
    Processes a file with a list of words/numbers.
    """
    voice = VOICES[gender]
    
    # Create output directory based on voice gender
    gender_output_dir = output_dir / gender
    gender_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create directory for raw (untrimmed) files
    raw_dir = output_dir / "raw" / gender
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Read words from file
    with open(input_file, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]
    
    print(f"Voice: {gender} ({voice})")
    print(f"Found {len(words)} words/numbers to process")
    print(f"Raw files saved to: {raw_dir}")
    
    for i, word in enumerate(words, 1):
        output_path = gender_output_dir / f"{word}.mp3"
        raw_path = raw_dir / f"{word}.mp3"
        print(f"[{i}/{len(words)}] Processing: {word}")
        
        # Priority check: 1) raw file, 2) trimmed file, 3) generate new
        if raw_path.exists():
            # Raw file exists - trim it and save to output
            print(f"  → Found raw file, trimming silence...")
            try:
                audio = AudioSegment.from_mp3(raw_path)
                trimmed_audio = trim_silence(audio)
                trimmed_audio.export(output_path, format="mp3")
                print(f"  ✓ Trimmed from raw: {output_path}")
            except Exception as e:
                print(f"  ✗ Error trimming raw file: {e}")
        elif output_path.exists():
            # No raw file, but trimmed exists - re-trim it
            print(f"  → File already exists, trimming silence...")
            success = trim_existing_file(output_path)
            if success:
                print(f"  ✓ Silence trimmed: {output_path}")
            else:
                print(f"  ✗ Error trimming silence: {word}")
        else:
            # No raw or trimmed file - generate new
            success = await generate_audio(word, output_path, raw_dir, voice)
            
            if success:
                print(f"  ✓ Saved: {output_path}")
            else:
                print(f"  ✗ Error processing: {word}")
    
    print(f"\nDone! Files saved to {gender_output_dir}")
    print(f"Raw files: {raw_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate audio files from a list of words using edge-tts"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to file with words/numbers (one per line)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("./audio"),
        help="Directory for saving audio files (default: ./audio)"
    )
    parser.add_argument(
        "-g", "--gender",
        choices=["male", "female", "all"],
        default="male",
        help="Voice gender: male (default), female, or all (both)"
    )
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"Error: file '{args.input_file}' not found")
        return 1
    
    if args.gender == "all":
        for gender in ["male", "female"]:
            asyncio.run(process_file(args.input_file, args.output, gender))
            print()  # Empty line between voices
    else:
        asyncio.run(process_file(args.input_file, args.output, args.gender))
    return 0


if __name__ == "__main__":
    exit(main())
