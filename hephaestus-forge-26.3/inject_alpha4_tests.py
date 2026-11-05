#!/usr/bin/env python3
"""Developer-only Alpha4 regressions: transactional rollback and block entity NBT round-trip.
Injected AFTER compile & previous smoke hooks. Never shipped in release jar.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/"src/main/java/com/titammods/compat/port/validation/ForgeSmokeTest.java"
s=p.read_text(encoding="utf-8")
anchor='        System.out.println("HEPHAESTUS_VERIFY_SUCCESS recipes, table, basin, melter");'
assert s.count(anchor)==1
s=s.replace(anchor,"""        checkFluidTransactions();
        checkBlockEntitySerialization(level,y);
        checkNoDropsOnNbtReload(level,y);
"""+anchor)
marker="    public static void check(MinecraftServer server) {"
assert s.count(marker)==1
s=s.replace(marker,"""    private static void checkNoDropsOnNbtReload(ServerLevel level,int y) {
        BlockPos pos=new BlockPos(46,y,20);
        level.setBlockAndUpdate(pos,ModBlocks.SMELTERY_CONTROLLER.get().defaultBlockState());
        var old=(SmelteryControllerBlockEntity)level.getBlockEntity(pos);
        require(old!=null,"Reload fixture failed");
        // Existing in-memory data should NEVER become dropped item entities
        // merely because the authoritative NBT payload replaces it.
        old.itemHandler=new com.titammods.compat.port.legacy.ItemStackHandler(4);
        old.itemHandler.setStackInSlot(3,new ItemStack(Items.DIAMOND,3));

        var source=new SmelteryControllerBlockEntity(pos,old.getBlockState());
        source.itemHandler=new com.titammods.compat.port.legacy.ItemStackHandler(1);
        source.itemHandler.setStackInSlot(0,new ItemStack(Items.REDSTONE,1));
        var saved=source.saveWithoutMetadata(level.registryAccess());
        var box=new net.minecraft.world.phys.AABB(pos).inflate(3);
        int before=level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class,box).size();
        old.loadWithComponents(net.minecraft.world.level.storage.TagValueInput.create(
                new net.minecraft.util.ProblemReporter.Collector(),level.registryAccess(),saved));
        int after=level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class,box).size();
        require(after==before,"Reload unexpectedly dropped old item stacks");
        require(old.itemHandler.getSlots()==1 && old.itemHandler.getStackInSlot(0).is(Items.REDSTONE),
                "Reload did not replace inventory with authoritative slot data");
        System.out.println("HEPHAESTUS_ALPHA4 no item ejection on NBT reload OK");
    }

    private static void checkFluidTransactions() {
        int[] changes={0};
        var h=new com.titammods.common.blockentities.multiblock.SmelteryFluidHandler(
                ()->changes[0]++);
        h.setCapacity(5000);
        h.fill(new FluidStack(Fluids.LAVA, 1300), IFluidHandler.FluidAction.EXECUTE);
        int baseline=changes[0];
        var lava=net.neoforged.neoforge.transfer.fluid.FluidResource.of(
                new FluidStack(Fluids.LAVA, 1));
        try (var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()) {
            require(h.extract(0,lava,600,tx)==600,"Transaction extract amount wrong");
            require(h.getTotalFluid()==700,"Extraction did not update transactional state");
            // No commit; closing root transaction must restore 1300.
        }
        require(h.getTotalFluid()==1300,"Rollback lost fluid");
        require(changes[0]==baseline,"Rolled back transfer dirtied owner");
        try (var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()) {
            require(h.insert(lava,500,tx)==500,"Transaction insert amount wrong");
            require(h.getTotalFluid()==1800,"Insertion temporary amount wrong");
        }
        require(h.getTotalFluid()==1300,"Insert rollback duplicated fluid");
        try (var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()) {
            require(h.extract(0,lava,300,tx)==300,"Committed extract amount wrong");
            tx.commit();
        }
        require(h.getTotalFluid()==1000,"Committed extraction not persisted");
        require(changes[0]==baseline+1,"Committed transaction did not notify owner once");
        System.out.println("HEPHAESTUS_ALPHA4 transactional rollback, commit and conservation OK");
    }

    private static void checkBlockEntitySerialization(ServerLevel level,int y) {
        BlockPos pos=new BlockPos(35,y,20);
        level.setBlockAndUpdate(pos,ModBlocks.SMELTERY_CONTROLLER.get().defaultBlockState());
        require(level.getBlockEntity(pos) instanceof SmelteryControllerBlockEntity,
                "Controller fixture missing");
        var be=(SmelteryControllerBlockEntity)level.getBlockEntity(pos);
        // Use the public internal inventory for a pre-loaded controller: NBT includes
        // inventory slot data, progress, fuel and all molten fluids.
        be.itemHandler=new com.titammods.compat.port.legacy.ItemStackHandler(3);
        be.itemHandler.setStackInSlot(0,new ItemStack(Items.IRON_ORE));
        be.meltingProgress=new int[] {12,0,0};
        be.meltingTime=new int[] {90,0,0};
        be.meltingState=new int[] {0,0,0};
        be.fuel=131;
        be.maxFuel=500;
        be.temperature=1000;
        be.currentFuel=new FluidStack(Fluids.LAVA,700);
        be.fluidTank.setCapacity(16000);
        Fluid molten=BuiltInRegistries.FLUID.getValue(
                Identifier.fromNamespaceAndPath("hephaestus","molten_iron"));
        require(be.fluidTank.fill(new FluidStack(molten,1200),
                IFluidHandler.FluidAction.EXECUTE)==1200,"Fixture fill failed");
        var saved=be.saveWithoutMetadata(level.registryAccess());
        var restored=new SmelteryControllerBlockEntity(pos,be.getBlockState());
        restored.loadWithComponents(net.minecraft.world.level.storage.TagValueInput.create(
                new net.minecraft.util.ProblemReporter.Collector(),level.registryAccess(),saved));
        require(restored.itemHandler.getSlots()==3,"Controller slot count not restored");
        require(restored.itemHandler.getStackInSlot(0).is(Items.IRON_ORE),
                "Controller inventory did not survive serialization");
        require(restored.meltingProgress.length==3 && restored.meltingProgress[0]==12,
                "Controller melting progress not restored");
        require(restored.meltingTime[0]==90,"Controller melting time not restored");
        require(restored.fuel==131 && restored.maxFuel==500 && restored.temperature==1000,
                "Fuel values did not survive serialization");
        require(restored.currentFuel.getAmount()==700,
                "Controller fuel liquid did not survive serialization");
        require(restored.fluidTank.getTotalFluid()==1200,
                "Molten iron amount not preserved across controller NBT round-trip");
        require(restored.fluidTank.getFluidInTank(0).is(molten),
                "Molten iron type not preserved across controller NBT round-trip");
        System.out.println("HEPHAESTUS_ALPHA4 Controller NBT roundtrip inventory, progress, fuel, molten fluid OK");

        BlockPos tankPos=new BlockPos(36,y,20);
        level.setBlockAndUpdate(tankPos,ModBlocks.SEARED_FUEL_TANK.get().defaultBlockState());
        require(level.getBlockEntity(tankPos) instanceof SearedTankBlockEntity,
                "Fuel tank fixture missing");
        var tank=(SearedTankBlockEntity)level.getBlockEntity(tankPos);
        tank.getFluidTank().setFluid(new FluidStack(Fluids.LAVA,1500));
        var tankTag=tank.saveWithoutMetadata(level.registryAccess());
        var tankCopy=new SearedTankBlockEntity(tankPos,tank.getBlockState());
        tankCopy.loadWithComponents(net.minecraft.world.level.storage.TagValueInput.create(
                new net.minecraft.util.ProblemReporter.Collector(),level.registryAccess(),tankTag));
        require(tankCopy.getFluidTank().getFluidAmount()==1500 &&
                tankCopy.getFluidTank().getFluid().is(Fluids.LAVA),
                "Fuel tank 1500mB lava not preserved after NBT roundtrip");
        System.out.println("HEPHAESTUS_ALPHA4 Seared Tank NBT roundtrip 1500mB lava OK");
    }

""" +marker)
p.write_text(s,encoding="utf-8")
print("Developer Alpha4 tests installed: transaction rollback + NBT controller/tank")
