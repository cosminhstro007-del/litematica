# Hephaestus Forge Alpha6 – performance hardening report
**Checked:** November 5, 2026  
**Runtime:** Minecraft 26.3 / NeoForge 26.3.0.101 / Java 25  
**Other mods in automated server tests:** Hephaestus Tools Beta7, JEI 31.17.0.108

## New optimization

Built from titammods' original Forge 1.0.20 code, preserving attribution and original feature set.

1. **Stop redundant idle broadcasts:** An empty/unformed Smeltery no longer sends a full block entity update every second without a change. Burning Smelteries continue their 1-second client fuel synchronization; real fuel-type changes still broadcast.
2. **Stop unnecessarily marking idle chunks dirty:** Unformed Smelteries clear currentFuel/fuelCapacity only when their values actually change, instead of calling `setChanged()` unconditionally once per second.
3. **Distribute multiblock scans across server ticks:** Check cadence remains once every 20 ticks, but controllers derive different start phases from their block positions. This reduces correlated 1-second spikes without changing total scan frequency.
4. **Avoid repeatedly notifying unchanged IO blocks:** Multiblock links are refreshed immediately when topology changes; a fallback reconciliation still runs every 10 scan cycles (10 seconds) to discover blocks replaced in-place. Rendering liquid type changes are still propagated on change.
5. **Skip alloy recipe evaluation for empty molten-fluid inventories.**
6. **Sparse melting processing:** A `BitSet` indexes active melting input slots. Full recipe-status scans run every 5 ticks (or earlier after an inventory/temperature change), while successful melting progress still advances *every game tick*. Recomputed cache after resizing or loading the inventory; recipe lookup cache itself is unchanged.

## Observed behavior (automated server tests, NOT claimed TPS uplift)

[Full gameplay and performance regression, including release build](https://github.com/cosminhstro007-del/litematica/actions/runs/42039557328)

- **100 idle controllers × 40 manual tick invocations:** **0 redundant periodic full-block-entity packet sends** recorded in instrumented code path. Manual workload took approximately **5.23 ms total** in that CI execution; it is not a comparison against an unpatched baseline.
- **2,048 empty Smeltery input slots × 50 ticks:** **10 complete recipe scans** instead of the unoptimized per-tick 50 scans; ~80% fewer complete refreshes in this example.
- **2,048 slots including a real melting recipe × 12 active ticks:** **12 ticks of progress** advanced, with **3 complete recipe scans**. No intentional speed reduction in melting progression.
- Legacy liquid simulation/commit/rollback, external tank-to-tank transfer conservation, bucket IO, controller and tank NBT roundtrip, casting table and basin outputs, Tools iron-part material component and dedicated server startup all passed.
- Developer-only counters and performance fixtures were injected **after the releasable JAR was built**. They are not included in the published JAR.

[Real two-boot world restart with Alpha6 + Tools Beta7](https://github.com/cosminhstro007-del/litematica/actions/runs/42039628779)

- Start server, populate and save actual world data, shut down, restart same saved world.
- Recovered Forge fuel tank (lava), casting table (mold and molten iron), Smeltery Controller (inventory, molten fluid, progress), Tools pick head with persisted iron material component.
- Both runs loaded Alpha6 and Beta7, with no fatal server crashes in this regression.

## Release files

- Forge Alpha6: https://raw.githubusercontent.com/cosminhstro007-del/litematica/hephaestus-forge-26.3-alpha6-optimized/hephaestus-forge-26.3/releases/HephaestusForge-26.3-Alpha6-Optimized.jar
- Tools Beta7 (unchanged): https://raw.githubusercontent.com/cosminhstro007-del/litematica/hephaestus-tools-26.3-beta7-hardening/hephaestus-tools-26.3/releases/HephaestusTools-26.3-Beta7-Hardening.jar
- Conservative fallback Forge Alpha5 (without the 5-tick indexed melting change): https://raw.githubusercontent.com/cosminhstro007-del/litematica/hephaestus-forge-26.3-alpha5-performance/hephaestus-forge-26.3/releases/HephaestusForge-26.3-Alpha5-Performance.jar
- Original original author/source attribution: **titammods**, MIT license.
- NeoForge 26.3 port contribution attribution: **CosminHstro & FL0X**.

## Remaining bottlenecks and limits

- **Unmeasured TPS with a 200+ modpack and multiple simultaneous real players**. Cannot claim a numeric TPS gain or guaranteed 20 TPS from this synthetic test.
- Full multiblock geometry validation still runs once per second and its cost scales with multiblock size; scans are staggered, not eliminated.
- Large Smeltery GUIs currently construct a slot for every internal inventory slot as well as visible slots. At maximum 15×15×63 internal volume this can produce a very large container state / initial menu synchronization and needs future optimization and dedicated client testing. Do **not** remove offscreen slots without preserving scroll and shift-click behavior.
- Full graphical JEI and Forge UI rendering require client/GPU testing. Earlier CI client boot could not initialize GLX or Vulkan, so a graphical client was not validated.
- The client may experience the deliberate **up to 5-tick (250 ms at 20 TPS)** re-evaluation delay for a melting slot blocked by changed fluid capacity when inventory/temperature did not change; actual melting progress continues every tick once valid. This should be checked manually in an automation-heavy world.
- Large machine stress testing over a prolonged real server session and profiling with spark remain necessary.

**Conclusion:** Alpha6 is an experimental optimized test build, not a guarantee of lag-free public-server performance. Use only in a backed-up test world until client and realistic load testing pass.
