#!/usr/bin/env python3
"""Alpha5: development-only idle packet count and deterministic 100-machine tick
workload, inserted AFTER the publishable JAR is built; not shipped to players.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
base=root/"src/main/java/com/titammods"
p=base/"common/blockentities/SmelteryControllerBlockEntity.java"
s=p.read_text(encoding="utf-8")
anchor="    private int ioRefreshCounter = 0;"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n    public static int PERF_DEBUG_IDLE_PACKET_COUNT = 0;")
a="""            if (fuelInfoChanged || (isFormed && fuel > 0))
                level.sendBlockUpdated(pos, getBlockState(), getBlockState(), Block.UPDATE_ALL);"""
b="""            if (fuelInfoChanged || (isFormed && fuel > 0)) {
                PERF_DEBUG_IDLE_PACKET_COUNT++;
                level.sendBlockUpdated(pos, getBlockState(), getBlockState(), Block.UPDATE_ALL);
            }"""
assert s.count(a)==1
s=s.replace(a,b)
p.write_text(s,encoding="utf-8")
p=base/"compat/port/validation/ForgeSmokeTest.java"
s=p.read_text(encoding="utf-8")
anchor='        System.out.println("HEPHAESTUS_VERIFY_SUCCESS recipes, table, basin, melter");'
assert s.count(anchor)==1
s=s.replace(anchor,"        verifyNoIdleSyncSpam(level,y);\n"+anchor)
marker="    public static void check(MinecraftServer server) {"
assert s.count(marker)==1
s=s.replace(marker,"""    private static void verifyNoIdleSyncSpam(ServerLevel level,int y) {
        java.util.ArrayList<SmelteryControllerBlockEntity> machines =
                new java.util.ArrayList<>();
        int x0=110;
        for(int i=0;i<100;i++) {
            BlockPos pos=new BlockPos(x0+(i%10)*2,y,30+(i/10)*2);
            level.setBlockAndUpdate(pos,ModBlocks.SMELTERY_CONTROLLER.get().defaultBlockState());
            require(level.getBlockEntity(pos) instanceof SmelteryControllerBlockEntity,
                    "Idle performance fixture controller missing");
            machines.add((SmelteryControllerBlockEntity)level.getBlockEntity(pos));
        }
        int before=SmelteryControllerBlockEntity.PERF_DEBUG_IDLE_PACKET_COUNT;
        long begin=System.nanoTime();
        for(int t=0;t<40;t++) for(var be:machines)
            be.tick(level,be.getBlockPos(),be.getBlockState());
        long elapsed=System.nanoTime()-begin;
        int sent=SmelteryControllerBlockEntity.PERF_DEBUG_IDLE_PACKET_COUNT-before;
        require(sent==0,"100 idle Smelteries sent "+sent+
                " redundant full-block-entity packets over 40 ticks");
        System.out.println("HEPHAESTUS_ALPHA5_PERF 100 idle Smelteries x 40 ticks: redundant packets=0, execution="+
                (elapsed/1000000.0)+"ms");
    }

"""+marker)
p.write_text(s,encoding="utf-8")
print("ALPHA5_DEV_BENCH: 100 idle controllers x 40 ticks, assert zero redundant full-BE packet sends")
