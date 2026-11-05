#!/usr/bin/env python3
"""Tools Beta6 JEI lifecycle: remove obsolete variants when switching servers,
prevent old material search results from leaking between different worlds.
Preserves Beta5 iron-casting mixin, block interactions and Beta4 durability rules.
"""
from pathlib import Path
import sys,re
root=Path(sys.argv[1]).resolve()
base=root/"src/main/java/com/titammods/hephaestus_tools"
p=base/"compat/jei/HephaestusToolsJeiPlugin.java"
s=p.read_text(encoding="utf-8")
old="    private static final Set<String> registered = new HashSet<>();"
new="""    // Track every ingredient *we* injected, so reloading a server with different
    // allowed materials cannot leave phantom variants in JEI.
    private static final java.util.Map<String, ItemStack> registered = new java.util.LinkedHashMap<>();"""
assert s.count(old)==1
s=s.replace(old,new)
start=s.index("    @Override public void onRuntimeAvailable(IJeiRuntime jei) {")
end=s.index("\n}",start)
s=s[:start]+"""    @Override public synchronized void onRuntimeAvailable(IJeiRuntime jei) {
        runtime = jei;
        registered.clear();
        refreshVariants();
    }

    @Override public synchronized void onRuntimeUnavailable() {
        runtime = null;
        registered.clear();
    }

    /** Remove old server-only part entries before switching worlds. */
    public static synchronized void clearVariants() {
        IJeiRuntime jei = runtime;
        if (jei != null && !registered.isEmpty()) {
            try {
                jei.getIngredientManager().removeIngredientsAtRuntime(
                        VanillaTypes.ITEM_STACK, new ArrayList<>(registered.values()));
            } catch (RuntimeException error) {
                LOG.warn("Could not clear old JEI variants: {}", error.getMessage());
            }
        }
        registered.clear();
    }

    /** May run during JEI startup or after MaterialsPayload arrives. */
    public static synchronized void refreshVariants() {
        IJeiRuntime jei = runtime;
        if (jei == null) return;
        java.util.Map<String, ItemStack> desired = new java.util.LinkedHashMap<>();
        for (var mat : MaterialManager.getInstance().getAllMaterials()) {
            MaterialId id = mat.id();
            for (var deferredPart : ModItems.PARTS) {
                String key = deferredPart.getId() + "|" + id;
                desired.put(key, deferredPart.get().withMaterial(id));
            }
        }
        List<ItemStack> obsolete = new ArrayList<>();
        for (var entry : registered.entrySet()) {
            if (!desired.containsKey(entry.getKey())) obsolete.add(entry.getValue());
        }
        List<ItemStack> added = new ArrayList<>();
        for (var entry : desired.entrySet()) {
            if (!registered.containsKey(entry.getKey())) added.add(entry.getValue());
        }
        try {
            if (!obsolete.isEmpty()) {
                jei.getIngredientManager().removeIngredientsAtRuntime(
                        VanillaTypes.ITEM_STACK, obsolete);
                registered.keySet().retainAll(desired.keySet());
            }
            if (!added.isEmpty()) {
                jei.getIngredientManager().addIngredientsAtRuntime(VanillaTypes.ITEM_STACK, added);
                for (var entry : desired.entrySet()) {
                    registered.putIfAbsent(entry.getKey(), entry.getValue());
                }
            }
            if (!obsolete.isEmpty() || !added.isEmpty())
                LOG.info("JEI materials reconciled: {} added, {} removed",
                        added.size(), obsolete.size());
        } catch (RuntimeException error) {
            LOG.warn("JEI material variant update failed: {}", error.getMessage());
        }
    }
""" +s[end:]
p.write_text(s,encoding="utf-8")

p=base/"compat/jei/SyncedCastingRecipes.java"
s=p.read_text(encoding="utf-8")
old="""    public static void onLoggingOut(ClientPlayerNetworkEvent.LoggingOut event) {
        recipes = null;
    }"""
new="""    public static void onLoggingOut(ClientPlayerNetworkEvent.LoggingOut event) {
        recipes = null;
        // A client can join a new server with a different material datapack.
        // Clear stale material definitions and remove JEI entries added by us.
        if (net.neoforged.fml.ModList.get().isLoaded("jei"))
            HephaestusToolsJeiPlugin.clearVariants();
        com.titammods.hephaestus_tools.materials.MaterialManager.receiveSync(java.util.Map.of());
    }"""
assert s.count(old)==1, "SyncedCastingRecipes logout hook changed"
s=s.replace(old,new)
p.write_text(s,encoding="utf-8")

p=root/"gradle.properties"
s=p.read_text(encoding="utf-8")
s,n=re.subn(r"(?m)^mod_version=.*$","mod_version=1.0.11-unofficial-26.3-beta6",s)
assert n==1
p.write_text(s,encoding="utf-8")
print("BETA6_STABILITY: JEI material variants are reconciled, removed on logout, runtime references released.")
