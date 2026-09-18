from pathlib import Path
import shutil

CORE = Path("core-src")
PL = Path("portinglib-src")

def copy_porting(rel: str):
    src = PL / rel
    parts = src.parts
    pkg_rel = Path(*parts[parts.index("java") + 1:])
    dst = CORE / "src/main/java" / pkg_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst

for rel in [
    "modules/transfer/src/main/java/io/github/fabricators_of_create/porting_lib/transfer/item/SlottedStackStorage.java",
    "modules/transfer/src/main/java/io/github/fabricators_of_create/porting_lib/transfer/item/ItemStackHandler.java",
    "modules/transfer/src/main/java/io/github/fabricators_of_create/porting_lib/transfer/item/ItemStackHandlerSlot.java",
    "modules/transfer/src/main/java/io/github/fabricators_of_create/porting_lib/transfer/callbacks/TransactionCallback.java",
    "modules/transfer/src/main/java/io/github/fabricators_of_create/porting_lib/transfer/callbacks/TransactionSuccessCallback.java",
    "modules/transfer/src/main/java/io/github/fabricators_of_create/porting_lib/transfer/callbacks/TransactionFailCallback.java",
]:
    copy_porting(rel)

# Keep the old Porting Lib item handler API because Sophisticated Core subclasses its internals.
ih = CORE / "src/main/java/io/github/fabricators_of_create/porting_lib/transfer/item/ItemStackHandler.java"
s = ih.read_text()
for imp in [
    "import io.github.fabricators_of_create.porting_lib.core.util.INBTSerializable;\n",
    "import io.github.fabricators_of_create.porting_lib.util.DualSortedSetIterator;\n",
    "import io.github.fabricators_of_create.porting_lib.util.EmptySortedSet;\n",
    "import io.github.fabricators_of_create.porting_lib.util.ItemStackUtil;\n",
]:
    s = s.replace(imp, "")
s = s.replace(
    " implements SlottedStackStorage, INBTSerializable<CompoundTag>",
    " implements SlottedStackStorage",
)
s = s.replace(
    "this(ItemStackUtil.createEmptyStackArray(stacks));",
    "this(java.util.stream.IntStream.range(0, stacks).mapToObj(i -> ItemStack.EMPTY).toArray(ItemStack[]::new));",
)
s = s.replace(
    "return lookup.containsKey(item) ? lookup.get(item) : EmptySortedSet.cast();",
    "return lookup.containsKey(item) ? lookup.get(item) : java.util.Collections.emptySortedSet();",
)

old_insert = "\n".join([
    "\tprivate Iterator<ItemStackHandlerSlot> getInsertableSlotsFor(ItemVariant variant) {",
    "\t\tSortedSet<ItemStackHandlerSlot> slots = getSlotsContaining(variant.getItem());",
    "\t\tSortedSet<ItemStackHandlerSlot> emptySlots = getSlotsContaining(Items.AIR);",
    "\t\tif (slots.isEmpty()) {",
    "\t\t\treturn emptySlots.isEmpty() ? Collections.emptyIterator() : emptySlots.iterator();",
    "\t\t} else {",
    "\t\t\treturn emptySlots.isEmpty() ? slots.iterator() : new DualSortedSetIterator<>(slots, emptySlots);",
    "\t\t}",
    "\t}",
])
new_insert = "\n".join([
    "\tprivate Iterator<ItemStackHandlerSlot> getInsertableSlotsFor(ItemVariant variant) {",
    "\t\tjava.util.ArrayList<ItemStackHandlerSlot> combined = new java.util.ArrayList<>();",
    "\t\tcombined.addAll(getSlotsContaining(variant.getItem()));",
    "\t\tcombined.addAll(getSlotsContaining(Items.AIR));",
    "\t\tcombined.sort(java.util.Comparator.comparingInt(ItemStackHandlerSlot::getIndex));",
    "\t\treturn combined.iterator();",
    "\t}",
])
s = s.replace(old_insert, new_insert)
s = s.replace("\n\t@Override\n\tpublic CompoundTag serializeNBT", "\n\tpublic CompoundTag serializeNBT")
s = s.replace("\n\t@Override\n\tpublic void deserializeNBT", "\n\tpublic void deserializeNBT")
ih.write_text(s)

slot = CORE / "src/main/java/io/github/fabricators_of_create/porting_lib/transfer/item/ItemStackHandlerSlot.java"
s = slot.read_text()
s = s.replace("import io.github.fabricators_of_create.porting_lib.core.PortingLib;\n", "")
s = s.replace("this.lastStack = PortingLib.DEBUG ? stack : stack.copy();", "this.lastStack = stack.copy();")
slot.write_text(s)

# Do not replace the Porting Lib ItemStackHandler with the simpler SFL handler.
for jf in (CORE / "src/main/java").rglob("*.java"):
    txt = jf.read_text(errors="ignore")
    txt2 = txt.replace(
        "com.github.salandora.sophisticatedfabriclib.transfer.api.v1.ItemStackHandler",
        "io.github.fabricators_of_create.porting_lib.transfer.item.ItemStackHandler",
    )
    if txt2 != txt:
        jf.write_text(txt2)

# Fabric 26.x: InventoryStorage -> ContainerStorage.
iw = CORE / "src/main/java/net/p3pp3rf1y/sophisticatedcore/inventory/InventoryStorageWrapper.java"
if iw.exists():
    s = iw.read_text()
    s = s.replace(
        "net.fabricmc.fabric.api.transfer.v1.item.InventoryStorage",
        "net.fabricmc.fabric.api.transfer.v1.item.ContainerStorage",
    )
    s = s.replace("InventoryStorage", "ContainerStorage")
    iw.write_text(s)

# Fabric 26.x no longer exposes InventoryStorageImpl.parts. Keep an explicit public slot view.
tp = CORE / "src/main/java/net/p3pp3rf1y/sophisticatedcore/network/TransferItemsPayload.java"
if tp.exists():
    s = tp.read_text()
    s = s.replace(
        "import net.fabricmc.fabric.api.transfer.v1.item.InventoryStorage;\n",
        "import net.fabricmc.fabric.api.transfer.v1.item.ContainerStorage;\n",
    )
    s = s.replace("import net.fabricmc.fabric.impl.transfer.item.InventoryStorageImpl;\n", "")
    s = s.replace("super(inv, 0, inv.items.size());", "super(inv, 0, 36);")

    start = s.find("\tprivate static class RangedWrapper implements IItemHandlerSimpleInserter {")
    end = s.rfind("\n\t}\n}")
    if start != -1 and end != -1 and end > start:
        replacement = """\tprivate static class RangedWrapper implements IItemHandlerSimpleInserter {
\t\tprivate final List<SingleSlotStorage<ItemVariant>> slots;

\t\tpublic RangedWrapper(Inventory inv, int start, int end) {
\t\t\tList<SingleSlotStorage<ItemVariant>> all = ContainerStorage.of(inv, null).getSlots();
\t\t\tthis.slots = List.copyOf(all.subList(Math.min(start, all.size()), Math.min(end, all.size())));
\t\t}

\t\t@Override
\t\tpublic int getSlotCount() {
\t\t\treturn slots.size();
\t\t}

\t\t@Override
\t\tpublic SingleSlotStorage<ItemVariant> getSlot(int slot) {
\t\t\treturn slots.get(slot);
\t\t}

\t\t@Override
\t\tpublic List<SingleSlotStorage<ItemVariant>> getSlots() {
\t\t\treturn slots;
\t\t}

\t\t@Override
\t\tpublic ItemStack getStackInSlot(int slot) {
\t\t\tvar view = getSlot(slot);
\t\t\treturn view.getResource().toStack((int) view.getAmount());
\t\t}

\t\t@Override
\t\tpublic void setStackInSlot(int slot, ItemStack stack) {
\t\t\t// This wrapper is only used by transfer operations.
\t\t}

\t\t@Override
\t\tpublic int getSlotLimit(int slot) {
\t\t\treturn (int) getSlot(slot).getCapacity();
\t\t}

\t\t@Override
\t\tpublic long insert(ItemVariant resource, long maxAmount, TransactionContext transaction) {
\t\t\tlong inserted = 0;
\t\t\tfor (SingleSlotStorage<ItemVariant> slot : slots) {
\t\t\t\tinserted += slot.insert(resource, maxAmount - inserted, transaction);
\t\t\t\tif (inserted >= maxAmount) break;
\t\t\t}
\t\t\treturn inserted;
\t\t}

\t\t@Override
\t\tpublic long extract(ItemVariant resource, long maxAmount, TransactionContext transaction) {
\t\t\tlong extracted = 0;
\t\t\tfor (SingleSlotStorage<ItemVariant> slot : slots) {
\t\t\t\textracted += slot.extract(resource, maxAmount - extracted, transaction);
\t\t\t\tif (extracted >= maxAmount) break;
\t\t\t}
\t\t\treturn extracted;
\t\t}
\t}"""
        s = s[:start] + replacement + s[end + len("\n\t}"):]
    tp.write_text(s)

print("Applied Fabric 26.x inventory compatibility layer.")


# Minecraft 26.x common API migration: NBT accessors now return Optional and several Level/Recipe APIs changed.
import re

java_root = CORE / "src/main/java"

# Keep these transformations deliberately limited to source files that participate in the common/runtime pass.
for jf in java_root.rglob("*.java"):
    txt = jf.read_text(errors="ignore")
    new = txt

    # Level accessors became methods in 26.x.
    new = re.sub(r"\.isClientSide\b(?!\s*\()", ".isClientSide()", new)

    # CompoundTag typed getters became Optional-returning accessors in 26.x.
    new = re.sub(r'\.contains\(([^,\n]+),\s*Tag\.TAG_[A-Z_]+\)', r'.contains(\1)', new)
    new = re.sub(r'\.getList\(([^,\n]+),\s*Tag\.TAG_[A-Z_]+\)', r'.getList(\1).orElseGet(ListTag::new)', new)

    # Add defaults only when the call isn't already followed by Optional handling.
    new = re.sub(r'(\.getInt\([^()\n]*\))(?!\s*\.)', r'\1.orElse(0)', new)
    new = re.sub(r'(\.getLong\([^()\n]*\))(?!\s*\.)', r'\1.orElse(0L)', new)
    new = re.sub(r'(\.getBoolean\([^()\n]*\))(?!\s*\.)', r'\1.orElse(false)', new)
    new = re.sub(r'(\.getString\([^()\n]*\))(?!\s*\.)', r'\1.orElse("")', new)
    new = re.sub(r'(\.getCompound\([^()\n]*\))(?!\s*\.)', r'\1.orElseGet(CompoundTag::new)', new)

    # Recipe#assemble no longer takes RegistryAccess in 26.x.
    new = new.replace(
        "assemble(craftingInventory.asCraftInput(), w.registryAccess())",
        "assemble(craftingInventory.asCraftInput())",
    )
    new = new.replace(
        "assemble(craftingInventory.asCraftInput(), level.registryAccess())",
        "assemble(craftingInventory.asCraftInput())",
    )

    # LivingEntity#drop gained Prediction.
    new = re.sub(
        r'player\.drop\(([^,\n]+),\s*(true|false)\)',
        r'player.drop(\1, \2, net.minecraft.world.entity.Prediction.SERVER_ONLY)',
        new,
    )
    new = re.sub(
        r'player\.drop\(([^,\n]+),\s*(true|false),\s*(true|false)\)',
        r'player.drop(\1, \2, net.minecraft.world.entity.Prediction.SERVER_ONLY)',
        new,
    )

    if new != txt:
        jf.write_text(new)

# Level.random became getRandom(); only touch files that javac identified for this migration.
random_files = [
    "net/p3pp3rf1y/sophisticatedcore/fluid/FluidUtil.java",
    "net/p3pp3rf1y/sophisticatedcore/util/LootHelper.java",
    "net/p3pp3rf1y/sophisticatedcore/util/InventoryHelper.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/jukebox/JukeboxUpgradeRenderer.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/magnet/MagnetUpgradeWrapper.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/cooking/CookingUpgradeRenderer.java",
    "net/p3pp3rf1y/sophisticatedcore/mixin/common/HopperBlockEntityMixin.java",
    "com/github/salandora/sophisticatedfabriclib/fluid/api/v1/FluidUtil.java",
]
for rel in random_files:
    jf = java_root / rel
    if jf.exists():
        txt = jf.read_text(errors="ignore")
        fixed = re.sub(r"\.random\b", ".getRandom()", txt)
        fixed = fixed.replace("Math.getRandom()()", "Math.random()")
        jf.write_text(fixed)

print("Applied Minecraft 26.x NBT/Level/drop/recipe compatibility patches.")


# Container click input was renamed in Minecraft 26.x.
for jf in java_root.rglob("*.java"):
    txt = jf.read_text(errors="ignore")
    new = txt.replace(
        "net.minecraft.world.inventory.ClickType",
        "net.minecraft.world.inventory.ContainerInput",
    )
    new = re.sub(r"\bClickType\b", "ContainerInput", new)
    if new != txt:
        jf.write_text(new)

print("Applied ClickType -> ContainerInput migration.")


# Additional 26.3 renames confirmed against current sources.
prediction_files = [
    "net/p3pp3rf1y/sophisticatedcore/compat/rei/REICompat.java",
    "net/p3pp3rf1y/sophisticatedcore/compat/jei/CraftingContainerRecipeTransferHandlerServer.java",
    "net/p3pp3rf1y/sophisticatedcore/common/gui/StorageContainerMenuBase.java",
    "net/p3pp3rf1y/sophisticatedcore/util/InventoryHelper.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/infinity/InfinityUpgradeItem.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/crafting/CraftingUpgradeContainer.java",
    "com/github/salandora/sophisticatedfabriclib/transfer/api/v1/ItemStackHandler.java",
    "com/github/salandora/sophisticatedfabriclib/transfer/api/v1/TransferUtil.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/tank/TankClickPayload.java",
    "com/github/salandora/sophisticatedfabriclib/util/Capabilities.java",
]
for rel in prediction_files:
    jf = java_root / rel
    if jf.exists():
        txt = jf.read_text(errors="ignore")
        txt = txt.replace("net.minecraft.world.entity.Prediction", "net.minecraft.util.Prediction")
        jf.write_text(txt)

location_files = [
    "net/p3pp3rf1y/sophisticatedcore/init/ModPayloads.java",
    "com/github/salandora/sophisticatedfabriclib/util/DeferredRegister.java",
    "com/github/salandora/sophisticatedfabriclib/util/DeferredHolder.java",
    "net/p3pp3rf1y/sophisticatedcore/init/ModFluids.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/crafting/CraftingItemHandler.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/FilterLogicContainerBase.java",
    "com/github/salandora/sophisticatedfabriclib/fluid/api/v1/FluidStack.java",
]
for rel in location_files:
    jf = java_root / rel
    if jf.exists():
        txt = jf.read_text(errors="ignore")
        jf.write_text(txt.replace(".location()", ".identifier()"))

normal_files = [
    "net/p3pp3rf1y/sophisticatedcore/upgrades/feeding/FeedingUpgradeWrapper.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/pump/PumpUpgradeWrapper.java",
    "net/p3pp3rf1y/sophisticatedcore/common/CommonEventHandler.java",
    "net/p3pp3rf1y/sophisticatedcore/controller/ControllerBlockEntityBase.java",
    "net/p3pp3rf1y/sophisticatedcore/controller/IControllerBoundable.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/cooking/CookingLogic.java",
]
for rel in normal_files:
    jf = java_root / rel
    if jf.exists():
        txt = jf.read_text(errors="ignore")
        jf.write_text(txt.replace(".getNormal()", ".getUnitVec3i()"))

print("Applied Prediction, ResourceKey.identifier and Direction.getUnitVec3i migrations.")


# Fabric Networking API renamed directional payload registries in 26.x.
for jf in java_root.rglob("*.java"):
    txt = jf.read_text(errors="ignore")
    new = txt.replace("PayloadTypeRegistry.playS2C()", "PayloadTypeRegistry.clientboundPlay()")
    new = new.replace("PayloadTypeRegistry.playC2S()", "PayloadTypeRegistry.serverboundPlay()")
    new = new.replace("PayloadTypeRegistry.configurationS2C()", "PayloadTypeRegistry.clientboundConfiguration()")
    new = new.replace("PayloadTypeRegistry.configurationC2S()", "PayloadTypeRegistry.serverboundConfiguration()")
    if new != txt:
        jf.write_text(new)

print("Applied Fabric 26.x PayloadTypeRegistry directional renames.")


# Fabric Screen Handler API was renamed to Menu API in 26.1+.
for jf in java_root.rglob("*.java"):
    txt = jf.read_text(errors="ignore")
    new = txt.replace(
        "net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerFactory",
        "net.fabricmc.fabric.api.menu.v1.ExtendedMenuProvider",
    )
    new = re.sub(r"\bExtendedScreenHandlerFactory\b", "ExtendedMenuProvider", new)
    if new != txt:
        jf.write_text(new)

print("Applied ExtendedScreenHandlerFactory -> ExtendedMenuProvider migration.")


# Mojang renamed MobSpawnType to EntitySpawnReason in 26.x.
for jf in java_root.rglob("*.java"):
    txt = jf.read_text(errors="ignore")
    new = txt.replace(
        "net.minecraft.world.entity.MobSpawnType",
        "net.minecraft.world.entity.EntitySpawnReason",
    )
    new = re.sub(r"\bMobSpawnType\b", "EntitySpawnReason", new)
    if new != txt:
        jf.write_text(new)

print("Applied MobSpawnType -> EntitySpawnReason migration.")


# Player feedback split in 26.x: system chat vs overlay/actionbar.
for jf in java_root.rglob("*.java"):
    txt = jf.read_text(errors="ignore")
    new = re.sub(r'\.displayClientMessage\((.+?),\s*false\)', r'.sendSystemMessage(\1)', txt)
    new = re.sub(r'\.displayClientMessage\((.+?),\s*true\)', r'.sendOverlayMessage(\1)', new)
    new = new.replace(".getAllKeys()", ".keySet()")
    if new != txt:
        jf.write_text(new)

print("Applied Player feedback split and CompoundTag.keySet migration.")


# More 26.x vanilla API migrations.
for jf in java_root.rglob("*.java"):
    txt = jf.read_text(errors="ignore")
    new = txt

    # ItemStack no longer forwards item registry tags directly.
    new = re.sub(
        r'(\b[A-Za-z_][A-Za-z0-9_]*Stack\b|\bstack\b|\bfirstStack\b|\bsecondStack\b)\.getTags\(\)',
        r'\1.getItem().builtInRegistryHolder().tags()',
        new,
    )

    # Numeric/string Tag value accessors are Optional-returning in 26.x.
    new = new.replace(".getAsInt()", ".asInt().orElse(0)")
    new = new.replace(".getAsLong()", ".asLong().orElse(0L)")
    new = new.replace(".getAsString()", '.asString().orElse("")')

    # Recipe#assemble lost the registry-access parameter. Handle arbitrary first arguments.
    new = re.sub(
        r'\.assemble\(([^;\n]+?),\s*(?:[A-Za-z_][A-Za-z0-9_]*\.)?(?:registryAccess\(\)|registryAccess)\)',
        r'.assemble(\1)',
        new,
    )

    if new != txt:
        jf.write_text(new)

print("Applied item tag, NBT Tag value, and remaining Recipe.assemble migrations.")


# Fabric 26.x Menu API and Mojang advancement package migrations.
for jf in java_root.rglob("*.java"):
    txt = jf.read_text(errors="ignore")
    new = txt
    new = new.replace(
        "net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerType",
        "net.fabricmc.fabric.api.menu.v1.ExtendedMenuType",
    )
    new = new.replace(
        "net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerFactory",
        "net.fabricmc.fabric.api.menu.v1.ExtendedMenuProvider",
    )
    new = re.sub(r"\bExtendedScreenHandlerType\b", "ExtendedMenuType", new)
    new = re.sub(r"\bExtendedScreenHandlerFactory\b", "ExtendedMenuProvider", new)
    new = new.replace(
        "net.minecraft.advancements.critereon.RecipeUnlockedTrigger",
        "net.minecraft.advancements.triggers.RecipeUnlockedTrigger",
    )
    new = new.replace(
        "net.minecraft.advancements.criterion.RecipeUnlockedTrigger",
        "net.minecraft.advancements.triggers.RecipeUnlockedTrigger",
    )
    new = new.replace(
        "net.minecraft.advancements.Criterion",
        "net.minecraft.advancements.triggers.Criterion",
    )
    if new != txt:
        jf.write_text(new)

# Preserve the public Sophisticated class name while using Fabric's new ContainerStorage backend.
iw = java_root / "net/p3pp3rf1y/sophisticatedcore/inventory/InventoryStorageWrapper.java"
if iw.exists():
    txt = iw.read_text(errors="ignore")
    txt = txt.replace("public class ContainerStorageWrapper", "public class InventoryStorageWrapper")
    txt = txt.replace("static ContainerStorageWrapper of(", "static InventoryStorageWrapper of(")
    txt = txt.replace("return new ContainerStorageWrapper(", "return new InventoryStorageWrapper(")
    txt = txt.replace("private ContainerStorageWrapper(", "private InventoryStorageWrapper(")
    iw.write_text(txt)

print("Applied Fabric Menu API, advancement trigger, and InventoryStorageWrapper class-name migrations.")


# Minecraft 26.x item tag and recipe access migrations.
for jf in java_root.rglob("*.java"):
    txt = jf.read_text(errors="ignore")
    new = txt.replace(".getTags()", ".typeHolder().tags()")
    new = new.replace(".getRecipeManager()", ".recipeAccess()")
    if new != txt:
        jf.write_text(new)

print("Applied ItemStack.typeHolder().tags and Level.recipeAccess migrations.")


# Fix Java functional suppliers and 26.x container/fluid accessors.
for jf in java_root.rglob("*.java"):
    txt = jf.read_text(errors="ignore")
    new = txt
    new = new.replace(".asInt().orElse(0)", ".getAsInt()")
    new = new.replace(".asLong().orElse(0L)", ".getAsLong()")
    new = new.replace(".asLong().orElse(0)", ".getAsLong()")
    new = new.replace("tagName.identifier()", "tagName.location()")
    new = new.replace("player.getInventory().items.size()", "player.getInventory().getContainerSize()")
    new = new.replace("inv.items.size()", "inv.getContainerSize()")
    if new != txt:
        jf.write_text(new)

tank = java_root / "net/p3pp3rf1y/sophisticatedcore/upgrades/tank/TankUpgradeWrapper.java"
if tank.exists():
    txt = tank.read_text(errors="ignore")
    txt = txt.replace("contents.getVariant()", "contents.getResource()")
    tank.write_text(txt)

print("Applied supplier, TagKey, inventory size, and FluidStack resource accessor fixes.")


# Minecraft 26.x Slot#getNoItemIcon returns a single Identifier; the block atlas pair was removed.
for rel in [
    "net/p3pp3rf1y/sophisticatedcore/common/gui/SettingsContainerMenu.java",
    "net/p3pp3rf1y/sophisticatedcore/common/gui/StorageContainerMenuBase.java",
]:
    jf = java_root / rel
    if not jf.exists():
        continue
    txt = jf.read_text(errors="ignore")
    txt = txt.replace(
        "Map<Integer, Pair<Identifier, Identifier>> emptySlotIcons",
        "Map<Integer, Identifier> emptySlotIcons",
    )
    txt = txt.replace(
        "public Pair<Identifier, Identifier> getNoItemIcon()",
        "public Identifier getNoItemIcon()",
    )
    txt = txt.replace(
        "new Pair<>(InventoryMenu.BLOCK_ATLAS, textureName)",
        "textureName",
    )
    txt = txt.replace(
        "new Pair<>(InventoryMenu.BLOCK_ATLAS, StorageContainerMenuBase.EMPTY_UPGRADE_SLOT_BACKGROUND)",
        "StorageContainerMenuBase.EMPTY_UPGRADE_SLOT_BACKGROUND",
    )
    txt = txt.replace(
        "new Pair<>(InventoryMenu.BLOCK_ATLAS, SophisticatedCore.getRL(\"item/inaccessible_slot\"))",
        "SophisticatedCore.getRL(\"item/inaccessible_slot\")",
    )
    txt = txt.replace(
        "Pair<Identifier, Identifier> noItemIcon = storageWrapper.getInventoryHandler().getNoItemIcon(slot);",
        "Identifier noItemIcon = storageWrapper.getInventoryHandler().getNoItemIcon(slot);",
    )
    txt = txt.replace(
        "noItemSlotTextures.computeIfAbsent(noItemIcon.getSecond(), rl -> new HashSet<>()).add(slot);",
        "noItemSlotTextures.computeIfAbsent(noItemIcon, rl -> new HashSet<>()).add(slot);",
    )
    jf.write_text(txt)

print("Applied Minecraft 26.x single-Identifier slot icon API.")
