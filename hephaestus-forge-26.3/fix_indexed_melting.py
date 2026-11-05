#!/usr/bin/env python3
"""Experimental lab: use a bitset of active melting slots and decouple
full inventory recipe scans (every 5 ticks or on item/temp change) from actual
melting progress (which still advances on EVERY tick). Test extensively before
using in a release.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/"src/main/java/com/titammods/common/blockentities/SmelteryControllerBlockEntity.java"
s=p.read_text(encoding="utf-8")

def repl(a,b):
    global s
    assert s.count(a)==1,("source changed",s.count(a),a[:110])
    s=s.replace(a,b)

repl(
"    private int ioRefreshCounter = 0;",
"""    private int ioRefreshCounter = 0;
    private final java.util.BitSet activeMeltingSlots = new java.util.BitSet();
    private int meltingScanTicks = 0;
    private int meltingScanInventoryVersion = Integer.MIN_VALUE;
    private int meltingScanTemperature = Integer.MIN_VALUE;""")
repl(
"""        updateMeltingTimes();

        boolean hasValidRecipe = false;
        for (int i = 0; i < itemHandler.getSlots(); i++) {
            if (meltingState[i] == 0 && !itemHandler.getStackInSlot(i).isEmpty()) {
                hasValidRecipe = true;
                break;
            }
        }""",
"""        // Bulk smelteries may have thousands of EMPTY slots. Scan the entire
        // inventory only every five ticks unless actual items or temperature
        // have changed; still advance active melting every single tick.
        checkInventorySync();
        if (++meltingScanTicks >= 5
                || meltingScanInventoryVersion != inventoryVersion
                || meltingScanTemperature != temperature) {
            updateMeltingTimes();
            meltingScanTicks = 0;
            meltingScanInventoryVersion = inventoryVersion;
            meltingScanTemperature = temperature;
        }
        boolean hasValidRecipe = !activeMeltingSlots.isEmpty();""")
repl(
"""        for (int i = 0; i < itemHandler.getSlots(); i++) {
            ItemStack stack = itemHandler.getStackInSlot(i);
            if (stack.isEmpty()) {
                if (meltingTime[i] != 0 || meltingProgress[i] != 0 || meltingState[i] != 0) {""",
"""        activeMeltingSlots.clear();
        for (int i = 0; i < itemHandler.getSlots(); i++) {
            ItemStack stack = itemHandler.getStackInSlot(i);
            if (stack.isEmpty()) {
                if (meltingTime[i] != 0 || meltingProgress[i] != 0 || meltingState[i] != 0) {""")
# after scanning a non-empty item, update bitset only when state==0; placed after
# each iteration's main logic, immediately before closing loop and setChanged.
repl(
"""                }
            }
        }
        if (changed) setChanged();
    }
    @SuppressWarnings("removal")
    private void processMelting() {""",
"""                }
            }
            if (!stack.isEmpty() && meltingState[i] == 0)
                activeMeltingSlots.set(i);
        }
        if (changed) setChanged();
    }
    @SuppressWarnings("removal")
    private void processMelting() {""")
repl(
"""        for (int i = 0; i < itemHandler.getSlots(); i++) {
            ItemStack stack = itemHandler.getStackInSlot(i);
            if (stack.isEmpty() || meltingTime[i] <= 0 || meltingState[i] != 0) continue;""",
"""        for (int i = activeMeltingSlots.nextSetBit(0); i >= 0;
                i = activeMeltingSlots.nextSetBit(i + 1)) {
            if (i >= itemHandler.getSlots()) break;
            ItemStack stack = itemHandler.getStackInSlot(i);
            if (stack.isEmpty() || meltingTime[i] <= 0 || meltingState[i] != 0) continue;""")
repl(
"""                        meltingState[i] = 3;
                        changed = true;
                        continue;""",
"""                        meltingState[i] = 3;
                        activeMeltingSlots.clear(i);
                        changed = true;
                        continue;""")
# Invalidate cache after inventory resizing (both real structure changes and NBT load)
repl(
"""        meltingProgress = np;
        meltingTime     = nt;
        meltingState    = ns;""",
"""        meltingProgress = np;
        meltingTime     = nt;
        meltingState    = ns;
        activeMeltingSlots.clear();
        meltingScanInventoryVersion = Integer.MIN_VALUE;""")
repl(
"""        meltingState    = new int[pc];
        for (int i = 0; i < pc; i++) {""",
"""        meltingState    = new int[pc];
        activeMeltingSlots.clear();
        meltingScanInventoryVersion = Integer.MIN_VALUE;
        for (int i = 0; i < pc; i++) {""")
p.write_text(s,encoding="utf-8")
print("MELTING_PERF_LAB: active BitSet + periodic 5-tick bulk scan, 1-tick melting progress unchanged")
