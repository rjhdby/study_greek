#!/usr/bin/env python3
"""
Скрипт для генерации аудиофайлов из списка слов/цифр с использованием edge-tts.
Использует греческий голос el-GR-NestorasNeural, обрезает тишину в конце до 0.5 секунды.
"""

import argparse
import asyncio
from pathlib import Path

import edge_tts
from pydub import AudioSegment
from pydub.silence import detect_silence


VOICE = "el-GR-NestorasNeural"
SILENCE_TAIL_MS = 20  # Оставляем 0.02 секунды тишины в конце
SILENCE_THRESHOLD = -40


def trim_silence(audio: AudioSegment, tail_ms: int = SILENCE_TAIL_MS, threshold: int = SILENCE_THRESHOLD) -> AudioSegment:
    """
    Обрезает длинный хвост тишины в конце аудио, оставляя tail_ms миллисекунд.
    """
    # Используем min_silence_len=100 для поиска реальных участков тишины (как в ffmpeg с d=0.1)
    silence_ranges = detect_silence(audio, min_silence_len=100, silence_thresh=threshold)
    
    if not silence_ranges:
        return audio
    
    # Проверяем, есть ли тишина в конце
    last_silence_start, last_silence_end = silence_ranges[-1]
    audio_length = len(audio)
    
    # Если последний участок тишины заканчивается в конце аудио
    if last_silence_end >= audio_length - 10:  # допуск 10 мс
        silence_duration = last_silence_end - last_silence_start
        
        if silence_duration > tail_ms:
            # Обрезаем до начала тишины + tail_ms
            trim_point = last_silence_start + tail_ms
            return audio[:trim_point]
    
    return audio


async def generate_audio(text: str, output_path: Path, raw_dir: Path) -> bool:
    """
    Генерирует аудиофайл для заданного текста с помощью edge-tts.
    Сохраняет сырой файл в raw_dir, обрезанный - в output_path.
    """
    try:
        communicate = edge_tts.Communicate(text, VOICE)
        
        # Путь для сырого (необрезанного) файла
        raw_path = raw_dir / f"{text}.mp3"
        
        # Сохраняем сырой файл от edge-tts
        await communicate.save(str(raw_path))
        
        # Загружаем аудио и обрезаем тишину
        audio = AudioSegment.from_mp3(str(raw_path))
        trimmed_audio = trim_silence(audio)
        
        # Сохраняем обрезанный результат
        trimmed_audio.export(output_path, format="mp3")
        
        return True
    except Exception as e:
        print(f"Ошибка при обработке '{text}': {e}")
        return False


def trim_existing_file(file_path: Path) -> bool:
    """
    Обрезает тишину в существующем аудиофайле.
    """
    try:
        audio = AudioSegment.from_mp3(file_path)
        trimmed_audio = trim_silence(audio)
        trimmed_audio.export(file_path, format="mp3")
        return True
    except Exception as e:
        print(f"Ошибка при обрезке тишины в '{file_path}': {e}")
        return False


async def process_file(input_file: Path, output_dir: Path) -> None:
    """
    Обрабатывает файл со списком слов/цифр.
    """
    # Создаём выходную директорию, если её нет
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаём директорию для сырых (необрезанных) файлов
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Читаем слова из файла
    with open(input_file, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]
    
    print(f"Найдено {len(words)} слов/цифр для обработки")
    print(f"Сырые файлы сохраняются в: {raw_dir}")
    
    for i, word in enumerate(words, 1):
        output_path = output_dir / f"{word}.mp3"
        raw_path = raw_dir / f"{word}.mp3"
        print(f"[{i}/{len(words)}] Обработка: {word}")
        
        # Приоритет проверки: 1) сырой файл, 2) обрезанный файл, 3) генерация нового
        if raw_path.exists():
            # Есть сырой файл - обрезаем его и сохраняем в output
            print(f"  → Найден сырой файл, обрезаем тишину...")
            try:
                audio = AudioSegment.from_mp3(raw_path)
                trimmed_audio = trim_silence(audio)
                trimmed_audio.export(output_path, format="mp3")
                print(f"  ✓ Обрезано из сырого: {output_path}")
            except Exception as e:
                print(f"  ✗ Ошибка при обрезке сырого файла: {e}")
        elif output_path.exists():
            # Нет сырого, но есть обрезанный - обрезаем его повторно
            print(f"  → Файл уже существует, обрезаем тишину...")
            success = trim_existing_file(output_path)
            if success:
                print(f"  ✓ Тишина обрезана: {output_path}")
            else:
                print(f"  ✗ Ошибка при обрезке тишины: {word}")
        else:
            # Нет ни сырого, ни обрезанного - генерируем новый
            success = await generate_audio(word, output_path, raw_dir)
            
            if success:
                print(f"  ✓ Сохранено: {output_path}")
            else:
                print(f"  ✗ Ошибка при обработке: {word}")
    
    print(f"\nГотово! Файлы сохранены в {output_dir}")
    print(f"Сырые файлы: {raw_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Генерация аудиофайлов из списка слов с помощью edge-tts"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Путь к файлу со словами/цифрами (по одному на строку)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("./audio"),
        help="Директория для сохранения аудиофайлов (по умолчанию: ./audio)"
    )
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"Ошибка: файл '{args.input_file}' не найден")
        return 1
    
    asyncio.run(process_file(args.input_file, args.output))
    return 0


if __name__ == "__main__":
    exit(main())
