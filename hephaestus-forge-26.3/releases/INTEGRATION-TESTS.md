# Hephaestus Forge + Tools + JEI — NeoForge 26.3

**Validated on 2026-11-05 (automated dedicated server, Java 25).**

## Versions

| Mod | Version |
|---|---|
| Minecraft | 26.3 |
| NeoForge | 26.3.0.101 |
| Hephaestus Tools | 1.0.11-unofficial-26.3-beta5 |
| Hephaestus Forge | 1.0.20-unofficial-26.3-alpha2 |
| JEI | 31.17.0.108 |

## Automated test results

GitHub Actions:
https://github.com/cosminhstro007-del/litematica/actions/runs/42018402457

1. Compiled both source ports against Minecraft 26.3.
2. Launched dedicated server with both Mods and JEI.
3. Verified Forge recipe map: 171 melting, 100 casting table, 11 casting basin.
4. Verified actual molten iron -> ingot (Casting Table).
5. Verified actual molten iron -> iron block (Casting Basin).
6. Verified actual redstone + lava -> molten redstone (Melter).
7. **Verified actual Tools pick head cast from molten iron has `hephaestus_tools:part_material` equal to `hephaestus_tools:iron`**. This failed in Tools Beta4/Forge Alpha1.
8. Confirmed Forge JEI plugin has six recipe categories; Tools JEI plugin has subtype interpreter for material-dependent parts.

**This confirms server integration and item-component correctness, NOT fully rendered client JEI pages.**

## Changes

- Tools Beta5: conditional Forge recipe return-value mixin attaches the ToolPart material
  from molten fluid; JEI gets material variants after recipe/material sync; Beta4
  passive repair remains **disabled by default**.
- Forge Alpha2: client JEI refreshes custom recipe lists when the server sends
  a new recipe map, even when JEI initialized first.
- Original upstream mods are credited to **titammods**, distributed under their license.
  Unofficial 26.3 adaptation credited to **CosminHstro & FL0X**.

## Installation

1. Stop the game/server and back up your test world.
2. Remove older Beta4/Alpha1 copies. Keep **one** Tools JAR and **one** Forge JAR.
3. Install **Tools Beta5 and Forge Alpha2 together** on both client and server.
4. Use Java 25 and NeoForge 26.3.0.101.
5. Install a matching 26.3 Player Animation Library and the required Athena client dependency.
6. Install JEI 31.17.0.108 on client if you want recipe browsing.

## Not yet proven

- Actual JEI **client screens**, search, click navigation, and visual recipes.
- Connected textures, material rendering, and animations of every item in a graphical client.
- Every multiblock configuration, fuel type, tank/pipe automation and bucket interaction.
- Every third-party material mod or all generated optional recipes.
- All 291 generic Minecraft RecipeManager placement warnings remain.
  The tested custom machine recipes are still found and executed. These warnings
  must not be treated as proof of a casting failure.

Do not claim this port is 100% bug-free. Continue using a **separate test world**
until manual client tests pass.

## Direct JARs

- Tools Beta5: https://raw.githubusercontent.com/cosminhstro007-del/litematica/hephaestus-tools-26.3-beta5-integration/hephaestus-tools-26.3/releases/HephaestusTools-26.3-Beta5-Integration.jar
- Forge Alpha2: https://raw.githubusercontent.com/cosminhstro007-del/litematica/hephaestus-forge-26.3-alpha2-integration/hephaestus-forge-26.3/releases/HephaestusForge-26.3-Alpha2-Integration.jar

Development branches preserve the prior builds and original test artifacts.
