#!/usr/bin/env python3
"""Unofficial Hephaestus Forge port scaffold for Minecraft 26.3 NeoForge.
Port upstream 26.1.2 v1.0.20 without editing original source repository.
Preserve namespace 'hephaestus' for Hephaestus Tools interoperability.
MIT license/copyright remains the original author's (titammodswa).
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
def patch(path,changes):
    p=root/path
    s=p.read_text(encoding="utf-8")
    for old,new in changes:
        if old not in s: raise RuntimeError(f"{path}: missing {old!r}")
        s=s.replace(old,new)
    p.write_text(s,encoding="utf-8")

patch("gradle.properties",[
("mod_version=1.0.20","mod_version=1.0.20-unofficial-26.3-alpha1"),
("minecraft_version=26.1.2","minecraft_version=26.3"),
("minecraft_version_range=[26.1.1,26.1.2]","minecraft_version_range=[26.3]"),
("neoforge_version=26.1.2.41-beta","neoforge_version=26.3.0.101"),
("jei_version=29.5.0.26","jei_version=31.17.0.108"),
("athena_version=4.7.3","athena_version=4.7.4"),
("jade_version=26.1.10","jade_version=26.3.5")
])
patch("build.gradle",[
("net.neoforged.moddev' version '2.0.141'","net.neoforged.moddev' version '2.0.148'"),
("jei-26.1.2-neoforge","jei-26.3-neoforge"),
("curse.maven:athena-841890:7970442","curse.maven:athena-841890:9385205"),
("curse.maven:jade-324717:8651070","curse.maven:jade-324717:9042207"),
('    implementation "curse.maven:ato-405593:8023670"',"    // ATO 26.1.2 only; keep data-driven compatibility, no mandatory compile dependency.")
])

toml=root/"src/main/resources/META-INF/neoforge.mods.toml"
s=toml.read_text(encoding="utf-8")
s=s.replace('license="All rights reserved"', 'license="MIT"')
s=s.replace('A multi-block forge mod inspired by classic mechanics.', 'Unofficial 26.3 port of titammods Hephaestus Forge; multiblock smeltery/casting.')
s=s.replace('versionRange="[4.0.0,)"','versionRange="[4.7.4,)"')
s=s.replace('versionRange="['+'$'+'{minecraft_version},)"','versionRange="[26.3]"')
toml.write_text(s,encoding="utf-8")

print("Port scaffold: Hephaestus Forge 1.0.20 -> Minecraft 26.3 / NeoForge 26.3.0.101")
print("Dependencies: JEI 31.17.0.108, Athena 4.7.4, Jade 26.3.5; optional ATO disabled")
