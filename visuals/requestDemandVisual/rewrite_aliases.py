from pathlib import Path
import os
import re

src = Path("src").resolve()

files = list(src.rglob("*.ts")) + list(src.rglob("*.tsx"))

pattern = re.compile(r'(["\'])(@/[^"\']+)\1')

changed = 0

for file in files:
    text = file.read_text(encoding="utf-8")

    def replace(match):
        quote = match.group(1)
        alias = match.group(2)

        target = src / alias[2:]
        relative = os.path.relpath(target, file.parent).replace("\\", "/")

        if not relative.startswith("."):
            relative = "./" + relative

        return f"{quote}{relative}{quote}"

    new_text = pattern.sub(replace, text)

    if new_text != text:
        file.write_text(new_text, encoding="utf-8")
        changed += 1
        print(f"updated: {file.relative_to(src)}")

print(f"\nDone. Updated {changed} files.")
