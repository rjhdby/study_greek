import random
import os
import subprocess
import sys
import select
import termios
import tty
import threading
import argparse
from tempfile import NamedTemporaryFile
from pydub import AudioSegment
from locales import t, set_language, get_available_languages

AUDIO_BASE_DIR = "./audio"
AVAILABLE_VOICES = ["female", "male"]
DEFAULT_MIN = 0
DEFAULT_MAX = 1999


def play_audio_async(seg, done_event):
    """Plays audio without console output in a separate thread."""
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
    Plays audio and reads keyboard input in parallel.
    Returns buffer of entered characters.
    """
    buffer = []
    done_event = threading.Event()
    
    # Start playback in a separate thread
    play_thread = threading.Thread(target=play_audio_async, args=(seg, done_event))
    play_thread.start()
    
    # Save terminal settings
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        # Switch terminal to raw mode for reading individual characters
        tty.setraw(fd)
        
        while not done_event.is_set():
            # Check if there is data to read (0.1 sec timeout)
            if select.select([sys.stdin], [], [], 0.1)[0]:
                char = sys.stdin.read(1)
                if char:
                    buffer.append(char)
    finally:
        # Restore terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    play_thread.join()
    return ''.join(buffer)


def get_audio_files_for_number(number, audio_dir):
    """
    Splits a number into components and returns a list of files to play.
    Example: 134 -> [100.mp3, 30.mp3, 4.mp3]
             1234 -> [1000.mp3, 200.mp3, 30.mp3, 4.mp3]
    """
    files = []
    
    exact_file = os.path.join(audio_dir, f"{number}.mp3")
    if os.path.exists(exact_file):
        return [exact_file]
    
    if number >= 1000:
        thousands = (number // 1000) * 1000
        files.append(os.path.join(audio_dir, f"{thousands}.mp3"))
        number = number % 1000
    
    if number >= 100:
        hundreds = (number // 100) * 100
        files.append(os.path.join(audio_dir, f"{hundreds}.mp3"))
        number = number % 100
    
    if number >= 20:
        tens = (number // 10) * 10
        files.append(os.path.join(audio_dir, f"{tens}.mp3"))
        number = number % 10
    
    if number > 0:
        files.append(os.path.join(audio_dir, f"{number}.mp3"))
    
    return files


def get_audio_for_number(number, audio_dir):
    """Returns AudioSegment for a number."""
    files = get_audio_files_for_number(number, audio_dir)
    
    combined = AudioSegment.empty()
    for audio_file in files:
        if os.path.exists(audio_file):
            segment = AudioSegment.from_mp3(audio_file)
            combined += segment
        else:
            print(t("file_not_found", file=audio_file))
    
    return combined


def input_with_prefill(prompt, prefill):
    """Input with prefilled value."""
    print(prompt + prefill, end='', flush=True)
    
    # Read additional input
    additional = input()
    return prefill + additional


def get_position_value(number, position):
    """
    Returns the value at a position in a number.
    Example: for 1965, position 1 (tens) -> 60
    """
    str_num = str(number)
    length = len(str_num)
    digit_index = length - 1 - position  # index from the end
    if digit_index < 0 or digit_index >= length:
        return None
    digit = int(str_num[digit_index])
    return digit * (10 ** position)


def get_number_components(number):
    """
    Splits a number into components (thousands, hundreds, tens, units).
    Example: 1234 -> [1000, 200, 30, 4]
             237 -> [200, 30, 7]
    """
    components = []
    
    if number >= 1000:
        thousands = (number // 1000) * 1000
        components.append(thousands)
        number = number % 1000
    
    if number >= 100:
        hundreds = (number // 100) * 100
        components.append(hundreds)
        number = number % 100
    
    if number >= 20:
        tens = (number // 10) * 10
        components.append(tens)
        number = number % 10
    elif number >= 11:
        # Numbers 11-19 as a single component
        components.append(number)
        number = 0
    
    if number > 0:
        components.append(number)
    
    return components


def generate_number_with_errors(errors, min_val=DEFAULT_MIN, max_val=DEFAULT_MAX):
    """
    Generates a number using components from error statistics.
    If no errors - generates a random number.
    """
    # Filter only positive counters
    positive_errors = {k: v for k, v in errors.items() if v > 0}
    
    if not positive_errors:
        return random.randint(max(min_val, 0), max_val)
    
    # Collect components by categories
    thousands = [k for k in positive_errors if k == 1000]
    hundreds = [k for k in positive_errors if 100 <= k <= 900 and k % 100 == 0]
    tens = [k for k in positive_errors if 20 <= k <= 90 and k % 10 == 0]
    teens = [k for k in positive_errors if 11 <= k <= 19]
    units = [k for k in positive_errors if 1 <= k <= 9]
    
    result = 0
    
    # Thousands (50% chance to use from errors if available)
    if thousands and random.random() < 0.5:
        result += random.choice(thousands)
    elif random.random() < 0.3:
        result += 1000
    
    # Hundreds (70% chance to use from errors if available)
    if hundreds and random.random() < 0.7:
        result += random.choice(hundreds)
    elif random.random() < 0.5:
        result += random.choice([100, 200, 300, 400, 500, 600, 700, 800, 900])
    
    # Tens or teens (70% chance to use from errors)
    if teens and random.random() < 0.7:
        result += random.choice(teens)
    elif tens and random.random() < 0.7:
        result += random.choice(tens)
        # Units
        if units and random.random() < 0.7:
            result += random.choice(units)
        elif random.random() < 0.5:
            result += random.randint(1, 9)
    else:
        # Random tens/units
        if random.random() < 0.5:
            result += random.randint(1, 99)
    
    # If result is 0 or out of range, generate a random number
    if result == 0 or result < min_val or result > max_val:
        return random.randint(max(min_val, 1), max_val)
    
    return result


def decrement_errors_for_number(number, errors):
    """
    Decrements error counters for number components.
    Called when guessed correctly on first try.
    """
    components = get_number_components(number)
    for comp in components:
        if comp in errors and errors[comp] > 0:
            errors[comp] -= 1


def print_statistics(total, first_try, errors):
    """Prints game statistics."""
    print("\n" + "=" * 40)
    print(t("statistics_header"))
    print("=" * 40)
    print(t("total_numbers", count=total))
    print(t("first_try_correct", count=first_try))
    
    if errors:
        # Sort errors by count (descending)
        sorted_errors = sorted(errors.items(), key=lambda x: x[1], reverse=True)[:5]
        print("\n" + t("top_errors_header"))
        for i, (pos_value, count) in enumerate(sorted_errors, 1):
            print(t("error_item", index=i, value=pos_value, count=count))
    print("=" * 40)


def main():
    parser = argparse.ArgumentParser(description="Number guessing game")
    parser.add_argument(
        "--lang",
        choices=get_available_languages(),
        default="ru",
        help="Interface language (default: ru)"
    )
    parser.add_argument(
        "--voice",
        choices=AVAILABLE_VOICES,
        default="female",
        help="Voice gender for audio: female (default) or male"
    )
    parser.add_argument(
        "--min",
        type=int,
        default=DEFAULT_MIN,
        help=f"Minimum number value (default: {DEFAULT_MIN})"
    )
    parser.add_argument(
        "--max",
        type=int,
        default=DEFAULT_MAX,
        help=f"Maximum number value (default: {DEFAULT_MAX})"
    )
    args = parser.parse_args()
    
    # Validate range
    if args.min < 0:
        args.min = 0
    if args.max > 1999:
        args.max = 1999
    if args.min >= args.max:
        print(f"Error: --min ({args.min}) must be less than --max ({args.max})")
        sys.exit(1)
    set_language(args.lang)
    
    # Directory with audio files for selected voice
    audio_dir = os.path.join(AUDIO_BASE_DIR, args.voice)
    
    print(t("game_title"))
    print(t("game_description"))
    print("-" * 40)
    
    # Statistics
    total_numbers = 0
    first_try_correct = 0
    errors = {}  # {position_value: count}
    
    while True:
        number = generate_number_with_errors(errors, args.min, args.max)
        audio_seg = get_audio_for_number(number, audio_dir)
        total_numbers += 1
        is_first_try = True
        
        # Play audio and read input in parallel
        prefill_buffer = read_input_during_playback(audio_seg)
        
        while True:
            print(t("controls_hint"))
            user_input = input_with_prefill(t("enter_number"), prefill_buffer).strip()
            prefill_buffer = ""  # Reset buffer after first input
            
            if user_input.lower() in ('q', 'quit', 'exit'):
                print_statistics(total_numbers - 1, first_try_correct, errors)
                print(t("goodbye"))
                return
            
            if user_input.lower() in ('r', 'repeat'):
                prefill_buffer = read_input_during_playback(audio_seg)
                continue
            
            if user_input.lower() in ('s', 'show'):
                print(t("answer_shown", number=number))
                print("-" * 40)
                break
            
            try:
                guess = int(user_input)
                if guess == number:
                    if is_first_try:
                        first_try_correct += 1
                        decrement_errors_for_number(number, errors)
                    print(t("correct"))
                    print("-" * 40)
                    break
                else:
                    is_first_try = False
                    # Highlight incorrect digits in red and collect errors
                    correct_str = str(number)
                    guess_str = str(guess)
                    highlighted = ""
                    
                    # Right-align for position comparison
                    max_len = max(len(correct_str), len(guess_str))
                    correct_padded = correct_str.zfill(max_len)
                    guess_padded = guess_str.zfill(max_len)
                    
                    for i, char in enumerate(guess_str):
                        # Position from end (0 - units, 1 - tens, etc.)
                        pos_from_end = len(guess_str) - 1 - i
                        guess_digit = int(char)
                        
                        # Check corresponding position in correct number
                        correct_pos_index = len(correct_padded) - 1 - pos_from_end
                        if correct_pos_index >= 0:
                            correct_digit = int(correct_padded[correct_pos_index])
                        else:
                            correct_digit = 0
                        
                        if guess_digit != correct_digit:
                            # Red color for incorrect digit
                            highlighted += f"\033[91m{char}\033[0m"
                            # Record error - value from target number that was misheard
                            error_value = correct_digit * (10 ** pos_from_end)
                            if error_value > 0:  # Don't record zeros
                                errors[error_value] = errors.get(error_value, 0) + 1
                        else:
                            highlighted += char
                    print(t("incorrect", highlighted=highlighted))
            except ValueError:
                print(t("enter_valid_number"))


if __name__ == "__main__":
    main()
