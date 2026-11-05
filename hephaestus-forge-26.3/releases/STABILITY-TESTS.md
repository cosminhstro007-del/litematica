# Hephaestus Tools Beta6 + Forge Alpha3 — Minecraft 26.3 stability checks

Date: 2026-11-05. Environment: Minecraft 26.3, NeoForge 26.3.0.101, Java 25, JEI 31.17.0.108.

## Changes relative to earlier versions

- Forge Alpha3 fixed missing save/dirty notifications after direct legacy fluid insertion, extraction, rearrangement and capacity changes.
- Forge Alpha3 fixed repeated menu closure returning the same bucket twice (clears ephemeral menu slots before giving items back).
- Tools Beta6 fixed stale material-dependent JEI item variants surviving logout or datapack material changes; previous sync registration, Forge material casting mixin and passive auto-repair OFF by default remain.
- No upstream original author source repository was modified.
- Prior Forge Alpha2 and Tools Beta5 JARs remain available; new Alpha3 and Beta6 use separate GitHub branches.

## Automated tests: passed

**Forge Alpha3 and Tools Beta5:** https://github.com/cosminhstro007-del/litematica/actions/runs/42026822251
- 171 melting, 100 casting table, 11 casting basin recipe entries detected.
- Real redstone -> molten redstone via fuel-based Melter.
- Real molten iron -> iron ingot (table) and iron block (basin).
- Real Tools pick-head casting produced `hephaestus_tools:part_material = hephaestus_tools:iron`.
- Smeltery fluid API simulated operations left state unchanged, committed legacy insertions/drains marked owner dirty.
- Bucket-in to Smeltery => empty bucket + 1000 lava; bucket-out => lava bucket + 0 remaining; second menu close leaves no pending buckets.

**Exact Alpha3 + Beta6 + JEI combination:** https://github.com/cosminhstro007-del/litematica/actions/runs/42027453467
- Both mod IDs loaded along with JEI 31.17.0.108.
- All Forge machine, Tools material, legacy fluid and bucket assertions passed.

**Workbench Beta6 with Forge Alpha3:** https://github.com/cosminhstro007-del/litematica/actions/runs/42028010443
- Real Arsenal Table placed in dedicated test world.
- Iron-material pickaxe parts inserted.
- WorkbenchMenu reported correct preview and accepted assemble-button action.
- Output pickaxe contained initialized material construction data.
- Every ingredient was consumed once, output contained correct material list.
- Test code was only injected into ephemeral development sources after the releasable JAR was built.

## Not yet verified

- JEI recipe panels, links, search and render behavior in a *graphical client*.
- Every Smeltery multiblock dimension, pipe automation, UI mouse interaction and external materials combination.
- Full world shutdown/relaunch persistence (the dirty flag behavior was tested, not a full restart).
- Client render layers, animations, GUI effects and compatibility with broad modpacks.
- Minecraft RecipeManager's placement warnings for custom fluid recipes may remain; our tests verify those recipe types still execute in custom machines.

Use on a backed-up test world. Do not deploy to production as a 100%-verified bug-free modpack.

## Verified downloads

- [Hephaestus Tools Beta6](https://raw.githubusercontent.com/cosminhstro007-del/litematica/hephaestus-tools-26.3-beta6-stability/hephaestus-tools-26.3/releases/HephaestusTools-26.3-Beta6-Stability.jar)
- [Hephaestus Forge Alpha3](https://raw.githubusercontent.com/cosminhstro007-del/litematica/hephaestus-forge-26.3-alpha3-stability/hephaestus-forge-26.3/releases/HephaestusForge-26.3-Alpha3-Stability.jar)

Remember: replace prior Tools Beta5/Forge Alpha2, don't load duplicate JARs.
