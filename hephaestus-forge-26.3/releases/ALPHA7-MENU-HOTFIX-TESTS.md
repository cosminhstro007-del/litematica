# Hephaestus Forge Alpha7 – Smeltery item and lava bucket hotfix

**Tested:** 2026-11-05. **Minecraft:** 26.3, **NeoForge:** 26.3.0.101, **Java:** 25.
**Compatibility:** Hephaestus Tools Beta7, JEI 31.17.0.108.

Original author/source: **titammods**, MIT.
Unofficial 26.3 port: **CosminHstro & FL0X**.

## User-reported bugs

1. Shift-clicking an entire ore/resource stack into the Smeltery Controller removed it from player inventory without appearing in the GUI.
2. Inserting lava buckets via left-click or Shift-click consumed the bucket without the expected empty bucket output.
3. Non-meltable items could be sent into hidden machine slots and seem to vanish.

## Confirmed technical cause

The Minecraft 26.3 compatibility bridge for `SlotItemHandler` incorrectly
used `Slot.index` as the item handler index. After a Slot was added to
`AbstractContainerMenu`, Minecraft replaced `Slot.index` with its menu index.
Consequently, for example, `bucketHandler.getStackInSlot(1)` showed a bucket
but the corresponding menu Slot at index 33 incorrectly read slot 33 of a
2-slot bucket handler and returned empty.

The previous menu also appended a separate synthetic/invisible Slot for every
Smeltery inventory position. Large machines created thousands of hidden menu
slots and even more backing container references, which was expensive for
memory, packet synchronization and Shift-click targeting.

## Fixes

- Capture the original handler slot index in an immutable `realHandlerSlot`
  separate from Minecraft's `Slot.index`. Applied across legacy machine menus.
- Eliminate per-internal-slot invisible menu entries. Keep 32 virtual visible
  slots, two bucket input/output slots and 36 player slots: **70 fixed slots**
  for any Smeltery size.
- Route player Shift-click directly through the **real** item handler's
  `insertItem` remainders. Insert only items with an actual melting recipe;
  non-meltable items stay in player inventory. Partial transfers keep their
  source remainder instead of deleting it.
- Protect vanilla lava/water buckets with a full 1000 mB simulated transaction
  check before consuming the item; produce the matching empty/filled bucket.
  Full/incompatible tanks leave the bucket untouched. For modded containers,
  do not commit a transfer if no replacement container was produced.
- Move bucket output back to real player slots with exact quantities.
- Clamp menu scrolling to legal inventory rows.
- Keep existing optimized melting, idle packet suppression, recipe cache, NBT,
  Tools material integration, and previous performance hardening.

## Actual automated test results

**[Alpha7 Smeltery interaction suite — passed](https://github.com/cosminhstro007-del/litematica/actions/runs/42049609017)**

- 64 `minecraft:raw_iron` shift-clicked from player inventory were all preserved
  in controller slots, with no extra items.
- If controller has space for only 10 items, 10 transferred and 54 remained in
  the player's inventory.
- `minecraft:iron_ore` blocks (not part of the upstream melting recipes) and
  ordinary unrelated items were rejected and retained, rather than swallowed.
- A 2,048-slot Smeltery produced exactly 70 menu slots.
- Lava bucket Shift-click into tank already containing lava added 1000 mB
  and yielded a normal empty bucket in output, which could be Shift-clicked
  back to the player.
- Empty bucket Shift-click into 2000 mB lava created one lava bucket and
  extracted exactly 1000 mB.
- Full 8000 mB tank refused a lava bucket without consuming the player's item.
- Manually inserting the lava bucket converted it correctly, and closing the
  menu twice did not duplicate the output.
- Earlier Forge machine melting, casting, tank rollback, NBT and Tools material
  interoperability regression checks passed.

**[Two real world boots — passed](https://github.com/cosminhstro007-del/litematica/actions/runs/42049619079)**

- Wrote actual loaded block entities, stopped the dedicated server, reloaded
  the same world; verified Smeltery, casting table, fuel tank, and Tools part
  material identity were correctly persisted.

## Release

[Hephaestus Forge Alpha7 Menu Hotfix JAR](https://raw.githubusercontent.com/cosminhstro007-del/litematica/hephaestus-forge-26.3-alpha7-menu-hotfix/hephaestus-forge-26.3/releases/HephaestusForge-26.3-Alpha7-MenuHotfix.jar)

[Hephaestus Tools Beta7 JAR (unchanged)](https://raw.githubusercontent.com/cosminhstro007-del/litematica/hephaestus-tools-26.3-beta7-hardening/hephaestus-tools-26.3/releases/HephaestusTools-26.3-Beta7-Hardening.jar)

**Installation:** Remove prior Forge Alpha6 JAR. Keep only one Forge JAR and
one Tools JAR on both client and server. Back up your world before testing.

**Limitations:** Automated tests exercise the server-side actual menu logic;
a physical graphical client / mouse click test remains necessary. Nonvanilla
fluid containers need additional compatibility testing. Do not claim this
entire modpack is 100% bug-free.
