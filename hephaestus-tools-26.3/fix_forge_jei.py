#!/usr/bin/env python3
"""Hephaestus Tools 26.3 Beta 5: restore safe Forge casting material mixin
and JEI item subtypes / per-material ingredient variants.
Original project: titammods (MIT). Original tools Beta 4 stays untouched.
"""
from pathlib import Path
import sys,re
root=Path(sys.argv[1]).resolve()
base=root/"src/main/java/com/titammods/hephaestus_tools"

# Only the recipe return-value injection is enabled. We deliberately do not
# restore the fragile blockentity/local capture mixin.
p=base/"compat/ForgeMixinPlugin.java"
s=p.read_text(encoding="utf-8")
old="return List.of(); // Forge 26.3 integration deferred"
assert old in s,"Missing Beta4 ForgeMixinPlugin guard"
s=s.replace(old,"""return FMLLoader.getCurrent().getLoadingModList()
                .getModFileById(HephaestusTools.FORGE_MOD_ID) != null
                ? List.of("CastingTableRecipeMixin") : List.of();""")
p.write_text(s,encoding="utf-8")

# The original MixingTableRecipe return injection is already present in upstream:
# com.titammods.hephaestus_tools.mixin.CastingTableRecipeMixin.
# It patches only Tools part outputs with PART_MATERIAL from molten fluid ID.
p=base/"mixin/CastingTableRecipeMixin.java"
assert p.exists(), "Original Forge recipe mixin missing"
m=p.read_text(encoding="utf-8")
assert '@Mixin(targets = "com.titammods.setup.ModRecipes$CastingTableRecipe", remap = false)' in m
assert '@ModifyReturnValue(method = "result", at = @At("RETURN"))' in m
assert "ModComponents.PART_MATERIAL.get()" in m

# Replace the minimal JEI plugin with a runtime-aware variant registry. JEI can
# initialize before server-to-client material sync. Register missing variants both
# at JEI startup and after the existing MaterialsPayload arrives.
p=base/"compat/jei/HephaestusToolsJeiPlugin.java"
p.write_text("""package com.titammods.hephaestus_tools.compat.jei;

import com.titammods.hephaestus_tools.HephaestusTools;
import com.titammods.hephaestus_tools.materials.MaterialId;
import com.titammods.hephaestus_tools.materials.MaterialManager;
import com.titammods.hephaestus_tools.registry.ModComponents;
import com.titammods.hephaestus_tools.registry.ModItems;
import mezz.jei.api.IModPlugin;
import mezz.jei.api.JeiPlugin;
import mezz.jei.api.constants.VanillaTypes;
import mezz.jei.api.ingredients.subtypes.ISubtypeInterpreter;
import mezz.jei.api.registration.ISubtypeRegistration;
import mezz.jei.api.runtime.IJeiRuntime;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

@JeiPlugin
public class HephaestusToolsJeiPlugin implements IModPlugin {
    private static final Logger LOG = LoggerFactory.getLogger(HephaestusToolsJeiPlugin.class);
    private static final Identifier UID = Identifier.fromNamespaceAndPath(
            HephaestusTools.MOD_ID, "jei_plugin");
    private static volatile IJeiRuntime runtime;
    private static final Set<String> registered = new HashSet<>();

    @Override public Identifier getPluginUid() { return UID; }

    private static Set<Item> parts() {
        Set<Item> items = new java.util.LinkedHashSet<>();
        for (var entry : ModItems.PARTS) items.add(entry.get());
        return items;
    }

    @Override public void registerItemSubtypes(ISubtypeRegistration reg) {
        ISubtypeInterpreter<ItemStack> interpreter = (stack, context) -> {
            MaterialId id = stack.get(ModComponents.PART_MATERIAL.get());
            return id == null ? "none" : id.toString();
        };
        for (Item part : parts()) reg.registerSubtypeInterpreter(part, interpreter);
    }

    @Override public void onRuntimeAvailable(IJeiRuntime jei) {
        runtime = jei;
        registered.clear();
        refreshVariants();
    }

    /** Called after material synchronization, as JEI may already be open. */
    public static synchronized void refreshVariants() {
        IJeiRuntime jei = runtime;
        if (jei == null) return;
        List<ItemStack> variants = new ArrayList<>();
        Set<String> pending = new HashSet<>();
        for (var mat : MaterialManager.getInstance().getAllMaterials()) {
            MaterialId id = mat.id();
            for (var deferredPart : ModItems.PARTS) {
                String key = deferredPart.getId() + "|" + id;
                if (registered.contains(key)) continue;
                variants.add(deferredPart.get().withMaterial(id));
                pending.add(key);
            }
        }
        if (variants.isEmpty()) return;
        try {
            jei.getIngredientManager().addIngredientsAtRuntime(VanillaTypes.ITEM_STACK, variants);
            registered.addAll(pending);
            LOG.info("Registered {} material-dependent Hephaestus Tools item variants in JEI", variants.size());
        } catch (RuntimeException error) {
            LOG.warn("JEI part variants could not be registered: {}", error.getMessage());
        }
    }
}
""",encoding="utf-8")

# The material network payload is received on client only; trigger registration
# after its material map has replaced the stale client map.
p=base/"network/SyncMaterialsPayload.java"
s=p.read_text(encoding="utf-8")
old="ctx.enqueueWork(() -> MaterialManager.receiveSync(payload.materials()));"
assert old in s
s=s.replace(old,"""ctx.enqueueWork(() -> {
            MaterialManager.receiveSync(payload.materials());
            if (net.neoforged.fml.ModList.get().isLoaded("jei")) {
                com.titammods.hephaestus_tools.compat.jei.HephaestusToolsJeiPlugin.refreshVariants();
            }
        });""")
p.write_text(s,encoding="utf-8")

# Preserve every previous fix in beta4.
p=root/"gradle.properties"
s=p.read_text(encoding="utf-8")
s,n=re.subn(r"(?m)^mod_version=.*$","mod_version=1.0.11-unofficial-26.3-beta5",s)
assert n==1
p.write_text(s,encoding="utf-8")
print("BETA5_INTEGRATION: conditional Forge recipe mixin + JEI subtype/material variants + post-sync refresh configured.")
