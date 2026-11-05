#!/usr/bin/env python3
"""Forge 26.3 Alpha4: no item drops while loading block-entity NBT.

The vanilla/NeoForge loadAdditional may run on existing block-entities when
receiving data or reconstituting a snapshot. Gameplay shrinking the Smeltery
should still drop overflow items, but deserialization must only replace stored
state, never spawn drops from the *previous* in-memory inventory.
Also clamp malformed NBT counts to the max feasible Smeltery volume (15x15x63).
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/"src/main/java/com/titammods/common/blockentities/SmelteryControllerBlockEntity.java"
s=p.read_text(encoding="utf-8")
anchor="""    @SuppressWarnings("removal")
    private void resizeInventory(int newSize) {
        ItemStackHandler newHandler = new ItemStackHandler(newSize) {"""
replacement="""    private static final int MAX_PERSISTED_SMELTERY_SLOTS = 15 * 15 * 63;

    private void resizeInventory(int newSize) {
        resizeInventory(newSize, true);
    }

    @SuppressWarnings("removal")
    private void resizeInventory(int newSize, boolean dropOverflow) {
        newSize = Math.max(0, Math.min(MAX_PERSISTED_SMELTERY_SLOTS, newSize));
        ItemStackHandler newHandler = new ItemStackHandler(newSize) {"""
assert s.count(anchor)==1, "Unexpected resizeInventory method body"
s=s.replace(anchor,replacement)
old="""                } else if (level != null) {
                    Containers.dropItemStack(level, worldPosition.getX(), worldPosition.getY() + 1, worldPosition.getZ(), stack);
                }"""
new="""                } else if (dropOverflow && level != null && !level.isClientSide()) {
                    // Only real structure resizing may eject overflow, never NBT reload.
                    Containers.dropItemStack(level, worldPosition.getX(), worldPosition.getY() + 1, worldPosition.getZ(), stack);
                }"""
assert s.count(old)==1
s=s.replace(old,new)
old="""        int slotCount = input.getIntOr("slot_count", 0);
        resizeInventory(slotCount);
        for (int i = 0; i < slotCount; i++) {"""
new="""        int slotCount = Math.max(0, Math.min(MAX_PERSISTED_SMELTERY_SLOTS,
                input.getIntOr("slot_count", 0)));
        // NBT reload replaces authoritative slots. Prior memory must NOT be
        // dropped into the world or copied into the newly loaded inventory.
        resizeInventory(slotCount, false);
        for (int i = 0; i < slotCount; i++) {"""
assert s.count(old)==1
s=s.replace(old,new)
old="""        int pc = input.getIntOr("progress_count", 0);
        meltingProgress = new int[pc];"""
new="""        int pc = Math.max(0, Math.min(slotCount, input.getIntOr("progress_count", 0)));
        meltingProgress = new int[pc];"""
assert s.count(old)==1
s=s.replace(old,new)
p.write_text(s,encoding="utf-8")
print("ALPHA4_HARDEN: NBT reload does not eject old inventory, gameplay shrink still drops safely, counts bounded")
