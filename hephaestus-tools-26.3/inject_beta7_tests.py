#!/usr/bin/env python3
"""Tools Beta7 isolated developer-only NBT and two-player double-crafting tests.
Runs after inject_workbench_test.py, after production JAR compilation.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/"src/main/java/com/titammods/hephaestus_tools/compat/port/validation/WorkbenchSmokeTest.java"
s=p.read_text(encoding="utf-8")
anchor='        System.out.println("HEPHAESTUS_WORKBENCH_OK pickaxe GUI menu preview, click, material components, input consumption");'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"""
        checkWorkbenchReload(level,pos,be);
        checkTwoPlayerCraft(level,pos.getY());
""")
marker="    public static void check(MinecraftServer server) {"
assert s.count(marker)==1
s=s.replace(marker,"""    private static void checkWorkbenchReload(ServerLevel level,BlockPos pos,
                                             ArsenalTableBlockEntity be) {
        // A live client BE can get an older or incomplete NBT payload. Fields not
        // present must clear old items instead of retaining phantom/duplicated stacks.
        be.getUpgradeSlot().setStackInSlot(0,new ItemStack(Items.DIAMOND));
        be.getBlueprintSlot().setStackInSlot(0,new ItemStack(Items.EMERALD));
        be.getInputSlots().setStackInSlot(0,new ItemStack(Items.REDSTONE));
        be.getOutputSlot().setStackInSlot(0,new ItemStack(Items.IRON_PICKAXE));
        var tag=be.saveWithoutMetadata(level.registryAccess());
        tag.remove("Upgrade");
        tag.remove("Blueprint");
        tag.remove("Inputs");
        tag.remove("Output");
        be.loadWithComponents(net.minecraft.world.level.storage.TagValueInput.create(
                new net.minecraft.util.ProblemReporter.Collector(),level.registryAccess(),tag));
        require(be.getUpgradeSlot().getStackInSlot(0).isEmpty(),
                "Workbench kept phantom upgrade after partial NBT reload");
        require(be.getBlueprintSlot().getStackInSlot(0).isEmpty(),
                "Workbench kept phantom blueprint after partial NBT reload");
        require(be.getInputSlots().getStackInSlot(0).isEmpty(),
                "Workbench kept phantom input after partial NBT reload");
        require(be.getOutputSlot().getStackInSlot(0).isEmpty(),
                "Workbench kept phantom output after partial NBT reload");
        System.out.println("HEPHAESTUS_BETA7 Workbench partial NBT reload clears old slots OK");
    }

    private static void checkTwoPlayerCraft(ServerLevel level,int y) {
        BlockPos pos=new BlockPos(54,y,20);
        level.setBlockAndUpdate(pos,ModBlocks.ARSENAL_TABLE.get().defaultBlockState());
        var be=(ArsenalTableBlockEntity)level.getBlockEntity(pos);
        require(be!=null,"Two-player Workbench missing");
        MaterialId iron=MaterialId.of("hephaestus_tools","iron");
        ToolAssembly.init();
        var ass=ToolAssembly.REGISTRY.stream()
                .filter(a->a.result()==ModItems.PICKAXE.get()).findFirst().orElseThrow();
        for(int i=0;i<ass.parts().size();i++) {
            var part=((ToolPartItem)ass.parts().get(i)).withMaterial(iron);
            be.getInputSlots().setStackInSlot(i,part);
        }
        var a=net.neoforged.neoforge.common.util.FakePlayerFactory.get(level,
                new com.mojang.authlib.GameProfile(
                        java.util.UUID.nameUUIDFromBytes("HephTestA".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                        "HephTestA"));
        var b=net.neoforged.neoforge.common.util.FakePlayerFactory.get(level,
                new com.mojang.authlib.GameProfile(
                        java.util.UUID.nameUUIDFromBytes("HephTestB".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                        "HephTestB"));
        a.setPos(pos.getX()+0.5,pos.getY()+1,pos.getZ()+0.5);
        b.setPos(pos.getX()+0.5,pos.getY()+1,pos.getZ()+0.5);
        var menuA=new WorkbenchMenu(24,a.getInventory(),be);
        var menuB=new WorkbenchMenu(25,b.getInventory(),be);
        require(menuA.canAssemble() && menuB.canAssemble(),"Both players cannot see valid inputs");
        require(menuA.clickMenuButton(a,ArsenalTableMenu.ASSEMBLE),"First player could not craft");
        require(!menuB.clickMenuButton(b,ArsenalTableMenu.ASSEMBLE),
                "Second player duplicated the same crafting ingredients");
        ItemStack first=menuA.quickMoveStack(a,5);
        require(first.is(ModItems.PICKAXE.get()),"First player failed shift-click output");
        require(menuA.quickMoveStack(a,5).isEmpty(),
                "Workbench shift-click repeated on empty output");
        require(!menuB.clickMenuButton(b,ArsenalTableMenu.ASSEMBLE),
                "Second player crafted again after output extraction");
        require(be.getOutputSlot().getStackInSlot(0).isEmpty(),
                "Workbench retained duplicate output after shift-click");
        int count=0;
        for(int i=0;i<a.getInventory().getContainerSize();i++) {
            ItemStack stack=a.getInventory().getItem(i);
            if(stack.is(ModItems.PICKAXE.get())) count += stack.getCount();
        }
        require(count==1,"Expected exactly one pickaxe in player inventory, got "+count);
        System.out.println("HEPHAESTUS_BETA7 two-player double craft and repeated shift-click anti-dupe OK");
    }

"""+marker)
s=s.replace("import net.minecraft.world.item.ItemStack;","import net.minecraft.world.item.ItemStack;\nimport net.minecraft.world.item.Items;")
p.write_text(s,encoding="utf-8")
print("BETA7_TESTS: injected two-player Workbench anti-dupe and partial NBT tests")
