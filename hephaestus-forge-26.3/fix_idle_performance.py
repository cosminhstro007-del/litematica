#!/usr/bin/env python3
"""Hephaestus Forge 26.3 Alpha5: reduce idle Smeltery tick and network overhead.

No game-rule or recipe changes; no data loss/lag from throttling the simulation.
Active melting remains on every tick. Structure still checked every 20 ticks.
Release versions Alpha4 and earlier remain untouched.
"""
from pathlib import Path
import re,sys
root=Path(sys.argv[1]).resolve()
p=root/"src/main/java/com/titammods/common/blockentities/SmelteryControllerBlockEntity.java"
s=p.read_text(encoding="utf-8")

def replace_one(a,b):
    global s
    n=s.count(a)
    assert n==1,("expected one source match",n,a[:180])
    s=s.replace(a,b)

# Stagger expensive 1-second structure scans across ticks when many identical
# Smelteries were placed/loaded together, avoiding simultaneous scan spikes.
a="    private int  tickCounter = 0;"
b="""    private int tickCounter = 0;
    private int ioRefreshCounter = 0;
    private static final int IO_REFRESH_CHECKS = 10; // 10 seconds, not each second
"""
replace_one(a,b)

# Look for constructor and set tickCounter on creation without changing global tick logic.
constructor='''        super(ModBlockEntities.SMELTERY_CONTROLLER.get(), pos, state);'''
assert s.count(constructor)==1,"constructor shifted"
s=s.replace(constructor,constructor+'''
        // Distribute once-per-second structure scans across different server ticks.
        this.tickCounter = Math.floorMod(pos.hashCode(), 20);''')

# IMPORTANT: Smeltery emits full block-entity NBT when sendBlockUpdated is called.
# Previously this happened even on idle, unformed controllers once per second.
old="""            if (isFormed) {
                updateFuelInfo();
                updateDisplayFluidSync();
                processAlloying();"""
new="""            boolean fuelInfoChanged = false;
            if (isFormed) {
                fuelInfoChanged = updateFuelInfo();
                updateDisplayFluidSync();
                processAlloying();"""
replace_one(old,new)

old="""            } else {
                this.currentFuel  = FluidStack.EMPTY;
                this.fuelCapacity = 0;
                setChanged();
            }
            level.sendBlockUpdated(pos, getBlockState(), getBlockState(), Block.UPDATE_ALL);"""
new="""            } else if (!this.currentFuel.isEmpty() || this.fuelCapacity != 0) {
                // Empty/unformed machines are not modified once a second.
                this.currentFuel  = FluidStack.EMPTY;
                this.fuelCapacity = 0;
                setChanged();
                fuelInfoChanged = true;
            }
            // Active machines still sync their evolving fuel to the GUI every
            // second. Idle machines transmit only on actual content changes.
            if (fuelInfoChanged || (isFormed && fuel > 0))
                level.sendBlockUpdated(pos, getBlockState(), getBlockState(), Block.UPDATE_ALL);"""
replace_one(old,new)

# Return fuel change to caller without modifying public protocol.
old="""    private void updateFuelInfo() {
        if (multiblock == null || multiblock.tanks.isEmpty()) {
            currentFuel = FluidStack.EMPTY;
            fuelCapacity = 0;
            return;
        }"""
new="""    private boolean updateFuelInfo() {
        if (multiblock == null || multiblock.tanks.isEmpty()) {
            boolean changed = !currentFuel.isEmpty() || fuelCapacity != 0;
            currentFuel = FluidStack.EMPTY;
            fuelCapacity = 0;
            if (changed) setChanged();
            return changed;
        }"""
replace_one(old,new)

old="""        if (fuelChanged) setChanged();
    }
    @SuppressWarnings("removal")
    private void consumeFuelFromTanks() {"""
new="""        if (fuelChanged) setChanged();
        return fuelChanged;
    }
    @SuppressWarnings("removal")
    private void consumeFuelFromTanks() {"""
replace_one(old,new)

# Linking every wall/floor block each second serializes/sends duplicate
# model-fluid state; resend only when topology changes, plus a 10s recovery
# sweep for IO blocks replaced in-place with the same bounding positions.
old="""        for (BlockPos pos : linkedPositions) {
            if (!currentPositions.contains(pos)) updateIOBlock(pos, false);
        }
        for (BlockPos pos : currentPositions) updateIOBlock(pos, true);
        linkedPositions.clear();
        linkedPositions.addAll(currentPositions);"""
new="""        for (BlockPos pos : linkedPositions) {
            if (!currentPositions.contains(pos)) updateIOBlock(pos, false);
        }
        boolean refresh = ++ioRefreshCounter >= IO_REFRESH_CHECKS;
        if (refresh) ioRefreshCounter = 0;
        for (BlockPos pos : currentPositions) {
            if (refresh || !linkedPositions.contains(pos)) updateIOBlock(pos, true);
        }
        linkedPositions.clear();
        linkedPositions.addAll(currentPositions);"""
replace_one(old,new)

# Do not attempt any alloy recipe when there is no molten liquid. This common
# case occurs in every newly formed but empty Smeltery.
old="""    private void processAlloying() {
        if (!(level instanceof ServerLevel sl)) return;"""
new="""    private void processAlloying() {
        if (fluidTank.getFluids().isEmpty()) return;
        if (!(level instanceof ServerLevel sl)) return;"""
replace_one(old,new)

p.write_text(s,encoding="utf-8")
v=root/"gradle.properties"
s=v.read_text(encoding="utf-8")
s,n=re.subn(r"(?m)^mod_version=.*$","mod_version=1.0.20-unofficial-26.3-alpha5",s)
assert n==1
v.write_text(s,encoding="utf-8")
print("HEPHAESTUS_ALPHA5_PERF: stagger scans, idle send/dirty guard, IO 10s refresh, idle alloy skip")
