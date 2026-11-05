#!/usr/bin/env python3
"""Development-only Tools 26.3 workbench assembly regression test.
Runs on dedicated dev server with Forge; test code is never included in published JAR.
"""
from pathlib import Path
import sys
src=Path(sys.argv[1]).resolve()/"src/main/java/com/titammods/hephaestus_tools"
p=src/"HephaestusTools.java"
s=p.read_text(encoding="utf-8")
anchor="        modBus.addListener(this::commonSetup);"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"""
        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(
            (net.neoforged.neoforge.event.server.ServerStartedEvent event) ->
                com.titammods.hephaestus_tools.compat.port.validation.WorkbenchSmokeTest.check(
                        event.getServer()));
""")
p.write_text(s,encoding="utf-8")
p=src/"compat/port/validation/WorkbenchSmokeTest.java"
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text("""package com.titammods.hephaestus_tools.compat.port.validation;

import com.titammods.hephaestus_tools.materials.MaterialId;
import com.titammods.hephaestus_tools.materials.MaterialManager;
import com.titammods.hephaestus_tools.registry.ModBlocks;
import com.titammods.hephaestus_tools.registry.ModItems;
import com.titammods.hephaestus_tools.table.ToolAssembly;
import com.titammods.hephaestus_tools.tables.blockentity.ArsenalTableBlockEntity;
import com.titammods.hephaestus_tools.tables.menu.ArsenalTableMenu;
import com.titammods.hephaestus_tools.tables.menu.WorkbenchMenu;
import com.titammods.hephaestus_tools.tools.nbt.ToolStack;
import com.titammods.hephaestus_tools.tools.part.ToolPartItem;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;

public final class WorkbenchSmokeTest {
    private static void require(boolean ok,String msg) {
        if (!ok) throw new IllegalStateException("HEPHAESTUS_WORKBENCH_FAILED: "+msg);
    }
    public static void check(MinecraftServer server) {
        ServerLevel level=server.overworld();
        MaterialId iron=MaterialId.of("hephaestus_tools","iron");
        require(MaterialManager.getInstance().getMaterial(iron)!=null,"iron material not loaded");
        ToolAssembly.init();
        var assembly=ToolAssembly.REGISTRY.stream()
                .filter(a->a.result()==ModItems.PICKAXE.get())
                .findFirst().orElseThrow(()->new IllegalStateException("No pickaxe layout"));
        require(assembly.parts().size()>=2 && assembly.parts().size()<=4,"Pickaxe part count wrong");

        BlockPos pos=new BlockPos(31,level.getSeaLevel()+17,20);
        level.setBlockAndUpdate(pos,ModBlocks.ARSENAL_TABLE.get().defaultBlockState());
        require(level.getBlockEntity(pos) instanceof ArsenalTableBlockEntity,
                "Workbench block entity missing");
        var be=(ArsenalTableBlockEntity)level.getBlockEntity(pos);
        for(int i=0;i<assembly.parts().size();i++) {
            require(assembly.parts().get(i) instanceof ToolPartItem,
                    "Non-part ingredient in pickaxe layout");
            var part=((ToolPartItem)assembly.parts().get(i)).withMaterial(iron);
            be.getInputSlots().setStackInSlot(i,part);
        }
        var player=net.neoforged.neoforge.common.util.FakePlayerFactory.getMinecraft(level);
        player.setPos(pos.getX()+0.5,pos.getY()+1,pos.getZ()+0.5);
        var menu=new WorkbenchMenu(22,player.getInventory(),be);
        require(menu.getActiveTab()==0,"Workbench opened on wrong tab");
        require(menu.preview().is(ModItems.PICKAXE.get()),"Workbench did not show pickaxe preview");
        require(menu.canAssemble(),"Workbench refuses completed recipe");
        boolean crafted=menu.clickMenuButton(player,ArsenalTableMenu.ASSEMBLE);
        require(crafted,"Workbench assemble button refused click");
        ItemStack output=be.getOutputSlot().getStackInSlot(0);
        require(output.is(ModItems.PICKAXE.get()),"Workbench produced wrong output");
        require(ToolStack.isInitialized(output),"Crafted pickaxe lacks construction data");
        require(ToolStack.getMaterials(output).size()==assembly.parts().size(),
                "Crafted pickaxe material part count wrong");
        for (var mat:ToolStack.getMaterials(output))
            require(iron.equals(mat),"Crafted pickaxe material was lost");
        for (int i=0;i<assembly.parts().size();i++)
            require(be.getInputSlots().getStackInSlot(i).isEmpty(),
                    "Crafted pickaxe ingredients weren't consumed");
        System.out.println("HEPHAESTUS_WORKBENCH_OK pickaxe GUI menu preview, click, material components, input consumption");
    }
}
""",encoding="utf-8")
print("Injected real WorkbenchMenu test after production build; no published JAR changed")
