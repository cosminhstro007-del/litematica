from pathlib import Path

CORE = Path("core-src/src/main/java")
DONOR = Path("upstream-26.2-src/src/main/java")

replaced = []
skipped_platform = []

for target in CORE.rglob("*.java"):
    rel = target.relative_to(CORE)
    donor = DONOR / rel
    if not donor.exists():
        continue

    current = target.read_text(errors="ignore")
    # Only touch restored/client-facing files. Never replace the already-ported backend/common core.
    is_client_facing = (
        "/client/" in ("/" + str(rel).replace("\\", "/"))
        or "import net.minecraft.client." in current
        or "import com.mojang.blaze3d." in current
    )
    if not is_client_facing:
        continue

    source = donor.read_text(errors="ignore")
    # Platform-neutral donor classes are safe semantic guides. NeoForge-specific classes stay on
    # the Fabric source and are adapted separately.
    if "net.neoforged." in source or "NeoForge" in source or "IClient" in source and "neoforged" in source:
        skipped_platform.append(str(rel))
        continue

    target.write_text(source)
    replaced.append(str(rel))

print(f"Overlayed {len(replaced)} platform-neutral official 26.2 client files")
for rel in replaced:
    print("OVERLAY", rel)
print(f"Skipped {len(skipped_platform)} NeoForge-specific donor files")
for rel in skipped_platform:
    print("SKIP_NEO", rel)
