#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name('phase03_apply.py')
text = path.read_text(encoding='utf-8')
needle = "    '''    if spec[\"mcpServers\"]:\n"
count = text.count(needle)
if count < 2:
    raise SystemExit(f'expected at least two render block anchors, found {count}')
text = text.replace(needle, "    r'''    if spec[\"mcpServers\"]:\n", 2)
path.write_text(text, encoding='utf-8')
Path(__file__).unlink()
