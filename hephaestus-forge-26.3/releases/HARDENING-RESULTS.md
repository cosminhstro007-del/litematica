# Hephaestus Forge Alpha4 + Hephaestus Tools Beta7 — hardening results

**Date:** 5 November 2026  
**Status:** experimental, verified in several automated dedicated-server suites.
**Original authors:** titammods (upstream projects, MIT; original author credit retained).  
**Unofficial 26.3 port contributions:** CosminHstro & FL0X.

## Supported test environment

| Software | Tested version |
|---|---|
| Minecraft | 26.3 |
| NeoForge | 26.3.0.101 |
| Java | 25 |
| Hephaestus Forge | 1.0.20-unofficial-26.3-alpha4 |
| Hephaestus Tools | 1.0.11-unofficial-26.3-beta7 |
| JEI | 31.17.0.108 |

**Do not install both old and new copies of either mod.** Replace Alpha3 with
Alpha4 and Beta6 with Beta7 for testing. Keep a world backup.

## Files

- [Forge Alpha4 JAR](https://raw.githubusercontent.com/cosminhstro007-del/litematica/hephaestus-forge-26.3-alpha4-hardening/hephaestus-forge-26.3/releases/HephaestusForge-26.3-Alpha4-Hardening.jar)
- [Tools Beta7 JAR](https://raw.githubusercontent.com/cosminhstro007-del/litematica/hephaestus-tools-26.3-beta7-hardening/hephaestus-tools-26.3/releases/HephaestusTools-26.3-Beta7-Hardening.jar)

## Fixes

### Forge Alpha4
- A saved block-entity inventory can be loaded over an existing in-memory
  inventory without spawning unwanted drops (data reload must not be confused
  with physically shrinking the Smeltery).
- Actual structure-resize overflow drops are retained server-side, not client-side.
- Malformed saved `slot_count` and `progress_count` are bounded by a
  Smeltery's maximum possible internal volume (15×15×63 slots).
- Preserves Alpha3 dirty/save notifications on fluid transfers and idempotent
  return of temporary bucket items.
- Preserves Alpha2 JEI client recipe refresh.

### Tools Beta7
- If a saved Workbench inventory omits Upgrade, Blueprint, Inputs or Output
  keys, the corresponding old in-memory slots are cleared rather than retained.
- Preserves Beta6 JEI material-variant reconciliation and clearing on logout.
- Preserves Beta5 Forge cast material identity and Beta4 passive durability
  regeneration disabled by default.

## Verified automated tests

1. **Exact Alpha4 + Beta7 + JEI shared dedicated server**:
   [GitHub Actions run](https://github.com/cosminhstro007-del/litematica/actions/runs/42034114319).
   Loaded all three; identified 171 melting, 100 table, 11 basin recipes.
   Completed molten iron -> ingot/block and redstone melting. Created a
   `hephaestus_tools:pick_head` by Forge casting that carried
   `hephaestus_tools:iron` as its part material. No fatal loading errors.

2. **Legacy and external fluid transaction integrity**:
   same run: simulated transfers made no change; aborted fluid extraction,
   insertion and tank-to-tank transfer rolled back entirely; committed transfer
   moved only the requested fluid. Seared Tank / Smeltery bucket fill and empty
   worked with no repeat-drop on menu close.

3. **NBT read/write regression**:
   same run: inventory, Smeltery melting progress, fuel and molten fluid
   round-tripped. Fuel Tank preserved 1,500 mB lava. Loading NBT onto a
   pre-existing inventory did not eject stale items into the world.

4. **Actual world disk save, shutdown and server restart**:
   [GitHub Actions run](https://github.com/cosminhstro007-del/litematica/actions/runs/42034745638).
   A test world was populated, fully saved, the dedicated server shut down,
   then the same world re-opened in a second server boot. Recovered Seared Fuel
   Tank (1,400 mB lava), Casting Table (ingot cast and 90 mB molten iron),
   Smeltery Controller (iron ore, 700 mB molten iron, saved melting progress),
   and Tools Workbench with a pick head retaining **iron material data**.

5. **Actual Workbench assembly and two-player duplicate prevention**:
   [GitHub Actions run](https://github.com/cosminhstro007-del/litematica/actions/runs/42033383560).
   GUI menu logic produced a pickaxe and consumed its input parts. Two distinct
   fake players attempted to craft using the same Workbench during the same
   server tick: only one result was produced. Repeated shift-click of the output
   did not create additional tools. Missing NBT slots were cleared.

6. **Bulk inputs**:
   [GitHub Actions run](https://github.com/cosminhstro007-del/litematica/actions/runs/42034270515).
   A 3,500-count Workbench input stack survived NBT save/load without loss.
   Not a stress test of many simultaneous Workbenches.

## Not yet proven / important limitations

- JEI client GUI: search, recipe pages, client-side material variant display and
  resource reload have not been visually verified. The CI client attempt
  couldn't initialize OpenGL/GLX or Vulkan in its headless GPU environment;
  dedicated server JEI loading alone does not exercise rendered JEI screens.
- All Workbench mouse drag-and-drop gestures, crafting designs, and every tool
  and modifier have not been exhaustively tested with real clients.
- Every Smeltery multiblock geometry, every automated third-party fluid pipe,
  and all recipe/material combinations are not covered.
- The vanilla RecipeManager may warn that custom fluid recipes have empty
  recipe-book placements. This did **not** prevent the tested Hephaestus machine
  recipes from executing, but a complete warning-free port is not established.
- Server load with 15–20 simultaneous real players and complex modpacks has
  not been benchmarked or verified.

**Conclusion:** This pair is suitable for controlled testing with a backup.
The specific automated regressions above passed; no claim of total
bug-freedom or production stability is made.
