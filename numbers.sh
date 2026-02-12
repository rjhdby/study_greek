#!/bin/sh

# All parameters are optional and named
# Usage: ./numbers.sh [--lang LANG] [--voice VOICE] [--min MIN] [--max MAX]
# Defaults: --lang en --voice female --min 0 --max 1999

python3 ./number_game.py "$@"