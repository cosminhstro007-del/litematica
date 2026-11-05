#!/usr/bin/env python3
"""Extra Beta7 bulk slot persistence regression test (developer-only).
The Workbench input slot supports 4000-count upgrade resources; the standard
ItemStack serializer is smaller, so the mod uses a separate InputCounts field.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1]).resolve()/"src/main/java/com/titammods/hephaestus_tools/compat/port/validation/WorkbenchSmokeTest.java"
s=p.read_text(encoding="utf-8")
anchor="        checkTwoPlayerCraft(level,pos.getY());"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n        checkBulkCountPersistence(level,pos.getY());")
mark="    public static void check(MinecraftServer server) {"
assert s.count(mark)==1
s=s.replace(mark,"""    private static void checkBulkCountPersistence(ServerLevel level,int y) {
        var pos=new BlockPos(61,y,20);
        var state=ModBlocks.ARSENAL_TABLE.get().defaultBlockState();
        var be=new ArsenalTableBlockEntity(pos,state);
        int amount=3500;
        be.getInputSlots().setStackInSlot(0,new ItemStack(Items.REDSTONE,amount));
        require(be.getInputSlots().getStackInSlot(0).getCount()==amount,
                "Bulk slot clamps to vanilla stack max, losing resource count");
        var nbt=be.saveWithoutMetadata(level.registryAccess());
        var loaded=new ArsenalTableBlockEntity(pos,state);
        loaded.loadWithComponents(net.minecraft.world.level.storage.TagValueInput.create(
                new net.minecraft.util.ProblemReporter.Collector(),level.registryAccess(),nbt));
        int got=loaded.getInputSlots().getStackInSlot(0).getCount();
        require(got==amount,"Bulk input stack lost items during NBT roundtrip: "+got);
        System.out.println("HEPHAESTUS_BULK_OK 3500-count Workbench input survives NBT save/load");
    }

"""+mark)
p.write_text(s,encoding="utf-8")
print("Developer-only bulk 3500-count slot persistence validation injected")
