# Installation Guide for macOS

This is a step-by-step guide for those who are not familiar with software development. Follow the instructions in order.

---

## Step 1: Open Terminal

1. Press `Cmd + Space` (this opens Spotlight)
2. Type `Terminal`
3. Press Enter

A window with a command line will open — this is where you will enter all commands.

---

## Step 2: Install Homebrew

**Homebrew** is a package manager for macOS that makes it easy to install software.

Copy and paste this command into Terminal, then press Enter:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

- You will be asked to enter your Mac password (characters won't be displayed as you type — this is normal)
- Press Enter when asked to confirm the installation
- Wait for it to complete (may take a few minutes)

**Important!** After installing Homebrew, it may show instructions labeled "Next steps". If there are commands to run — run them. Usually it looks like this:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Verify that Homebrew is installed:
```bash
brew --version
```

You should see a version number, for example: `Homebrew 4.x.x`

---

## Step 3: Install Git

**Git** is a version control system, needed to download the project.

```bash
brew install git
```

> **Note:** During Git installation, you may be prompted to install **Xcode Command Line Tools**. This is a set of developer tools from Apple required for many programs. If a dialog window appears asking to install them — click "Install" and wait for the installation to complete. This is a one-time setup.

Verify the installation:
```bash
git --version
```

---

## Step 4: Install Python

macOS may have a pre-installed Python, but it's better to install a fresh version:

```bash
brew install python@3.12
```

Verify the installation:
```bash
python3 --version
```

It should show version 3.10 or higher.

---

## Step 5: Install ffmpeg

**ffmpeg** is a program for working with audio and video files.

```bash
brew install ffmpeg
```

Verify the installation:
```bash
ffmpeg -version
```

---

## Step 6: Download the Project

Choose a folder where you want to download the project. For example, the Documents folder:

```bash
cd ~/Documents
```

Download the project (replace the URL with the actual one if needed):

```bash
git clone https://github.com/rjhdby/study_greek.git
```

---

## Step 7: Create a Virtual Environment

A virtual environment isolates project dependencies from the system.

Navigate to the project folder (if not already there):
```bash
cd study_greek
```

Create a virtual environment:
```bash
python3 -m venv .venv
```

Activate it:
```bash
source .venv/bin/activate
```

After activation, `(.venv)` will appear at the beginning of the terminal line — this means the environment is active.

---

## Step 8: Install Project Dependencies

```bash
pip install -r requirements.txt
```

This will install all required Python packages:
- **edge-tts** — text-to-speech library for generating audio
- **pydub** — audio processing library (requires ffmpeg installed via brew)
- **audioop-lts** — audio processing library (required for Python 3.13+)

> **Note:** The `pydub` library requires `ffmpeg` to work with audio files. That's why we installed it in Step 5 using `brew install ffmpeg`.

Wait for all packages to finish installing.

---

## Step 9: Run the Game!

```bash
python3 number_game.py
```

Or with Russian interface:
```bash
python3 number_game.py --lang ru
```

---

## Useful Commands

| Action | Command |
|--------|---------|
| Activate environment | `source .venv/bin/activate` |
| Deactivate environment | `deactivate` |
| Run the game | `python3 number_game.py` |
| Run with Russian interface | `python3 number_game.py --lang ru` |
| Exit the game | Type `q` or `quit` |

---

## Troubleshooting

### "command not found: brew"
After installing Homebrew, run the commands from the "Next steps" section that the installer showed, or restart Terminal.

### "command not found: python3"
Try:
```bash
brew link python@3.12
```

### Error when installing dependencies
Make sure the virtual environment is activated (`(.venv)` should appear at the beginning of the line).

### No sound in the game
Make sure ffmpeg is installed (`ffmpeg -version`) and the sound on your Mac is not muted.

---

## Running Again (after reboot)

Every time you want to run the project after restarting your computer:

1. Open Terminal
2. Navigate to the project folder:
   ```bash
   cd ~/Documents/greek
   ```
3. Activate the environment:
   ```bash
   source .venv/bin/activate
   ```
4. Run the game:
   ```bash
   python3 number_game.py
   ```
