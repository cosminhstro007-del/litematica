#!/usr/bin/env python3
"""Update generated vanilla datapack recipes/advancements to Minecraft 26.3.
Minecraft 26.3 renamed advancement 'recipe_unlocked.conditions.recipe' to 'recipes'.
Also define optional shared item tags required by Forge casts on a minimal test server.
Recipe definitions and reward IDs remain unchanged; preserves forge crafting progression.
"""
from pathlib import Path
import json,sys

root=Path(sys.argv[1]).resolve()
candidates=[
    root/"src/generated/server/data",
    root/"src/main/resources/data",
]
changed=0
for data in candidates:
    if not data.exists(): continue
    for path in data.rglob("*.json"):
        if "advancement" not in path.parts: continue
        try: obj=json.loads(path.read_text(encoding="utf-8"))
        except (ValueError,UnicodeDecodeError):continue
        did=False
        for criterion in obj.get("criteria",{}).values():
            if not isinstance(criterion,dict):continue
            if criterion.get("trigger")=="minecraft:recipe_unlocked":
                c=criterion.get("conditions")
                if isinstance(c,dict) and "recipe" in c:
                    c["recipes"]=c.pop("recipe")
                    did=True
            if criterion.get("trigger")=="minecraft:recipe_crafted":
                c=criterion.get("conditions")
                if isinstance(c,dict) and "recipe_id" in c:
                    c["recipes"]=c.pop("recipe_id")
                    did=True
        if did:
            path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            changed+=1
# C-tag compatibility: these generic tags are normally populated by technology
# mods. Defining them empty allows the optional casting recipes to load without
# pretending Hephaestus Forge itself adds external gear/plate materials.
target=root/"src/generated/server/data/c/tags/item"
target.mkdir(parents=True,exist_ok=True)
for name in ["gears","plates"]:
    p=target/(name+".json")
    if not p.exists(): p.write_text('{"replace": false, "values": []}\n',encoding="utf-8")
print(f"26.3 data migration: patched {changed} recipe advancements; defined empty optional c:gears/c:plates tags.")
