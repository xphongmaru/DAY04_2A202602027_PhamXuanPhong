import os
from pathlib import Path

ROOT = Path("E:/Downloads/AI_VINUI/DAY04_2A202602027_PhamXuanPhong/starter_v0")

for p in ROOT.rglob("*.py"):
    try:
        content = p.read_text(encoding="utf-8")
        if "\u2011" in content:
            print(f"Found in {p.relative_to(ROOT)}")
    except Exception as e:
        pass

for p in ROOT.rglob("*.md"):
    try:
        content = p.read_text(encoding="utf-8")
        if "\u2011" in content:
            print(f"Found in {p.relative_to(ROOT)}")
    except Exception as e:
        pass
