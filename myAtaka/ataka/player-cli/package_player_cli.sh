#!/bin/bash

set -e
set -u

TMPFILE="$(mktemp -d)"
trap "rm -rf '$TMPFILE'" 0               # EXIT
trap "rm -rf '$TMPFILE'; exit 1" 2       # INT
trap "rm -rf '$TMPFILE'; exit 1" 1 15    # HUP TERM

cd "$TMPFILE"
cp -r /ataka/player-cli .
cp "/ataka/ctfconfig/$CTF.py" player-cli/player_cli/ctfconfig.py
mkdir -p player-cli/ataka/common
cp /ataka/common/flag_status.py player-cli/ataka/common/flag_status.py
pip install -r player-cli/requirements.txt --target player-cli/

#mkdir -p /data/shared
#rm -f /data/shared/ataka-player-cli.pyz

python -m zipapp -c --python "/usr/bin/env python3" --output /data/shared/ataka-player-cli.pyz player-cli/

# Presumendo che il tuo entrypoint sia in player-cli/__main__.py:
#python3 -m shiv --site-packages player-cli/ --compressed -p "/usr/bin/env python3" -o /data/shared/ataka-player-cli.pyz -e player_cli:app

echo 'Python player created'
