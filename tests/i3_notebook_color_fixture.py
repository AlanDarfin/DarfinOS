"""Check actual widget pixels for gold selection and inherited blue accents."""
from pathlib import Path
import re
import sys

histogram, minimum_gold, maximum_blue = sys.argv[1:]
gold = blue = 0
for line in Path(histogram).read_text().splitlines():
    match = re.match(r"\s*(\d+):.*#([0-9A-Fa-f]{6})(?:[0-9A-Fa-f]{2})?\s", line)
    if not match:
        continue
    count = int(match[1])
    red, green, cyan = (int(match[2][i:i + 2], 16) for i in (0, 2, 4))
    if (red, green, cyan) == (255, 203, 46):
        gold += count
    if cyan > 100 and cyan > red * 1.2 and cyan > green * 1.1:
        blue += count
print(f"Rendered accents: gold={gold}, blue={blue}")
if gold < int(minimum_gold):
    raise SystemExit(f"Gold selection missing: {gold} pixels")
if blue > int(maximum_blue):
    raise SystemExit(f"Inherited blue accent visible: {blue} pixels")
