#!/usr/bin/env python3
"""Hephaestus Tools 26.3 click/keyboard and durability synchronization fixes.
Unofficial compatibility patch. Authors retained from upstream titammods MIT project.
"""
from pathlib import Path
import re, sys

root = Path(sys.argv[1])
p = root / "gradle.properties"
s = p.read_text(encoding="utf-8")
s = re.sub(r"(?m)^mod_version=.*$", "mod_version=1.0.11-unofficial-26.3-beta2", s)
p.write_text(s, encoding="utf-8")

base = root / "src/main/java/com/titammods/hephaestus_tools"
def change(rel, fn):
    p = base / rel
    before = p.read_text(encoding="utf-8")
    after = fn(before)
    if after == before: raise AssertionError("No change in "+rel)
    p.write_text(after,encoding="utf-8")

# Minecraft 26.3 SDL3: left=1, middle=2, right=3 (GLFW used left=0,right=1).
# Don't change vanilla inventory slot button IDs (0/1), ONLY raw mouse events.
def screen(s):
    assert "int button = event.button();" in s
    assert "if (button == 0 && !inspect && !hideUi)" in s
    assert "if ((button == 0 || button == 1)" in s
    s=s.replace("if (button == 0", "if (button == com.mojang.blaze3d.platform.InputConstants.MOUSE_BUTTON_LEFT")
    s=s.replace("if ((button == 0 || button == 1)",
        "if ((button == com.mojang.blaze3d.platform.InputConstants.MOUSE_BUTTON_LEFT || button == com.mojang.blaze3d.platform.InputConstants.MOUSE_BUTTON_RIGHT)")
    # The previous direct change doesn't touch conditions such as "button == 0)"? It does.
    # Apply the 26.3 SDL keyboard scancodes instead of old GLFW constants.
    keymap={
      "256":"KEY_ESCAPE","72":"KEY_H","70":"KEY_F","258":"KEY_TAB","32":"KEY_SPACE",
      "71":"KEY_G","265":"KEY_UP","264":"KEY_DOWN"
    }
    # Only replace the keyCode == / != checks, NEVER other ints.
    for old,new in keymap.items():
        s=re.sub(r"(keyCode\s*(?:==|!=)\s*)"+old+r"\b",
            r"\1com.mojang.blaze3d.platform.InputConstants."+new,s)
    return s
change("tables/screen/WorkbenchScreen.java",screen)

def other_screen(s):
    assert "event.button() == 0" in s
    return s.replace("event.button() == 0",
        "event.button() == com.mojang.blaze3d.platform.InputConstants.MOUSE_BUTTON_LEFT")
change("tables/screen/ArsenalTableScreen.java", other_screen)

# Ensure the mod's own construction damage and vanilla DAMAGE component agree.
# Older code used ItemStack#setDamageValue which writes the vanilla component only
# and then stale properties can overwrite that component during recalculation.
def setter(rel):
    def do(s):
        count=s.count(".setDamageValue(")
        assert count>0,rel
        return re.sub(r"(\b(?:tool|result|repaired|swapped|current)\b)\.setDamageValue\(",
                      r"com.titammods.hephaestus_tools.tools.nbt.ToolStack.setDamage(\1, ",s)
    change(rel,do)
for rel in [
  "tools/helper/ToolDurability.java",
  "effect/types/RepairEffect.java",
  "event/MasteryEvents.java",
  "tables/menu/ArsenalTableMenu.java",
  "tables/menu/WorkbenchMenu.java",
]: setter(rel)

# The base game writes DAMAGE directly in some contexts, so bring construction
# data in sync before checking the material fingerprint on every server tick.
def sync(s):
    old="""        super.inventoryTick(stack, level, entity, slot);
        ToolStack.refreshIfStale(stack);"""
    new="""        super.inventoryTick(stack, level, entity, slot);
        if (ToolStack.isInitialized(stack)) {
            int previous = ToolStack.getCurrentDamage(stack);
            int actual = stack.getOrDefault(DataComponents.DAMAGE, previous);
            if (previous != actual) ToolStack.setDamage(stack, actual);
        }
        ToolStack.refreshIfStale(stack);"""
    assert old in s
    return s.replace(old,new)
change("tools/item/ModifiableItem.java",sync)

# The reimplementation of legacy NeoForge SlotItemHandler is still incomplete.
# Keep consistent slot bounds and inventories server-side for click handling.
def slots(s):
    assert "public class ToolSlotContainer extends SimpleContainer" in s
    s=s.replace(
      "public int getSlotLimit(int slot) { return 99; }",
      "public int getSlotLimit(int slot) { return 99; }\n    @Override public int getMaxStackSize(ItemStack item) { return Math.max(super.getMaxStackSize(item), getSlotLimit(0)); }"
    )
    return s
# Intentionally skip changing slots until container API is tested on 26.3.

print("SDL3 mouse buttons + scancodes + durability data synchronization fixed.")
