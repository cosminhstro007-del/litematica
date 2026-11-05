# Hephaestus Forge – unofficial Minecraft 26.3 NeoForge port

Status: **Alpha 1 / experimental**. Compiles and starts a NeoForge 26.3.0.101
dedicated development server alongside **Hephaestus Tools Beta 4**.

## Tested (2026-11-05)
- Original upstream: titammods/hephaestusforge, branch `26.1/main`,
  source commit `483807dfda3da0c188a50a28de783a40d5e28274`,
  version 1.0.20. Upstream remains copyright titammodswa, MIT license.
- Java 25 / Minecraft 26.3 / NeoForge 26.3.0.101.
- Gradle build successful.
- Combined server smoke test with
  `HephaestusTools-26.3-Beta4-NoAutoRepair.jar`:
  both `hephaestus` and `hephaestus_tools` loaded,
  server reached **Done (2.790s)!**, with no error-level log entries.
  Workflow: https://github.com/cosminhstro007-del/litematica/actions/runs/42010654768
- The Tools 26.3 progress was separately saved on branch
  `hephaestus-tools-26.3-beta4-snapshot`; no Tools source changed.

## Additional in-world verification (2026-11-05)

The validation run https://github.com/cosminhstro007-del/litematica/actions/runs/42014697711
recompiled the unmodified release source and injected a **development-only**
test hook *after* generating the publishable JAR. The published binary stayed
unchanged (1,794,514 bytes).

Tested on NeoForge 26.3.0.101 with Hephaestus Tools Beta4 installed:
- Recipe registry contained 171 melting, 100 casting table, and 11 casting basin recipes.
- HephaestusRecipeCache found the vanilla iron-pickaxe melting recipe,
  iron-ingot cast recipe, and iron-block basin recipe.
- Casting Table in the server world accepted molten iron and yielded iron ingot.
- Casting Basin accepted molten iron and yielded iron block.
- Seared Melter above a fuel tank consumed redstone with lava fuel and
  produced molten redstone.
- The test finished with `HEPHAESTUS_VERIFY_SUCCESS recipes, table, basin, melter`.
- The server reached `Done (3.100s)!` with no ERROR-level log entries.

**Nuance:** The server still logs 291 vanilla RecipeManager warnings
about empty placement ingredients across Forge and Tools recipe types.
The tests proved Forge's relevant recipes remain discoverable through
its recipe registry and executable by the custom machines. These warnings
are not, by themselves, proof that Forge crafting is broken; they do not
mean all recipes or UI integrations have been manually verified.

## Current port adaptations
- 26.3 API update for blocks, new SDL3 keyboard, renderer, inventory slots.
- Inventory/fluid legacy internal bridges under `com.titammods.compat.port.legacy`
  retain local machine behavior; new ResourceHandler capabilities remain available.
- Fluid-bucket slots now use modern transaction-based transfers.
- Converted advancement recipe conditions (`recipe` -> `recipes`),
  defined optional shared c:gears/c:plates item tags.
- The original `hephaestus` mod ID, textures and generated data were preserved.

## Known limitations
- This is **not yet a fully verified gameplay port**:
  multiblock construction, smelting, casting, tanks, buckets, pipes, GUI,
  client-side renders, every recipe, and both-mod recipe integration
  still require **interactive testing** in Minecraft.
- Hephaestus Tools Beta 4 still has its prior Forge-specific casting/JEI
  compatibility disabled; loading both mods proves coexistence, **not**
  that every Tools part automatically casts in the Forge.
- Client graphics cannot be tested on the runner because it lacks a
  working OpenGL/Vulkan GPU.
- Optional ATO integration remains absent for 26.3.
- Use **Athena 4.7.4 for Minecraft 26.3 NeoForge on client**, as well as
  Player Animation Library for the Tools mod.
- Back up worlds and avoid production installations until manual testing.

## Rebuild
Branch `hephaestus-forge-26.3-port` stores all patch scripts:
`port_forge.py`, `legacy_bridge.py`, `fix_26_3_apis.py`,
`fix_generated_data.py`, and the
`.github/workflows/hephaestus-forge-26-3-port.yml` build workflow.
Build runner clones original upstream, applies patches, compiles,
then publishes the JAR to this releases folder.

JAR: `HephaestusForge-26.3-Alpha1-Experimental.jar`.
