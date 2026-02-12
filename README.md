# Greek Numbers Audio Trainer

A project for learning Greek numbers by ear. Includes a game for training number perception and tools for generating audio files.

## Deployment

### Requirements

- Python 3.10+
- ffmpeg (for audio playback and processing)

### Installing ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

### Installing Python Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Scripts

### 1. number_game.py — "Guess the Number" Game

An interactive game for training Greek number perception by ear. The program plays a random number from the specified range, and the user must guess it.

**Run:**
```bash
python3 number_game.py
```

or via shell script:
```bash
./numbers.sh
```

**Options:**
- `--lang` — interface language: `en` (default), `ru`
- `--voice` — voice gender for audio: `female` (default), `male`
- `--min` — minimum number value (default: 0, range: 0-1999)
- `--max` — maximum number value (default: 1999, range: 0-1999)

**Examples:**
```bash
# English interface, female voice (default), full range 0-1999
python3 number_game.py

# Russian interface, male voice
python3 number_game.py --lang ru --voice male

# Practice only numbers 1-100
python3 number_game.py --min 1 --max 100

# Practice numbers 500-1000
python3 number_game.py --min 500 --max 1000

# Via shell script (all parameters are named)
./numbers.sh --lang en --voice female
./numbers.sh --lang ru --voice male
./numbers.sh --min 1 --max 100
./numbers.sh --lang ru --voice male --min 500 --max 1000
```

**Controls:**
- Type the number while audio is playing — input will be pre-filled in the prompt
- `r` or `repeat` — replay the audio
- `s` or `show` — show the answer and move to the next number
- `q` or `quit` — exit the game

**Features:**
- Parallel input during audio playback
- Incorrect digits highlighted in red
- End-of-game statistics: total numbers, first-try correct guesses, top 5 position errors
- Localized interface (Russian, English)

---

### 2. make_dataset.py — Audio File Generation

Generates audio files for words/numbers from a new line delimited text file using edge-tts. Supports male and female Greek voices. Automatically trims trailing silence.

**Voices:**
- `male` — el-GR-NestorasNeural (default)
- `female` — el-GR-AthinaNeural

**Run:**
```bash
python3 make_dataset.py dataset.txt
```

**Parameters:**
- `input_file` — path to file with words/numbers (one per line)
- `-o, --output` — output directory (default: `./audio`)
- `-g, --gender` — voice gender: `male` (default), `female`, or `all` (both)

**Examples:**
```bash
# Generate with male voice (default)
python3 make_dataset.py dataset.txt

# Generate with female voice
python3 make_dataset.py dataset.txt -g female

# Generate both male and female voices
python3 make_dataset.py dataset.txt -g all
```

**Result:**
- Trimmed files are saved to `./audio/{gender}/` (e.g., `./audio/male/`, `./audio/female/`)
- Raw (untrimmed) files are saved to `./audio/raw/{gender}/`

---

### 3. trim_silence.py — Audio Silence Trimming

A utility for trimming trailing silence in audio files using ffmpeg.

**Run:**
```bash
python3 trim_silence.py input.mp3 output.mp3
```

**Parameters:**
- `input` — input MP3 file
- `output` — output MP3 file
- `-t, --threshold` — silence threshold in decibels (default: -40)
- `--tail` — maximum silence tail in milliseconds (default: 500)

**Example:**
```bash
python3 trim_silence.py audio/raw/100.mp3 audio/100.mp3 --tail 20
```
