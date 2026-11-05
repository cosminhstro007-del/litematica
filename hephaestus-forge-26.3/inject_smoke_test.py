#!/usr/bin/env python3
"""Inject smoke-test hooks into *development server run only*.
The build task already emitted the release jar before this injection. Do not
publish debug tests inside production jar.
"""
from pathlib import Path
import sys
src=Path(sys.argv[1]).resolve()/"src/main/java/com/titammods"
main=src/"TitamMods.java"
s=main.read_text(encoding="utf-8")
anchor="        HephaestusFluids.registerFluids();"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"""
        // Development-only automated smoke test. Not included in the published release jar.
        NeoForge.EVENT_BUS.addListener(
                (net.neoforged.neoforge.event.server.ServerStartedEvent event) ->
                        com.titammods.compat.port.validation.ForgeSmokeTest.check(event.getServer()));
""")
main.write_text(s,encoding="utf-8")
d=src/"compat/port/validation"
d.mkdir(parents=True,exist_ok=True)
p=d/"ForgeSmokeTest.java"
p.write_text("""package com.titammods.compat.port.validation;

import com.titammods.common.blockentities.*;
import com.titammods.common.recipe.HephaestusRecipeCache;
import com.titammods.setup.ModBlocks;
import com.titammods.setup.ModItems;
import com.titammods.setup.ModRecipes;
import com.titammods.compat.port.legacy.IFluidHandler;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.fluids.FluidStack;

public final class ForgeSmokeTest {
    private static void require(boolean ok, String message) {
        if (!ok) throw new IllegalStateException("HEPHAESTUS_VERIFY_FAILED: " + message);
    }

    public static void check(MinecraftServer server) {
        ServerLevel level = server.overworld();
        var map = server.getRecipeManager().recipeMap();
        int melting = 0, tableRecipes = 0, basinRecipes = 0;
        for (var ignored : map.byType(ModRecipes.MELTING_TYPE.get())) melting++;
        for (var ignored : map.byType(ModRecipes.CASTING_TABLE_TYPE.get())) tableRecipes++;
        for (var ignored : map.byType(ModRecipes.CASTING_BASIN_TYPE.get())) basinRecipes++;
        System.out.println("HEPHAESTUS_VERIFY recipe counts melting=" + melting +
                " table=" + tableRecipes + " basin=" + basinRecipes);
        require(melting > 20 && tableRecipes > 20 && basinRecipes > 8,
                "Recipe registry missing most original Hephaestus recipes");

        Fluid moltenIron = BuiltInRegistries.FLUID.getValue(
                Identifier.fromNamespaceAndPath("hephaestus", "molten_iron"));
        require(moltenIron != null && !moltenIron.isSame(Fluids.EMPTY), "No molten iron");
        require(HephaestusRecipeCache.melting(level, new ItemStack(Items.IRON_PICKAXE)) != null,
                "Melting recipe iron pickaxe not found via cache");
        require(HephaestusRecipeCache.table(level, new ItemStack(ModItems.INGOT_CAST.get()), moltenIron) != null,
                "Table cast iron ingot recipe not found via cache");
        require(HephaestusRecipeCache.basin(level, ItemStack.EMPTY, moltenIron) != null,
                "Basin cast iron block recipe not found via cache");
        System.out.println("HEPHAESTUS_VERIFY recipe lookups OK");

        int y = level.getSeaLevel()+18;
        // Real block entities, real recipes, no fake outputs.
        BlockPos tablePos = new BlockPos(20,y,20);
        level.setBlockAndUpdate(tablePos, ModBlocks.SEARED_TABLE.get().defaultBlockState());
        require(level.getBlockEntity(tablePos) instanceof TableBlockEntity, "Table block entity missing");
        TableBlockEntity table = (TableBlockEntity)level.getBlockEntity(tablePos);
        table.inventory.setStackInSlot(0, new ItemStack(ModItems.INGOT_CAST.get()));
        require(table.tank.fill(new FluidStack(moltenIron,90), IFluidHandler.FluidAction.EXECUTE)==90,
                "Iron fluid refused by casting table");
        for(int i=0;i<160;i++) table.tick();
        require(table.inventory.getStackInSlot(1).is(Items.IRON_INGOT),
                "Casting table did not produce iron ingot");
        System.out.println("HEPHAESTUS_VERIFY actual cast iron ingot OK");

        BlockPos basinPos = new BlockPos(22,y,20);
        level.setBlockAndUpdate(basinPos, ModBlocks.SEARED_BASIN.get().defaultBlockState());
        require(level.getBlockEntity(basinPos) instanceof BasinBlockEntity, "Basin block entity missing");
        BasinBlockEntity basin = (BasinBlockEntity)level.getBlockEntity(basinPos);
        require(basin.tank.fill(new FluidStack(moltenIron,810), IFluidHandler.FluidAction.EXECUTE)==810,
                "Iron fluid refused by casting basin");
        for(int i=0;i<260;i++) basin.tick();
        require(basin.inventory.getStackInSlot(0).is(Items.IRON_BLOCK),
                "Casting basin did not produce iron block");
        System.out.println("HEPHAESTUS_VERIFY actual cast iron block OK");

        BlockPos fuelPos = new BlockPos(24,y-1,20);
        level.setBlockAndUpdate(fuelPos, ModBlocks.SEARED_FUEL_TANK.get().defaultBlockState());
        require(level.getBlockEntity(fuelPos) instanceof SearedTankBlockEntity, "Fuel tank missing");
        SearedTankBlockEntity fuel = (SearedTankBlockEntity)level.getBlockEntity(fuelPos);
        require(fuel.getFluidTank().fill(new FluidStack(Fluids.LAVA,1000), IFluidHandler.FluidAction.EXECUTE)==1000,
                "Fuel tank did not take lava");
        BlockPos melterPos = fuelPos.above();
        level.setBlockAndUpdate(melterPos, ModBlocks.SEARED_MELTER.get().defaultBlockState());
        require(level.getBlockEntity(melterPos) instanceof MelterBlockEntity, "Melter block entity missing");
        MelterBlockEntity melter=(MelterBlockEntity)level.getBlockEntity(melterPos);
        melter.inventory.setStackInSlot(0,new ItemStack(Items.REDSTONE));
        for(int i=0;i<210;i++) melter.tick(level,melterPos,melter.getBlockState());
        require(melter.inventory.getStackInSlot(0).isEmpty() && melter.tank.getFluidAmount() >=10,
                "Melter did not turn redstone into molten redstone");
        System.out.println("HEPHAESTUS_VERIFY actual melting redstone OK");

        System.out.println("HEPHAESTUS_VERIFY_SUCCESS recipes, table, basin, melter");
    }
}
""",encoding="utf-8")
print("Injected non-production Forge smoke tests for recipes, casting table/basin and melter")
