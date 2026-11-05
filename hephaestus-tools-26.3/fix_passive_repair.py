#!/usr/bin/env python3
"""Disable unintended passive auto-repair by default on Minecraft 26.3.
The original Cultivated trait repairs 1 damage every 40 ticks even while idle.
Preserve a server-authoritative gameplay config to enable the original behavior.
Unofficial beta4 fix; original authors titammods (MIT).
"""
from pathlib import Path
import re,sys

root=Path(sys.argv[1]).resolve()
base=root/"src/main/java/com/titammods/hephaestus_tools"
cfg=base/"config/HephaestusGameplayConfig.java"
cfg.parent.mkdir(parents=True,exist_ok=True)
cfg.write_text("""package com.titammods.hephaestus_tools.config;

import net.neoforged.neoforge.common.ModConfigSpec;

/** Shared server gameplay configuration. Passive durability repair defaults OFF. */
public final class HephaestusGameplayConfig {
    public static final String FILE_NAME = "hephaestus-tools-gameplay.toml";
    public static final ModConfigSpec SPEC;
    public static final ModConfigSpec.BooleanValue PASSIVE_REPAIR;

    static {
        ModConfigSpec.Builder builder = new ModConfigSpec.Builder();
        builder.comment("Hephaestus Tools gameplay rules (server controlled).").push("durability");
        PASSIVE_REPAIR = builder.comment(
                "Allow passive self-repair from the Cultivated trait.",
                "Defaults to false: all tools keep normal vanilla-like wear.",
                "Set true only if you want the original automatic restoration effect.")
                .define("enable_passive_repair", false);
        builder.pop();
        SPEC = builder.build();
    }

    private HephaestusGameplayConfig() {}

    public static boolean passiveRepairEnabled() {
        try {
            return PASSIVE_REPAIR.get();
        } catch (IllegalStateException e) {
            // Safe default until the server has loaded its config.
            return false;
        }
    }
}
""",encoding="utf-8")

j=base/"HephaestusTools.java"
s=j.read_text(encoding="utf-8")
anchor="        container.registerConfig(ModConfig.Type.CLIENT, HephaestusConfig.SPEC, HephaestusConfig.FILE_NAME);"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"""
        container.registerConfig(ModConfig.Type.COMMON,
                com.titammods.hephaestus_tools.config.HephaestusGameplayConfig.SPEC,
                com.titammods.hephaestus_tools.config.HephaestusGameplayConfig.FILE_NAME);""")
j.write_text(s,encoding="utf-8")

j=base/"effect/types/RepairEffect.java"
s=j.read_text(encoding="utf-8")
anchor="""    public void inventoryTick(EffectContext context, int level) {
        ItemStack tool = context.tool();"""
assert s.count(anchor)==1
s=s.replace(anchor,"""    public void inventoryTick(EffectContext context, int level) {
        // Cultivated is opt-in on 26.3: prevent universal +1 auto-repair while idle.
        if (!com.titammods.hephaestus_tools.config.HephaestusGameplayConfig.passiveRepairEnabled()) return;
        ItemStack tool = context.tool();""")
j.write_text(s,encoding="utf-8")

j=root/"gradle.properties"
s=j.read_text(encoding="utf-8")
s,n=re.subn(r"(?m)^mod_version=.*$","mod_version=1.0.11-unofficial-26.3-beta4",s)
assert n==1
j.write_text(s,encoding="utf-8")
print("Beta4: automatic Cultivated tool repair disabled by default, opt-in via COMMON config.")
