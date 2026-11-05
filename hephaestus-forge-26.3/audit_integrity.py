#!/usr/bin/env python3
"""Non-production compatibility audit of Hephaestus Forge 26.3 + Tools Beta4 + JEI.
Patches the development-only ForgeSmokeTest file and validates released class presence.
DOES NOT CHANGE THE RELEASE JAR.
"""
from pathlib import Path
from zipfile import ZipFile
import sys

root = Path(sys.argv[1]).resolve()
tools = Path(sys.argv[2]).resolve()
jar_paths = [p for p in (root/"build/libs").glob("*.jar") if not p.name.endswith(("-sources.jar","-javadoc.jar"))]
assert len(jar_paths)==1,jar_paths
forge = jar_paths[0]

with ZipFile(forge) as z:
    names = set(z.namelist())
    required=[
       "com/titammods/compat/jei/TitamModsJEIPlugin.class",
       "com/titammods/compat/jei/MelterCategory.class",
       "com/titammods/compat/jei/SmelteryCategory.class",
       "com/titammods/compat/jei/CastingTableCategory.class",
       "com/titammods/compat/jei/CastingBasinCategory.class",
       "com/titammods/compat/jei/AlloyCategory.class",
       "com/titammods/compat/jei/EntityMeltingCategory.class",
       "com/titammods/common/recipe/HephaestusRecipeCache.class",
       "com/titammods/common/blockentities/TableBlockEntity.class",
       "META-INF/neoforge.mods.toml",
    ]
    missing=[n for n in required if n not in names]
    assert not missing,"Forge release missing JEI/casting classes: "+repr(missing)
    toml=z.read("META-INF/neoforge.mods.toml").decode()
    assert 'modId="hephaestus"' in toml,toml[:300]
    print("HEPHAESTUS_INTEGRITY_STATIC Forge JEI plugin + six categories + recipe cache OK")

with ZipFile(tools) as z:
    names=set(z.namelist())
    required=[
       "com/titammods/hephaestus_tools/compat/jei/HephaestusToolsJeiPlugin.class",
       "com/titammods/hephaestus_tools/registry/ModComponents.class",
       "META-INF/neoforge.mods.toml"
    ]
    missing=[n for n in required if n not in names]
    assert not missing,"Tools Beta4 missing subtype JEI plugin: "+repr(missing)
    toml=z.read("META-INF/neoforge.mods.toml").decode()
    assert 'modId="hephaestus_tools"' in toml,toml[:300]
    has_mixin="com/titammods/hephaestus_tools/mixin/TableBlockEntityMixin.class" in names
    has_sync="com/titammods/hephaestus_tools/compat/jei/CastingRecipeSync.class" in names
    print(f"HEPHAESTUS_INTEGRITY_STATIC Tools JEI subtype plugin OK; Forge part-material mixin present={has_mixin}; recipe sync present={has_sync}")

p=root/"src/main/java/com/titammods/compat/port/validation/ForgeSmokeTest.java"
s=p.read_text(encoding="utf-8")
anchor='        System.out.println("HEPHAESTUS_VERIFY_SUCCESS recipes, table, basin, melter");'
assert s.count(anchor)==1
s=s.replace(anchor, """
        // Verify cross-mod casting using the actual recipe registered by Tools.
        var headCast = BuiltInRegistries.ITEM.getValue(
                Identifier.fromNamespaceAndPath("hephaestus_tools", "pick_head_cast"));
        var pickHead = BuiltInRegistries.ITEM.getValue(
                Identifier.fromNamespaceAndPath("hephaestus_tools", "pick_head"));
        var materialType = BuiltInRegistries.DATA_COMPONENT_TYPE.getValue(
                Identifier.fromNamespaceAndPath("hephaestus_tools", "part_material"));
        require(headCast != null && pickHead != null && materialType != null,
                "Tool head or part material component missing");

        var toolRecipe = HephaestusRecipeCache.table(level, new ItemStack(headCast), moltenIron, 180);
        require(toolRecipe != null, "Forge cannot see Tools iron pick-head casting recipe");
        require(toolRecipe.result().is(pickHead), "Tools cast recipe produces incorrect item");
        var toolTablePos = new BlockPos(26,y,20);
        level.setBlockAndUpdate(toolTablePos, ModBlocks.SEARED_TABLE.get().defaultBlockState());
        require(level.getBlockEntity(toolTablePos) instanceof TableBlockEntity, "Tools casting table entity missing");
        TableBlockEntity toolTable = (TableBlockEntity)level.getBlockEntity(toolTablePos);
        toolTable.inventory.setStackInSlot(0,new ItemStack(headCast));
        require(toolTable.tank.fill(new FluidStack(moltenIron,180), IFluidHandler.FluidAction.EXECUTE)==180,
                "Tools casting table rejected molten iron");
        for(int i=0;i<180;i++) toolTable.tick();
        ItemStack created = toolTable.inventory.getStackInSlot(1);
        require(created.is(pickHead), "Forge casting table failed to produce Tools pick head");
        boolean material = created.has(materialType);
        System.out.println("HEPHAESTUS_INTEGRITY Tools pick head cast from iron: item=OK materialComponent=" + material);
        System.out.println(material ?
                "HEPHAESTUS_INTEGRITY Tools material integration PASS" :
                "HEPHAESTUS_INTEGRITY Tools material integration INCOMPLETE (missing part_material on cast result)");
        System.out.println("HEPHAESTUS_VERIFY_SUCCESS recipes, table, basin, melter");
""")
p.write_text(s,encoding="utf-8")
print("Injected runtime cross-mod casting test. No release JAR changed.")
