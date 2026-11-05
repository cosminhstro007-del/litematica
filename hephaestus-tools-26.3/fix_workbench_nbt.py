#!/usr/bin/env python3
"""Tools Beta7: authoritative NBT reload should clear absent machine slots.
A live block entity can receive a partial/legacy NBT payload without e.g. Upgrade,
Output or Inputs. Never keep the previous in-memory ItemStacks in such cases.
"""
from pathlib import Path
import re,sys
root=Path(sys.argv[1]).resolve()
p=root/"src/main/java/com/titammods/hephaestus_tools/tables/blockentity/ArsenalTableBlockEntity.java"
s=p.read_text(encoding="utf-8")
for name,handler in (
    ("Upgrade","upgradeSlot"),
    ("Blueprint","blueprintSlot"),
    ("Inputs","inputSlots"),
    ("Output","outputSlot"),
):
    old=f'input.read("{name}", STACKS_CODEC).ifPresent(list -> restore({handler}, list));'
    new=f'restore({handler}, input.read("{name}", STACKS_CODEC).orElse(List.of()));'
    assert s.count(old)==1,("Missing NBT field",name)
    s=s.replace(old,new)
p.write_text(s,encoding="utf-8")

p=root/"gradle.properties"
s=p.read_text(encoding="utf-8")
s,n=re.subn(r"(?m)^mod_version=.*$","mod_version=1.0.11-unofficial-26.3-beta7",s)
assert n==1
p.write_text(s,encoding="utf-8")
print("BETA7_HARDEN: Workbench NBT reload clears absent Upgrade/Blueprint/Inputs/Output slots")
