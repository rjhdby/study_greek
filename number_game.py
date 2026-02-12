import random
import os
import subprocess
import sys
import select
import termios
import tty
import threading
from tempfile import NamedTemporaryFile
from pydub import AudioSegment

AUDIO_DIR = "./audio"


def play_audio_async(seg, done_event):
    """Воспроизводит аудио без вывода в консоль в отдельном потоке."""
    with NamedTemporaryFile("w+b", suffix=".wav", delete=False) as f:
        temp_path = f.name
        seg.export(f.name, "wav")
    try:
        subprocess.call(
            ["ffplay", "-nodisp", "-autoexit", "-hide_banner", "-loglevel", "quiet", temp_path]
        )
    finally:
        os.unlink(temp_path)
        done_event.set()


def read_input_during_playback(seg):
    """
    Воспроизводит аудио и параллельно читает ввод с клавиатуры.
    Возвращает буфер введённых символов.
    """
    buffer = []
    done_event = threading.Event()
    
    # Запускаем воспроизведение в отдельном потоке
    play_thread = threading.Thread(target=play_audio_async, args=(seg, done_event))
    play_thread.start()
    
    # Сохраняем настройки терминала
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        # Переключаем терминал в raw-режим для чтения отдельных символов
        tty.setraw(fd)
        
        while not done_event.is_set():
            # Проверяем, есть ли данные для чтения (таймаут 0.1 сек)
            if select.select([sys.stdin], [], [], 0.1)[0]:
                char = sys.stdin.read(1)
                if char:
                    buffer.append(char)
    finally:
        # Восстанавливаем настройки терминала
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    play_thread.join()
    return ''.join(buffer)


def get_audio_files_for_number(number):
    """
    Разбивает число на составляющие и возвращает список файлов для воспроизведения.
    Например: 134 -> [100.mp3, 30.mp3, 4.mp3]
             1234 -> [1000.mp3, 200.mp3, 30.mp3, 4.mp3]
    """
    files = []
    
    exact_file = os.path.join(AUDIO_DIR, f"{number}.mp3")
    if os.path.exists(exact_file):
        return [exact_file]
    
    if number >= 1000:
        thousands = (number // 1000) * 1000
        files.append(os.path.join(AUDIO_DIR, f"{thousands}.mp3"))
        number = number % 1000
    
    if number >= 100:
        hundreds = (number // 100) * 100
        files.append(os.path.join(AUDIO_DIR, f"{hundreds}.mp3"))
        number = number % 100
    
    if number >= 20:
        tens = (number // 10) * 10
        files.append(os.path.join(AUDIO_DIR, f"{tens}.mp3"))
        number = number % 10
    
    if number > 0:
        files.append(os.path.join(AUDIO_DIR, f"{number}.mp3"))
    
    return files


def get_audio_for_number(number):
    """Возвращает AudioSegment для числа."""
    files = get_audio_files_for_number(number)
    
    combined = AudioSegment.empty()
    for audio_file in files:
        if os.path.exists(audio_file):
            segment = AudioSegment.from_mp3(audio_file)
            combined += segment
        else:
            print(f"Файл не найден: {audio_file}")
    
    return combined


def input_with_prefill(prompt, prefill):
    """Ввод с предзаполненным значением."""
    print(prompt + prefill, end='', flush=True)
    
    # Читаем дополнительный ввод
    additional = input()
    return prefill + additional


def get_position_value(number, position):
    """
    Возвращает значение позиции в числе.
    Например: для 1965, позиция 1 (десятки) -> 60
    """
    str_num = str(number)
    length = len(str_num)
    digit_index = length - 1 - position  # индекс с конца
    if digit_index < 0 or digit_index >= length:
        return None
    digit = int(str_num[digit_index])
    return digit * (10 ** position)


def print_statistics(total, first_try, errors):
    """Выводит статистику игры."""
    print("\n" + "=" * 40)
    print("СТАТИСТИКА")
    print("=" * 40)
    print(f"Всего загадано: {total}")
    print(f"Угадано с первой попытки: {first_try}")
    
    if errors:
        # Сортируем ошибки по количеству (убывание)
        sorted_errors = sorted(errors.items(), key=lambda x: x[1], reverse=True)[:5]
        print("\nТоп 5 ошибок (по позициям):")
        for i, (pos_value, count) in enumerate(sorted_errors, 1):
            print(f"  {i}. {pos_value}: {count} раз(а)")
    print("=" * 40)


def main():
    print("Игра: Угадай число!")
    print("Вы услышите число от 1 до 1999. Введите его.")
    print("-" * 40)
    
    # Статистика
    total_numbers = 0
    first_try_correct = 0
    errors = {}  # {позиция_значение: количество}
    
    while True:
        number = random.randint(1, 1999)
        audio_seg = get_audio_for_number(number)
        total_numbers += 1
        is_first_try = True
        
        # Воспроизводим и параллельно читаем ввод
        prefill_buffer = read_input_during_playback(audio_seg)
        
        while True:
            print("r - repeat, s - skip, q - quit")
            user_input = input_with_prefill("Введите число: ", prefill_buffer).strip()
            prefill_buffer = ""  # Сбрасываем буфер после первого ввода
            
            if user_input.lower() in ('q', 'quit', 'exit'):
                print_statistics(total_numbers, first_try_correct, errors)
                print("До свидания!")
                return
            
            if user_input.lower() in ('r', 'repeat'):
                prefill_buffer = read_input_during_playback(audio_seg)
                continue
            
            if user_input.lower() in ('s', 'show'):
                print(f"Ответ: {number}. Следующее число...")
                print("-" * 40)
                break
            
            try:
                guess = int(user_input)
                if guess == number:
                    if is_first_try:
                        first_try_correct += 1
                    print("Правильно! Следующее число...")
                    print("-" * 40)
                    break
                else:
                    is_first_try = False
                    # Выделяем красным неправильные цифры и собираем ошибки
                    correct_str = str(number)
                    guess_str = str(guess)
                    highlighted = ""
                    
                    # Выравниваем по правому краю для сравнения позиций
                    max_len = max(len(correct_str), len(guess_str))
                    correct_padded = correct_str.zfill(max_len)
                    guess_padded = guess_str.zfill(max_len)
                    
                    for i, char in enumerate(guess_str):
                        # Позиция с конца (0 - единицы, 1 - десятки, и т.д.)
                        pos_from_end = len(guess_str) - 1 - i
                        guess_digit = int(char)
                        
                        # Проверяем соответствующую позицию в правильном числе
                        correct_pos_index = len(correct_padded) - 1 - pos_from_end
                        if correct_pos_index >= 0:
                            correct_digit = int(correct_padded[correct_pos_index])
                        else:
                            correct_digit = 0
                        
                        if guess_digit != correct_digit:
                            # Красный цвет для неправильной цифры
                            highlighted += f"\033[91m{char}\033[0m"
                            # Записываем ошибку по позиции
                            error_value = guess_digit * (10 ** pos_from_end)
                            errors[error_value] = errors.get(error_value, 0) + 1
                        else:
                            highlighted += char
                    print(f"Неправильно: {highlighted}. Попробуйте ещё раз.")
            except ValueError:
                print("Пожалуйста, введите число.")


if __name__ == "__main__":
    main()
