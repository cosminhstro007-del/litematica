#!/usr/bin/env python3
"""Restore reliable change notification and per-slot limits for 26.3 ToolSlotContainer.

The initial port replaced the removed ItemStackHandler with SimpleContainer.
This additional patch fixes slot dirty notification, mass-count clamping and menu bounds.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
src=root/"src/main/java/com/titammods/hephaestus_tools"
slots=src/"tables/blockentity/ToolSlotContainer.java"
s=slots.read_text(encoding="utf-8")
assert "public class ToolSlotContainer extends SimpleContainer" in s
s=s.replace("public int getSlotLimit(int slot) { return 99; }", "public int getSlotLimit(int slot) { return 64; }")
s=s.replace("""    @Override public void setItem(int slot, ItemStack stack) {
        super.setItem(slot, stack);
        onContentsChanged(slot);
    }""", """    @Override public int getMaxStackSize(ItemStack stack) {
        // Forge workbench can legitimately hold a bulk stack in input slot 0.
        return ArsenalTableBlockEntity.BULK_LIMIT;
    }
    @Override public void setItem(int slot, ItemStack stack) {
        if (slot < 0 || slot >= getContainerSize()) return;
        super.setItem(slot, stack.isEmpty() ? ItemStack.EMPTY :
                stack.copyWithCount(Math.min(stack.getCount(), getSlotLimit(slot))));
    }
    @Override public void setChanged() {
        super.setChanged();
        onContentsChanged(-1);
    }""")
slots.write_text(s, encoding="utf-8")
j=src/"tables/blockentity/ArsenalTableBlockEntity.java"
s=j.read_text(encoding="utf-8")
old="@Override protected void onContentsChanged(int slot) { setChanged(); syncToClient(); }"
assert s.count(old)==4,(j,s.count(old))
s=s.replace(old,
  "@Override protected void onContentsChanged(int slot) { ArsenalTableBlockEntity.this.setChanged(); syncToClient(); }")
# The one-slot output slot must keep one tool, just like the input upgrade slot.
old="""    private final ToolSlotContainer outputSlot = new ToolSlotContainer(1) {
        @Override protected void onContentsChanged(int slot) { ArsenalTableBlockEntity.this.setChanged(); syncToClient(); }
    };"""
assert old in s
s=s.replace(old,"""    private final ToolSlotContainer outputSlot = new ToolSlotContainer(1) {
        @Override protected void onContentsChanged(int slot) { ArsenalTableBlockEntity.this.setChanged(); syncToClient(); }
        @Override public int getSlotLimit(int slot) { return 1; }
    };""")
j.write_text(s, encoding="utf-8")

# Slot must observe the handler's individual stack limits. Its vanilla implementation
# otherwise calculates the global container limit and can place too many items.
slot=src/"tables/menu/ToolBenchSlot.java"
slot.write_text("""package com.titammods.hephaestus_tools.tables.menu;

import com.titammods.hephaestus_tools.tables.blockentity.ToolSlotContainer;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

public class ToolBenchSlot extends Slot {
    private final ToolSlotContainer handler;
    public ToolBenchSlot(ToolSlotContainer handler, int index, int x, int y) {
        super(handler,index,x,y);
        this.handler=handler;
    }
    @Override public int getMaxStackSize() {
        return handler.getSlotLimit(index);
    }
    @Override public int getMaxStackSize(ItemStack stack) {
        return Math.min(handler.getSlotLimit(index), stack.getMaxStackSize());
    }
}
""",encoding="utf-8")
j=src/"tables/menu/ArsenalTableMenu.java"
s=j.read_text(encoding="utf-8")
assert s.count("new Slot(be.get")==3
s=s.replace("new Slot(be.getUpgradeSlot()", "new ToolBenchSlot(be.getUpgradeSlot()")
s=s.replace("new Slot(be.getInputSlots()", "new ToolBenchSlot(be.getInputSlots()")
s=s.replace("new Slot(be.getOutputSlot()", "new ToolBenchSlot(be.getOutputSlot()")
j.write_text(s,encoding="utf-8")
print("Hephaestus 26.3 inventory dirty/update propagation and slot limits patched.")
