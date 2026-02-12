#!/usr/bin/env python3
"""
Script for trimming silence at the end of an audio file.
"""

import argparse
import subprocess
import json
from pathlib import Path


def get_audio_duration(file_path: str) -> float:
    """Gets the duration of an audio file in milliseconds."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", file_path
        ],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"]) * 1000


def detect_silence_end(file_path: str, threshold: int) -> float | None:
    """
    Finds the start of the last silence segment at the end of the file.
    Returns time in milliseconds or None if no silence is found.
    """
    result = subprocess.run(
        [
            "ffmpeg", "-i", file_path, "-af",
            f"silencedetect=noise={threshold}dB:d=0.1",
            "-f", "null", "-"
        ],
        capture_output=True, text=True
    )
    
    # Parse ffmpeg output to find silence_start
    lines = result.stderr.split('\n')
    silence_starts = []
    
    for line in lines:
        if "silence_start:" in line:
            try:
                start_str = line.split("silence_start:")[1].split()[0]
                silence_starts.append(float(start_str) * 1000)  # to milliseconds
            except (IndexError, ValueError):
                continue
    
    if silence_starts:
        return silence_starts[-1]  # Last silence segment
    return None


def trim_audio(input_path: str, output_path: str, end_ms: float) -> None:
    """Trims audio to the specified point."""
    end_seconds = end_ms / 1000
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-t", str(end_seconds),
            "-c:a", "libmp3lame", "-q:a", "2",
            output_path
        ],
        capture_output=True
    )


def main():
    parser = argparse.ArgumentParser(
        description="Trim silence at the end of an audio file"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input MP3 file"
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Output MP3 file"
    )
    parser.add_argument(
        "-t", "--threshold",
        type=int,
        default=-40,
        help="Silence threshold in decibels (default: -40)"
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=500,
        help="Maximum silence tail in milliseconds (default: 500)"
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: file '{args.input}' not found")
        return 1
    
    input_path = str(args.input)
    output_path = str(args.output)
    
    # Get audio duration
    duration = get_audio_duration(input_path)
    print(f"Duration: {duration:.0f} ms")
    
    # Find the start of silence at the end
    silence_start = detect_silence_end(input_path, args.threshold)
    
    if silence_start is None:
        print("No silence detected at the end, copying file without changes")
        subprocess.run(["cp", input_path, output_path])
        return 0
    
    print(f"Silence start: {silence_start:.0f} ms")
    
    silence_duration = duration - silence_start
    print(f"Silence duration: {silence_duration:.0f} ms")
    
    if silence_duration <= args.tail:
        print(f"Silence ({silence_duration:.0f} ms) does not exceed tail ({args.tail} ms), copying without changes")
        subprocess.run(["cp", input_path, output_path])
        return 0
    
    # Trim to silence_start + tail
    trim_point = silence_start + args.tail
    print(f"Trimming to: {trim_point:.0f} ms")
    
    trim_audio(input_path, output_path, trim_point)
    
    new_duration = get_audio_duration(output_path)
    print(f"New duration: {new_duration:.0f} ms")
    print(f"✓ Saved: {output_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
