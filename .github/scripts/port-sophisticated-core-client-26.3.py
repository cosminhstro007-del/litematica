from pathlib import Path
import re

ROOT = Path("core-src/src/main/java")

# Baseline mechanical 26.3 renames for restored client sources.
for p in ROOT.rglob("*.java"):
    text = p.read_text(errors="ignore")
    new = text

    new = re.sub(r"\.isClientSide\b(?!\s*\()", ".isClientSide()", new)

    # 26.x components/NBT return optionals in the same way as the common pass.
    new = re.sub(r'(\.getInt\([^()\n]*\))(?!\s*\.)', r'\1.orElse(0)', new)
    new = re.sub(r'(\.getLong\([^()\n]*\))(?!\s*\.)', r'\1.orElse(0L)', new)
    new = re.sub(r'(\.getBoolean\([^()\n]*\))(?!\s*\.)', r'\1.orElse(false)', new)
    new = re.sub(r'(\.getString\([^()\n]*\))(?!\s*\.)', r'\1.orElse("")', new)

    # Common 26.3 item/crafting method simplifications.
    new = new.replace(".getHoverName().getString().orElse(\"\")", ".getHoverName().getString()")
    new = re.sub(r'\.assemble\(([^,\n]+),\s*[^)]+registryAccess\(\)\)', r'.assemble(\1)', new)

    if new != text:
        p.write_text(new)

# Remove runtime-inapplicable Fabric datagen entrypoint from metadata for the test/full runtime jar.
fmj = Path("core-src/src/main/resources/fabric.mod.json")
if fmj.exists():
    text = fmj.read_text()
    # Keep metadata syntactically valid while excluding the deleted datagen class.
    text = re.sub(
        r',?\s*"fabric-datagen"\s*:\s*\[[^\]]*\]',
        '',
        text,
        flags=re.S
    )
    fmj.write_text(text)

print("Applied baseline Sophisticated Core client 26.3 patch pass.")
