#!/usr/bin/env python3
"""Development-only two-boot persistence test for Hephaestus Forge and Tools.
Tests real Minecraft world chunk serialization on shutdown/restart (not merely
in-memory ValueOutput roundtrip). Applied after JAR compilation, NEVER shipped.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/"src/main/java/com/titammods/TitamMods.java"
s=p.read_text(encoding="utf-8")
anchor="        HephaestusFluids.registerFluids();"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"""
        NeoForge.EVENT_BUS.addListener(
                (net.neoforged.neoforge.event.server.ServerStartedEvent event) ->
                        com.titammods.compat.port.validation.PersistenceSmokeTest.check(event.getServer()));
""")
p.write_text(s,encoding="utf-8")
dest=root/"src/main/java/com/titammods/compat/port/validation/PersistenceSmokeTest.java"
dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text("""package com.titammods.compat.port.validation;

import java.nio.file.Files;
import java.nio.file.Path;
import com.titammods.setup.ModBlocks;
import com.titammods.common.blockentities.*;
import com.titammods.compat.port.legacy.IFluidHandler;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.fluids.FluidStack;

public final class PersistenceSmokeTest {
    private static void require(boolean ok,String message) {
        if (!ok) throw new IllegalStateException("HEPHAESTUS_PERSIST_FAILED: "+message);
    }

    private static final Path MARKER = Path.of(".hephaestus-world-persist-stage");

    public static void check(MinecraftServer server) {
        try {
            ServerLevel level=server.overworld();
            int y=level.getSeaLevel()+18;
            BlockPos fuelPos=new BlockPos(72,y,19);
            BlockPos castingPos=new BlockPos(73,y,19);
            BlockPos controllerPos=new BlockPos(74,y,19);
            BlockPos workbenchPos=new BlockPos(75,y,19);
            var moltenIron=BuiltInRegistries.FLUID.getValue(
                    Identifier.fromNamespaceAndPath("hephaestus","molten_iron"));
            require(moltenIron!=null,"missing molten iron registry entry");
            if (!Files.exists(MARKER)) {
                level.setBlockAndUpdate(fuelPos,ModBlocks.SEARED_FUEL_TANK.get().defaultBlockState());
                var fuel=(SearedTankBlockEntity)level.getBlockEntity(fuelPos);
                fuel.getFluidTank().setFluid(new FluidStack(Fluids.LAVA,1400));
                fuel.setChanged();

                level.setBlockAndUpdate(castingPos,ModBlocks.SEARED_TABLE.get().defaultBlockState());
                var table=(TableBlockEntity)level.getBlockEntity(castingPos);
                table.inventory.setStackInSlot(0,new ItemStack(Items.DIAMOND));
                require(table.tank.fill(new FluidStack(moltenIron,450),
                        IFluidHandler.FluidAction.EXECUTE)==450, "casting fluid seed failed");
                table.setChanged();

                level.setBlockAndUpdate(controllerPos,ModBlocks.SMELTERY_CONTROLLER.get().defaultBlockState());
                var controller=(SmelteryControllerBlockEntity)level.getBlockEntity(controllerPos);
                controller.itemHandler=new com.titammods.compat.port.legacy.ItemStackHandler(2);
                controller.itemHandler.setStackInSlot(0,new ItemStack(Items.IRON_ORE));
                controller.meltingProgress=new int[] {19,0};
                controller.meltingTime=new int[] {90,0};
                controller.meltingState=new int[] {0,0};
                controller.fluidTank.setCapacity(5000);
                require(controller.fluidTank.fill(new FluidStack(moltenIron,700),
                        IFluidHandler.FluidAction.EXECUTE)==700,"controller fluid seed failed");
                controller.setChanged();

                var toolsBlock=BuiltInRegistries.BLOCK.getValue(
                        Identifier.fromNamespaceAndPath("hephaestus_tools","arsenal_table"));
                var toolsPart=BuiltInRegistries.ITEM.getValue(
                        Identifier.fromNamespaceAndPath("hephaestus_tools","pick_head"));
                require(toolsBlock!=null && toolsPart!=null,"Tools integration registry entries missing");
                level.setBlockAndUpdate(workbenchPos,toolsBlock.defaultBlockState());
                var workbench=level.getBlockEntity(workbenchPos);
                require(workbench!=null,"Tools workbench block entity missing");
                Object input=workbench.getClass().getMethod("getInputSlots").invoke(workbench);
                input.getClass().getMethod("setStackInSlot",int.class,ItemStack.class)
                        .invoke(input,0,new ItemStack(toolsPart));
                workbench.setChanged();

                server.saveEverything(false,true,true);
                Files.writeString(MARKER,"saved");
                System.out.println("HEPHAESTUS_PERSIST_SEEDED saved world and halting");
                server.halt(false);
            } else {
                level.getChunkAt(fuelPos);
                level.getChunkAt(castingPos);
                level.getChunkAt(controllerPos);
                level.getChunkAt(workbenchPos);

                require(level.getBlockEntity(fuelPos) instanceof SearedTankBlockEntity,
                        "Fuel tank missing after real restart");
                var fuel=(SearedTankBlockEntity)level.getBlockEntity(fuelPos);
                require(fuel.getFluidTank().getFluid().is(Fluids.LAVA)
                        && fuel.getFluidTank().getFluidAmount()==1400,
                        "Fuel tank amount/type changed after restart");

                require(level.getBlockEntity(castingPos) instanceof TableBlockEntity,
                        "Casting table missing after restart");
                var table=(TableBlockEntity)level.getBlockEntity(castingPos);
                require(table.inventory.getStackInSlot(0).is(Items.DIAMOND),
                        "Casting table inventory changed after restart");
                require(table.tank.getFluid().is(moltenIron)
                        && table.tank.getFluidAmount()==450,
                        "Casting table molten iron amount changed after restart");

                require(level.getBlockEntity(controllerPos) instanceof SmelteryControllerBlockEntity,
                        "Smeltery controller missing after restart");
                var controller=(SmelteryControllerBlockEntity)level.getBlockEntity(controllerPos);
                require(controller.itemHandler.getSlots()==2 &&
                        controller.itemHandler.getStackInSlot(0).is(Items.IRON_ORE),
                        "Smeltery inventory changed after restart");
                require(controller.fluidTank.getTotalFluid()==700,
                        "Smeltery molten fluid amount changed after restart");
                require(controller.meltingProgress.length==2 &&
                        controller.meltingProgress[0]==19,
                        "Smeltery melting progress lost across actual shutdown");

                var workbench=level.getBlockEntity(workbenchPos);
                require(workbench!=null,"Tools workbench missing after restart");
                Object input=workbench.getClass().getMethod("getInputSlots").invoke(workbench);
                ItemStack part=(ItemStack)input.getClass()
                        .getMethod("getStackInSlot",int.class).invoke(input,0);
                require(part.is(BuiltInRegistries.ITEM.getValue(
                        Identifier.fromNamespaceAndPath("hephaestus_tools","pick_head"))),
                        "Tools part missing after restart");
                System.out.println("HEPHAESTUS_PERSIST_VERIFIED restart passed for Forge fuel tank, casting table, controller and Tools workbench");
                server.halt(false);
            }
        } catch (Exception e) {
            throw new IllegalStateException("HEPHAESTUS_PERSIST_FAILED",e);
        }
    }
}
""",encoding="utf-8")
print("Injected developer-only two-boot persisted world test")
