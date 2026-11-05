#!/usr/bin/env python3
"""Hephaestus Forge Alpha7: non-destructive Smeltery GUI transfer hotfix.

1. Stop building one hidden menu Slot + allocated SimpleContainer for every internal
   Smeltery slot (huge menu/network overhead; invisible target for shift-click).
2. Route shift-click directly to the real ItemStackHandler using its remainders.
   Accept only valid melting ingredients, leave non-meltable items untouched.
   Preserve partial stacks when capacity is insufficient.
3. Harden vanilla lava/water bucket conversion with explicit 1000mB simulate
   + execute, retaining input if output is unavailable or tank cannot accept.
4. For other fluid containers, only commit the resource transaction if the
   resulting container item actually exists; otherwise rollback.
5. Clamp scroll offsets so stale client packets cannot address invalid slots.
"""
from pathlib import Path
import sys,re
root=Path(sys.argv[1]).resolve()
p=root/"src/main/java/com/titammods/menu/SmelteryMenu.java"
s=p.read_text(encoding="utf-8")
def change(old,new):
    global s
    assert s.count(old)==1,(old[:150],s.count(old))
    s=s.replace(old,new)

change(
"""        for (int ri = 0; ri < total; ri++) {
            final int realIdx = ri;
            addSlot(new SlotItemHandler(blockEntity.itemHandler, ri, -9999, -9999) {
                @Override public boolean isActive() { return false; }
                @Override public boolean mayPickup(Player player) {
                    return true;
                }
            });
        }

""", """        // Offscreen items are accessed through scrollWrapper and shift-click
        // directly, NOT thousands of inactive, synthetic menu slots.
        // The old per-slot SimpleContainer allocation caused O(n^2) memory
        // overhead for large Smelteries, and hidden shift-click targets.
""")
change("""    public void updateScrollOffset(int rowOffset) {
        this.currentRowOffset = rowOffset;
    }""",
"""    public void updateScrollOffset(int rowOffset) {
        int maxOffset = Math.max(0, getTotalRows() - getVisibleRows());
        this.currentRowOffset = Math.max(0, Math.min(rowOffset, maxOffset));
    }""")
change(
"""            if (blockEntity == null) return -1;
            int total = blockEntity.itemHandler.getSlots();""",
"""            if (blockEntity == null || slot < 0 || slot >= MAX_COLS * MAX_VIS_ROWS) return -1;
            int total = blockEntity.itemHandler.getSlots();""")

# Override vanilla buckets via the native legacy tank API. Does not depend on
# item access events and NEVER consumes without producing the empty/filled bucket.
start=s.index("    private void processBucket() {")
end=s.index("\n    @Override",start)
s=s[:start]+"""    private void processBucket() {
        if (isProcessingBucket || blockEntity == null || blockEntity.getLevel() == null
                || blockEntity.getLevel().isClientSide()) return;
        ItemStack input = bucketHandler.getStackInSlot(0);
        if (input.isEmpty() || !bucketHandler.getStackInSlot(1).isEmpty()) return;

        isProcessingBucket = true;
        try {
            var tank = blockEntity.fluidTank;
            net.neoforged.neoforge.fluids.FluidStack offered = null;
            if (input.is(net.minecraft.world.item.Items.LAVA_BUCKET)) {
                offered = new net.neoforged.neoforge.fluids.FluidStack(
                        net.minecraft.world.level.material.Fluids.LAVA, 1000);
            } else if (input.is(net.minecraft.world.item.Items.WATER_BUCKET)) {
                offered = new net.neoforged.neoforge.fluids.FluidStack(
                        net.minecraft.world.level.material.Fluids.WATER, 1000);
            }

            if (offered != null) {
                if (tank.fill(offered, com.titammods.compat.port.legacy.IFluidHandler.FluidAction.SIMULATE)
                        != 1000) return;
                if (tank.fill(offered, com.titammods.compat.port.legacy.IFluidHandler.FluidAction.EXECUTE)
                        != 1000) return;
                bucketHandler.setStackInSlot(0, ItemStack.EMPTY);
                bucketHandler.setStackInSlot(1, new ItemStack(net.minecraft.world.item.Items.BUCKET));
                blockEntity.setChanged();
                return;
            }

            if (input.is(net.minecraft.world.item.Items.BUCKET)) {
                for (var fluid : tank.getFluids()) {
                    net.minecraft.world.item.Item filledBucket;
                    if (fluid.is(net.minecraft.world.level.material.Fluids.LAVA))
                        filledBucket = net.minecraft.world.item.Items.LAVA_BUCKET;
                    else if (fluid.is(net.minecraft.world.level.material.Fluids.WATER))
                        filledBucket = net.minecraft.world.item.Items.WATER_BUCKET;
                    else continue;

                    if (tank.drain(new net.neoforged.neoforge.fluids.FluidStack(
                            fluid.getFluid(), 1000),
                            com.titammods.compat.port.legacy.IFluidHandler.FluidAction.SIMULATE)
                            .getAmount() != 1000) continue;
                    var drained = tank.drain(new net.neoforged.neoforge.fluids.FluidStack(
                            fluid.getFluid(), 1000),
                            com.titammods.compat.port.legacy.IFluidHandler.FluidAction.EXECUTE);
                    if (drained.getAmount() != 1000) return;
                    bucketHandler.setStackInSlot(0, ItemStack.EMPTY);
                    bucketHandler.setStackInSlot(1, new ItemStack(filledBucket));
                    blockEntity.setChanged();
                    return;
                }
                return;
            }

            // Other mods may provide fluid containers. Only commit if the
            // transaction gives back a nonempty replacement container.
            var itemHandler = new com.titammods.common.blockentities.TransactionalItemHandler(
                    () -> bucketHandler, true, true);
            var itemAccess = net.neoforged.neoforge.transfer.access.ItemAccess
                    .forHandlerIndexStrict(itemHandler, 0);
            var fluidItem = itemAccess.getCapability(
                    net.neoforged.neoforge.capabilities.Capabilities.Fluid.ITEM);
            if (fluidItem == null) return;
            ItemStack changedBucket;
            try (var transaction = net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()) {
                int moved = net.neoforged.neoforge.transfer.ResourceHandlerUtil.move(
                        fluidItem, tank, fluid -> true, 1000, transaction);
                if (moved == 0)
                    moved = net.neoforged.neoforge.transfer.ResourceHandlerUtil.move(
                            tank, fluidItem, fluid -> true, 1000, transaction);
                if (moved <= 0) return;
                changedBucket = bucketHandler.getStackInSlot(0).copy();
                if (changedBucket.isEmpty() ||
                        net.minecraft.world.item.ItemStack.isSameItemSameComponents(
                                changedBucket, input)) return;
                transaction.commit();
            }
            bucketHandler.setStackInSlot(0, ItemStack.EMPTY);
            bucketHandler.setStackInSlot(1, changedBucket);
            blockEntity.setChanged();
        } finally {
            isProcessingBucket = false;
        }
    }

    private boolean bucketCanTransfer(ItemStack input) {
        if (blockEntity == null || blockEntity.getLevel() == null
                || blockEntity.getLevel().isClientSide()) return false;
        if (!bucketHandler.getStackInSlot(0).isEmpty()
                || !bucketHandler.getStackInSlot(1).isEmpty()) return false;

        var tank = blockEntity.fluidTank;
        if (input.is(net.minecraft.world.item.Items.LAVA_BUCKET))
            return tank.fill(new net.neoforged.neoforge.fluids.FluidStack(
                    net.minecraft.world.level.material.Fluids.LAVA, 1000),
                    com.titammods.compat.port.legacy.IFluidHandler.FluidAction.SIMULATE) == 1000;
        if (input.is(net.minecraft.world.item.Items.WATER_BUCKET))
            return tank.fill(new net.neoforged.neoforge.fluids.FluidStack(
                    net.minecraft.world.level.material.Fluids.WATER, 1000),
                    com.titammods.compat.port.legacy.IFluidHandler.FluidAction.SIMULATE) == 1000;
        if (input.is(net.minecraft.world.item.Items.BUCKET)) {
            for (var fluid : tank.getFluids()) {
                if ((fluid.is(net.minecraft.world.level.material.Fluids.LAVA)
                        || fluid.is(net.minecraft.world.level.material.Fluids.WATER))
                        && fluid.getAmount() >= 1000) return true;
            }
            return false;
        }
        return false;
    }
"""+s[end:]

# Keep all existing menu scrolling and interaction. The hidden slot range is
# removed; 32 virtual visible slots, 2 bucket slots, 36 player slots.
start=s.index("    @SuppressWarnings(\"removal\")\n    @Override\n    public ItemStack quickMoveStack(")
s=s[:start]+"""    /**
     * The scrollable virtual slots are not real vanilla Container slots.
     * Do not rely on moveItemStackTo() to interpret a large, nonstandard
     * inventory: copy into actual player slots and shrink the source only
     * by the amount those slots accepted. No overflow is ever discarded.
     */
    private boolean moveToPlayerInventorySafely(ItemStack source, int start, int end) {
        boolean changed = false;
        for (int i = end - 1; i >= start && !source.isEmpty(); i--) {
            Slot target = slots.get(i);
            if (!target.mayPlace(source)) continue;
            ItemStack current = target.getItem();
            if (current.isEmpty() ||
                    !ItemStack.isSameItemSameComponents(current, source)) continue;
            int max = Math.min(target.getMaxStackSize(source), current.getMaxStackSize());
            int amount = Math.min(Math.max(0, max - current.getCount()), source.getCount());
            if (amount > 0) {
                target.set(current.copyWithCount(current.getCount() + amount));
                source.shrink(amount);
                changed = true;
            }
        }
        for (int i = end - 1; i >= start && !source.isEmpty(); i--) {
            Slot target = slots.get(i);
            if (!target.mayPlace(source) || target.hasItem()) continue;
            int amount = Math.min(target.getMaxStackSize(source), source.getCount());
            if (amount <= 0) continue;
            target.set(source.copyWithCount(amount));
            source.shrink(amount);
            changed = true;
        }
        return changed;
    }

    @SuppressWarnings("removal")
    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        if (player.level().isClientSide() || !hasCurrentInventory(player)
                || index < 0 || index >= slots.size()) return ItemStack.EMPTY;
        final int visible = MAX_COLS * MAX_VIS_ROWS;
        final int bucketInput = visible;
        final int bucketOutput = visible + 1;
        final int playerStart = visible + 2;
        final int playerEnd = playerStart + 36;

        Slot slot = slots.get(index);
        if (slot == null || !slot.hasItem()) return ItemStack.EMPTY;
        ItemStack source = slot.getItem();
        ItemStack original = source.copy();
        if (original.isEmpty()) return ItemStack.EMPTY;

        if (index < visible || index == bucketInput || index == bucketOutput) {
            if (!moveToPlayerInventorySafely(source, playerStart, playerEnd))
                return ItemStack.EMPTY;
            slot.set(source.isEmpty() ? ItemStack.EMPTY : source);
            slot.setChanged();
            slot.onTake(player, source);
            return original;
        }

        if (index < playerStart || index >= playerEnd) return ItemStack.EMPTY;

        if (source.is(net.minecraft.world.item.Items.LAVA_BUCKET)
                || source.is(net.minecraft.world.item.Items.WATER_BUCKET)
                || source.is(net.minecraft.world.item.Items.BUCKET)) {
            if (!bucketCanTransfer(source)) return ItemStack.EMPTY;
            // For a stack of empty buckets, process exactly one at a time.
            ItemStack offered = source.copyWithCount(1);
            bucketHandler.setStackInSlot(0, offered);
            // On successful transfer, output must contain the replacement.
            if (!bucketHandler.getStackInSlot(0).isEmpty() ||
                    bucketHandler.getStackInSlot(1).isEmpty()) {
                // Never destroy an item if its fluid cannot be transferred.
                if (bucketHandler.getStackInSlot(0).is(
                        source.getItem())) bucketHandler.setStackInSlot(0, ItemStack.EMPTY);
                return ItemStack.EMPTY;
            }
            source.shrink(1);
            slot.set(source.isEmpty() ? ItemStack.EMPTY : source);
            slot.setChanged();
            slot.onTake(player, source);
            return original;
        }

        // Direct insertion with exact remainders into the authoritative block
        // entity. Do not shift items into hidden, inactive synthetic slots.
        // Non-meltable items stay in the player's inventory.
        if (com.titammods.common.recipe.HephaestusRecipeCache.melting(
                blockEntity.getLevel(), source) == null) return ItemStack.EMPTY;

        ItemStack remainder = source.copy();
        for (int i = 0; i < blockEntity.itemHandler.getSlots() && !remainder.isEmpty(); i++) {
            remainder = blockEntity.itemHandler.insertItem(i, remainder, false);
        }
        if (remainder.getCount() == original.getCount()) return ItemStack.EMPTY;
        slot.set(remainder.isEmpty() ? ItemStack.EMPTY : remainder);
        slot.setChanged();
        slot.onTake(player, remainder);
        return original;
    }
}
"""
p.write_text(s,encoding="utf-8")
p2=root/"gradle.properties"
q=p2.read_text(encoding="utf-8")
q,n=re.subn(r"(?m)^mod_version=.*$","mod_version=1.0.20-unofficial-26.3-alpha7",q)
assert n==1
p2.write_text(q,encoding="utf-8")
print("ALPHA7_MENU_HOTFIX: no hidden menu slots, safe remainder shift click, fail-safe vanilla buckets")
