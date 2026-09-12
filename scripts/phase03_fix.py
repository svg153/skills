#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name('phase03_apply.py')
text = path.read_text(encoding='utf-8')
old = '''    ''' + '''    if spec["mcpServers"]:
        config["mcpServers"] = spec["mcpServers"]
    return (json.dumps(config, indent=2, ensure_ascii=False) + "\\n").encode("utf-8")
''' + '''',
    ''' + '''    if spec["mcpServers"]:
        config["mcpServers"] = spec["mcpServers"]
    if spec["externalSkillComponents"]:
        config["externalSkillComponents"] = spec["externalSkillComponents"]
    return (json.dumps(config, indent=2, ensure_ascii=False) + "\\n").encode("utf-8")
''' + '''','''
new = '''    r''' + "'''" + '''    if spec["mcpServers"]:
        config["mcpServers"] = spec["mcpServers"]
    return (json.dumps(config, indent=2, ensure_ascii=False) + "\\n").encode("utf-8")
''' + "'''" + ''',
    r''' + "'''" + '''    if spec["mcpServers"]:
        config["mcpServers"] = spec["mcpServers"]
    if spec["externalSkillComponents"]:
        config["externalSkillComponents"] = spec["externalSkillComponents"]
    return (json.dumps(config, indent=2, ensure_ascii=False) + "\\n").encode("utf-8")
''' + "'''" + ''','''
if old not in text:
    raise SystemExit('phase03 render anchor patch not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
Path(__file__).unlink()
