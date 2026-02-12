#!/usr/bin/env python3
"""
Скрипт для обрезки тишины в конце аудиофайла.
"""

import argparse
import subprocess
import json
from pathlib import Path


def get_audio_duration(file_path: str) -> float:
    """Получает длительность аудиофайла в миллисекундах."""
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
    Находит начало последнего участка тишины в конце файла.
    Возвращает время в миллисекундах или None, если тишина не найдена.
    """
    result = subprocess.run(
        [
            "ffmpeg", "-i", file_path, "-af",
            f"silencedetect=noise={threshold}dB:d=0.1",
            "-f", "null", "-"
        ],
        capture_output=True, text=True
    )
    
    # Парсим вывод ffmpeg для поиска silence_start
    lines = result.stderr.split('\n')
    silence_starts = []
    
    for line in lines:
        if "silence_start:" in line:
            try:
                start_str = line.split("silence_start:")[1].split()[0]
                silence_starts.append(float(start_str) * 1000)  # в миллисекунды
            except (IndexError, ValueError):
                continue
    
    if silence_starts:
        return silence_starts[-1]  # Последний участок тишины
    return None


def trim_audio(input_path: str, output_path: str, end_ms: float) -> None:
    """Обрезает аудио до указанной точки."""
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
        description="Обрезка тишины в конце аудиофайла"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Входной MP3 файл"
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Выходной MP3 файл"
    )
    parser.add_argument(
        "-t", "--threshold",
        type=int,
        default=-40,
        help="Порог тишины в децибелах (по умолчанию: -40)"
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=500,
        help="Максимальный хвост тишины в миллисекундах (по умолчанию: 500)"
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Ошибка: файл '{args.input}' не найден")
        return 1
    
    input_path = str(args.input)
    output_path = str(args.output)
    
    # Получаем длительность аудио
    duration = get_audio_duration(input_path)
    print(f"Длительность: {duration:.0f} мс")
    
    # Находим начало тишины в конце
    silence_start = detect_silence_end(input_path, args.threshold)
    
    if silence_start is None:
        print("Тишина в конце не обнаружена, копируем файл без изменений")
        subprocess.run(["cp", input_path, output_path])
        return 0
    
    print(f"Начало тишины: {silence_start:.0f} мс")
    
    silence_duration = duration - silence_start
    print(f"Длительность тишины: {silence_duration:.0f} мс")
    
    if silence_duration <= args.tail:
        print(f"Тишина ({silence_duration:.0f} мс) не превышает tail ({args.tail} мс), копируем без изменений")
        subprocess.run(["cp", input_path, output_path])
        return 0
    
    # Обрезаем до silence_start + tail
    trim_point = silence_start + args.tail
    print(f"Обрезаем до: {trim_point:.0f} мс")
    
    trim_audio(input_path, output_path, trim_point)
    
    new_duration = get_audio_duration(output_path)
    print(f"Новая длительность: {new_duration:.0f} мс")
    print(f"✓ Сохранено: {output_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
