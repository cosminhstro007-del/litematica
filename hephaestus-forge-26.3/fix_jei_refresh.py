#!/usr/bin/env python3
"""Forge Alpha2: keep JEI recipe pages current when connecting to dedicated servers.
The source mod already syncs all five custom recipe types via OnDatapackSyncEvent.
This patch ensures JEI sees them even if JEI initializes before the sync arrives.
"""
from pathlib import Path
import re,sys
root=Path(sys.argv[1]).resolve()
base=root/"src/main/java/com/titammods"
p=base/"compat/jei/TitamModsJEIPlugin.java"
s=p.read_text(encoding="utf-8")
s=s.replace("import mezz.jei.api.registration.IRecipeRegistration;",
    "import mezz.jei.api.registration.IRecipeRegistration;\nimport mezz.jei.api.runtime.IJeiRuntime;\nimport mezz.jei.api.recipe.IRecipeManager;")
anchor="public class TitamModsJEIPlugin implements IModPlugin {"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"""
    private static volatile IJeiRuntime runtime;
    private static RecipeMap visibleMap = RecipeMap.EMPTY;
    
    @Override
    public void onRuntimeAvailable(IJeiRuntime jei) {
        runtime = jei;
        refreshRecipes(ClientRecipes.getRecipes());
    }

    /** RecipesReceivedEvent may arrive after JEI has registered categories. */
    public static synchronized void refreshRecipes(RecipeMap incoming) {
        IJeiRuntime jei = runtime;
        if (jei == null || incoming == visibleMap) return;
        IRecipeManager recipes = jei.getRecipeManager();
        try {
            if (visibleMap != RecipeMap.EMPTY) {
                recipes.hideRecipes(MELTING_TYPE, values(visibleMap, ModRecipes.MELTING_TYPE.get()));
                recipes.hideRecipes(SMELTERY_TYPE, values(visibleMap, ModRecipes.MELTING_TYPE.get()));
                recipes.hideRecipes(CASTING_TABLE_TYPE, values(visibleMap, ModRecipes.CASTING_TABLE_TYPE.get()));
                recipes.hideRecipes(CASTING_BASIN_TYPE, values(visibleMap, ModRecipes.CASTING_BASIN_TYPE.get()));
                recipes.hideRecipes(ALLOY_TYPE, values(visibleMap, ModRecipes.ALLOY_TYPE.get()));
                recipes.hideRecipes(ENTITY_MELTING_TYPE, values(visibleMap, ModRecipes.ENTITY_MELTING_TYPE.get()));
            }
            if (incoming != RecipeMap.EMPTY) {
                var melting = values(incoming, ModRecipes.MELTING_TYPE.get());
                recipes.addRecipes(MELTING_TYPE, melting);
                recipes.addRecipes(SMELTERY_TYPE, melting);
                recipes.addRecipes(CASTING_TABLE_TYPE, values(incoming, ModRecipes.CASTING_TABLE_TYPE.get()));
                recipes.addRecipes(CASTING_BASIN_TYPE, values(incoming, ModRecipes.CASTING_BASIN_TYPE.get()));
                recipes.addRecipes(ALLOY_TYPE, values(incoming, ModRecipes.ALLOY_TYPE.get()));
                recipes.addRecipes(ENTITY_MELTING_TYPE, values(incoming, ModRecipes.ENTITY_MELTING_TYPE.get()));
            }
            visibleMap = incoming;
        } catch (RuntimeException error) {
            org.slf4j.LoggerFactory.getLogger(TitamModsJEIPlugin.class)
                    .warn("JEI recipe refresh failed: {}", error.getMessage());
        }
    }
    
    private static <T extends net.minecraft.world.item.crafting.Recipe<?>> List<T> values(
            RecipeMap map, net.minecraft.world.item.crafting.RecipeType<T> type) {
        return map.byType(type).stream().map(RecipeHolder::value).toList();
    }
""")
anchor="        RecipeMap recipes = ClientRecipes.getRecipes();"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n        visibleMap = recipes;")
p.write_text(s,encoding="utf-8")

p=base/"client/ClientRecipes.java"
s=p.read_text(encoding="utf-8")
old="""        recipes = event.getRecipeMap();"""
assert s.count(old)==1
s=s.replace(old,old+"""
        if (net.neoforged.fml.ModList.get().isLoaded("jei")) {
            com.titammods.compat.jei.TitamModsJEIPlugin.refreshRecipes(recipes);
        }""")
old="""        recipes = RecipeMap.EMPTY;"""
assert s.count(old)==1
s=s.replace(old,old+"""
        if (net.neoforged.fml.ModList.get().isLoaded("jei")) {
            com.titammods.compat.jei.TitamModsJEIPlugin.refreshRecipes(recipes);
        }""")
p.write_text(s,encoding="utf-8")

# Dedicated server protocol already sends custom recipe types on sync.
p=base/"TitamMods.java"
s=p.read_text(encoding="utf-8")
assert "e.sendRecipes(ModRecipes.MELTING_TYPE.get()" in s,"Recipe synchronization is missing"
p=root/"gradle.properties"
s=p.read_text(encoding="utf-8")
s,n=re.subn(r"(?m)^mod_version=.*$","mod_version=1.0.20-unofficial-26.3-alpha2",s)
assert n==1
p.write_text(s,encoding="utf-8")
print("FORGE_ALPHA2_JEI: six JEI categories refreshed on remote server recipes sync; offline Forge unaffected.")
