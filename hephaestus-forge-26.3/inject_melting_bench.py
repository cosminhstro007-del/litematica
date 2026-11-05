#!/usr/bin/env python3
"""Experimental developer-only load regression: 2,048 empty Smeltery slots
and a real melting recipe must still progress every tick. Never package it.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
base=root/"src/main/java/com/titammods"
p=base/"common/blockentities/SmelteryControllerBlockEntity.java"
s=p.read_text(encoding="utf-8")
a="    private int meltingScanTicks = 0;"
assert s.count(a)==1
s=s.replace(a,a+"\n    public static int PERF_LAB_RECIPE_SCANS = 0;")
a="    private void updateMeltingTimes() {\n"
assert s.count(a)==1
s=s.replace(a,a+"        PERF_LAB_RECIPE_SCANS++;\n")
p.write_text(s,encoding="utf-8")

p=base/"compat/port/validation/ForgeSmokeTest.java"
s=p.read_text(encoding="utf-8")
anchor='        System.out.println("HEPHAESTUS_VERIFY_SUCCESS recipes, table, basin, melter");'
assert s.count(anchor)==1
s=s.replace(anchor,"        verifyIndexedMelting(level,y);\n"+anchor)
marker="    public static void check(MinecraftServer server) {"
assert s.count(marker)==1
s=s.replace(marker,"""    private static void verifyIndexedMelting(ServerLevel level,int y) {
        var pos=new BlockPos(148,y,20);
        level.setBlockAndUpdate(pos,ModBlocks.SMELTERY_CONTROLLER.get().defaultBlockState());
        var be=(SmelteryControllerBlockEntity)level.getBlockEntity(pos);
        require(be!=null,"Indexed melting test controller missing");
        be.itemHandler=new com.titammods.compat.port.legacy.ItemStackHandler(2048);
        be.meltingProgress=new int[2048];
        be.meltingTime=new int[2048];
        be.meltingState=new int[2048];
        be.fluidTank.setCapacity(150000);

        try {
            var tick=SmelteryControllerBlockEntity.class.getDeclaredMethod("handleHeating");
            tick.setAccessible(true);
            int start=SmelteryControllerBlockEntity.PERF_LAB_RECIPE_SCANS;
            for (int i=0;i<50;i++) tick.invoke(be);
            int scans=SmelteryControllerBlockEntity.PERF_LAB_RECIPE_SCANS-start;
            require(scans>=9 && scans<=11,
                    "Inactive 2048-slot machine scanned recipes "+scans+" times instead of ~10");
            System.out.println("HEPHAESTUS_PERF_LAB_IDLE 2048 slots x 50 ticks, full scans="+scans);

            net.minecraft.world.item.ItemStack item=null;
            var choices=java.util.List.of(Items.IRON_ORE,Items.IRON_INGOT,
                    Items.GOLD_INGOT,Items.COPPER_INGOT,Items.REDSTONE);
            var recipe=(com.titammods.setup.ModRecipes.MeltingRecipe)null;
            for(var candidate:choices) {
                var test=new ItemStack(candidate);
                var rr=com.titammods.common.recipe.HephaestusRecipeCache.melting(level,test);
                if(rr!=null && rr.time()>14) {item=test;recipe=rr;break;}
            }
            require(item!=null,"No suitable >14-tick melting recipe found for test fixture");
            be.itemHandler.setStackInSlot(0,item);
            be.temperature=10000;
            be.fuel=200;
            int s0=SmelteryControllerBlockEntity.PERF_LAB_RECIPE_SCANS;
            for(int t=0;t<12;t++) tick.invoke(be);
            int progress=be.meltingProgress[0];
            require(progress==12,"Molten processing no longer advances every tick: "+progress);
            int scansActive=SmelteryControllerBlockEntity.PERF_LAB_RECIPE_SCANS-s0;
            require(scansActive<=4,
                    "Active 2048-slot Smeltery scanned all slots too often: "+scansActive);
            System.out.println("HEPHAESTUS_PERF_LAB_ACTIVE 2048 slots, 12 real melting ticks, full scans="+scansActive);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("Indexed melting workload failed",e);
        }
    }

"""+marker)
p.write_text(s,encoding="utf-8")
print("Experimental indexed melting tests injected")
