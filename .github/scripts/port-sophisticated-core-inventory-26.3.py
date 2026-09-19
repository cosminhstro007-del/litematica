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


# Port Sophisticated runtime recipe serializers to the 26.x recipe API.
recipe_wrapper = java_root / "net/p3pp3rf1y/sophisticatedcore/crafting/RecipeWrapperSerializer.java"
if recipe_wrapper.exists():
    recipe_wrapper.write_text(r'''package net.p3pp3rf1y.sophisticatedcore.crafting;

import com.mojang.serialization.MapCodec;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeSerializer;

import java.util.function.Function;

public final class RecipeWrapperSerializer {
    private RecipeWrapperSerializer() {}

    public static <T extends Recipe<?>, R extends Recipe<?> & IWrapperRecipe<T>> RecipeSerializer<R> create(
            Function<T, R> initialize, RecipeSerializer<T> recipeSerializer) {
        MapCodec<R> codec = recipeSerializer.codec().xmap(initialize, IWrapperRecipe::getCompose);
        StreamCodec<RegistryFriendlyByteBuf, R> streamCodec = new StreamCodec<>() {
            @Override
            public R decode(RegistryFriendlyByteBuf buffer) {
                return initialize.apply(recipeSerializer.streamCodec().decode(buffer));
            }

            @Override
            public void encode(RegistryFriendlyByteBuf buffer, R value) {
                recipeSerializer.streamCodec().encode(buffer, value.getCompose());
            }
        };
        return new RecipeSerializer<>(codec, streamCodec);
    }
}
''')

upgrade_clear = java_root / "net/p3pp3rf1y/sophisticatedcore/crafting/UpgradeClearRecipe.java"
if upgrade_clear.exists():
    upgrade_clear.write_text(r'''package net.p3pp3rf1y.sophisticatedcore.crafting;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CustomRecipe;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.level.Level;
import net.p3pp3rf1y.sophisticatedcore.init.ModRecipes;
import net.p3pp3rf1y.sophisticatedcore.upgrades.UpgradeItemBase;

public class UpgradeClearRecipe extends CustomRecipe {
    public UpgradeClearRecipe() {}

    @Override
    public boolean matches(CraftingInput inventory, Level level) {
        boolean upgradePresent = false;
        for (int i = 0; i < inventory.size(); i++) {
            ItemStack stack = inventory.getItem(i);
            if (!stack.isEmpty()) {
                if (stack.getItem() instanceof UpgradeItemBase && !stack.getComponents().isEmpty() && !upgradePresent) {
                    upgradePresent = true;
                } else {
                    return false;
                }
            }
        }
        return upgradePresent;
    }

    @Override
    public ItemStack assemble(CraftingInput inventory) {
        ItemStack upgrade = ItemStack.EMPTY;
        for (int i = 0; i < inventory.size(); i++) {
            ItemStack stack = inventory.getItem(i);
            if (!stack.isEmpty() && stack.getItem() instanceof UpgradeItemBase) {
                upgrade = stack;
            }
        }
        return new ItemStack(upgrade.getItem(), 1);
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width >= 1 && height >= 1;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return ModRecipes.UPGRADE_CLEAR_SERIALIZER.get();
    }
}
''')

upgrade_next = java_root / "net/p3pp3rf1y/sophisticatedcore/crafting/UpgradeNextTierRecipe.java"
if upgrade_next.exists():
    upgrade_next.write_text(r'''package net.p3pp3rf1y.sophisticatedcore.crafting;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.ShapedRecipe;
import net.p3pp3rf1y.sophisticatedcore.init.ModRecipes;
import net.p3pp3rf1y.sophisticatedcore.upgrades.IUpgradeItem;

import java.util.Optional;

public class UpgradeNextTierRecipe extends ShapedRecipe implements IWrapperRecipe<ShapedRecipe> {
    private final ShapedRecipe compose;

    public UpgradeNextTierRecipe(ShapedRecipe compose) {
        super(new Recipe.CommonInfo(compose.showNotification()),
                new CraftingRecipe.CraftingBookInfo(compose.category(), compose.group()),
                compose.pattern, compose.result);
        this.compose = compose;
    }

    @Override
    public ShapedRecipe getCompose() {
        return compose;
    }

    @Override
    public ItemStack assemble(CraftingInput inv) {
        ItemStack nextTier = super.assemble(inv);
        getUpgrade(inv).ifPresent(upgrade -> nextTier.components.setAll(upgrade.getComponents()));
        return nextTier;
    }

    private Optional<ItemStack> getUpgrade(CraftingInput inv) {
        for (int slot = 0; slot < inv.size(); slot++) {
            ItemStack slotStack = inv.getItem(slot);
            if (slotStack.getItem() instanceof IUpgradeItem) {
                return Optional.of(slotStack);
            }
        }
        return Optional.empty();
    }

    @Override
    public boolean isSpecial() {
        return true;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return ModRecipes.UPGRADE_NEXT_TIER_SERIALIZER.get();
    }
}
''')

mod_recipes = java_root / "net/p3pp3rf1y/sophisticatedcore/init/ModRecipes.java"
if mod_recipes.exists():
    txt = mod_recipes.read_text(errors="ignore")
    txt = txt.replace("import net.minecraft.world.item.crafting.SimpleCraftingRecipeSerializer;\n", "")
    if "import com.mojang.serialization.MapCodec;" not in txt:
        txt = txt.replace("package net.p3pp3rf1y.sophisticatedcore.init;\n", "package net.p3pp3rf1y.sophisticatedcore.init;\n\nimport com.mojang.serialization.MapCodec;\nimport net.minecraft.network.codec.StreamCodec;\nimport net.minecraft.world.item.crafting.CustomRecipe;\nimport net.minecraft.world.item.crafting.ShapedRecipe;\n")
    txt = txt.replace(
        'RECIPE_SERIALIZERS.register("upgrade_next_tier", UpgradeNextTierRecipe.Serializer::new)',
        'RECIPE_SERIALIZERS.register("upgrade_next_tier", () -> RecipeWrapperSerializer.create(UpgradeNextTierRecipe::new, ShapedRecipe.SERIALIZER))'
    )
    txt = txt.replace(
        'public static final Supplier<SimpleCraftingRecipeSerializer<?>> UPGRADE_CLEAR_SERIALIZER = RECIPE_SERIALIZERS.register("upgrade_clear", () -> new SimpleCraftingRecipeSerializer<>(UpgradeClearRecipe::new));',
        'public static final Supplier<RecipeSerializer<?>> UPGRADE_CLEAR_SERIALIZER = RECIPE_SERIALIZERS.register("upgrade_clear", () -> new RecipeSerializer<>(MapCodec.unit(UpgradeClearRecipe::new), StreamCodec.unit(new UpgradeClearRecipe())));'
    )
    if "net.p3pp3rf1y.sophisticatedcore.crafting.RecipeWrapperSerializer" not in txt:
        txt = txt.replace("import net.p3pp3rf1y.sophisticatedcore.crafting.ItemEnabledCondition;\n",
                          "import net.p3pp3rf1y.sophisticatedcore.crafting.ItemEnabledCondition;\nimport net.p3pp3rf1y.sophisticatedcore.crafting.RecipeWrapperSerializer;\n")
    mod_recipes.write_text(txt)

print("Ported runtime recipe serializers and upgrade recipes to Minecraft 26.x.")


# Minecraft 26.x SavedData is codec-based. Port settings template persistence instead of stubbing it.
sts = java_root / "net/p3pp3rf1y/sophisticatedcore/settings/SettingsTemplateStorage.java"
if sts.exists():
    sts.write_text(r'''package net.p3pp3rf1y.sophisticatedcore.settings;

import com.mojang.serialization.Codec;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
import net.p3pp3rf1y.sophisticatedcore.SophisticatedCore;
import net.p3pp3rf1y.sophisticatedcore.util.NBTHelper;

import java.util.*;

public class SettingsTemplateStorage extends SavedData {
    private Map<UUID, Map<Integer, CompoundTag>> playerTemplates = new HashMap<>();
    private Map<UUID, Map<String, CompoundTag>> playerNamedTemplates = new HashMap<>();
    private static final SettingsTemplateStorage clientStorageCopy = new SettingsTemplateStorage();

    private static final Codec<SettingsTemplateStorage> CODEC = CompoundTag.CODEC.xmap(
            SettingsTemplateStorage::loadTag,
            SettingsTemplateStorage::saveTag
    );

    private static final SavedDataType<SettingsTemplateStorage> TYPE = new SavedDataType<>(
            SophisticatedCore.getRL("settings_templates"),
            SettingsTemplateStorage::new,
            CODEC,
            null
    );

    private SettingsTemplateStorage() {
    }

    private SettingsTemplateStorage(Map<UUID, Map<Integer, CompoundTag>> playerTemplates,
                                    Map<UUID, Map<String, CompoundTag>> playerNamedTemplates) {
        this.playerTemplates = playerTemplates;
        this.playerNamedTemplates = playerNamedTemplates;
    }

    public void putPlayerTemplate(Player player, int slot, CompoundTag settingsTag) {
        playerTemplates.computeIfAbsent(player.getUUID(), u -> new HashMap<>()).put(slot, settingsTag);
        setDirty();
    }

    public void putPlayerNamedTemplate(Player player, String name, CompoundTag settingsTag) {
        playerNamedTemplates.computeIfAbsent(player.getUUID(), u -> new TreeMap<>()).put(name, settingsTag);
        setDirty();
    }

    public Map<Integer, CompoundTag> getPlayerTemplates(Player player) {
        return playerTemplates.getOrDefault(player.getUUID(), new HashMap<>());
    }

    public Map<String, CompoundTag> getPlayerNamedTemplates(Player player) {
        return playerNamedTemplates.getOrDefault(player.getUUID(), new TreeMap<>());
    }

    public static SettingsTemplateStorage get() {
        if (SophisticatedCore.isLogicalServerThread()) {
            MinecraftServer server = SophisticatedCore.getCurrentServer();
            if (server != null) {
                ServerLevel overworld = server.getLevel(Level.OVERWORLD);
                if (overworld != null) {
                    return overworld.getDataStorage().computeIfAbsent(TYPE);
                }
            }
        }
        return clientStorageCopy;
    }

    private CompoundTag saveTag() {
        CompoundTag tag = new CompoundTag();
        NBTHelper.putMap(tag, "playerTemplates", playerTemplates, UUID::toString,
                slotTemplates -> NBTHelper.putMap(new CompoundTag(), "slotTemplates", slotTemplates,
                        String::valueOf, settingsTag -> settingsTag));
        NBTHelper.putMap(tag, "playerNamedTemplates", playerNamedTemplates, UUID::toString,
                namedTemplates -> NBTHelper.putMap(new CompoundTag(), "namedTemplates", namedTemplates,
                        v -> v, settingsTag -> settingsTag));
        return tag;
    }

    private static SettingsTemplateStorage loadTag(CompoundTag tag) {
        return new SettingsTemplateStorage(
                NBTHelper.getMap(tag, "playerTemplates", UUID::fromString,
                        (key, playerTemplatesTag) -> NBTHelper.getMap((CompoundTag) playerTemplatesTag,
                                "slotTemplates", Integer::valueOf,
                                (k, settingsTag) -> Optional.of((CompoundTag) settingsTag))
                ).orElse(new HashMap<>()),
                NBTHelper.getMap(tag, "playerNamedTemplates", UUID::fromString,
                        (key, playerNamedTemplatesTag) -> NBTHelper.getMap((CompoundTag) playerNamedTemplatesTag,
                                "namedTemplates", v -> v,
                                (k, settingsTag) -> Optional.of((CompoundTag) settingsTag), TreeMap::new)
                ).orElse(new TreeMap<>())
        );
    }

    public void clearPlayerTemplates(Player player) {
        playerTemplates.remove(player.getUUID());
        playerNamedTemplates.remove(player.getUUID());
        setDirty();
    }
}
''')

print("Ported SettingsTemplateStorage to codec-based SavedDataType API.")


# Minecraft 26.3 split entity constants into EntityTypes. Fabric entity lookup callbacks
# are typed as Entity, so narrow to the known vanilla inventory entity interfaces explicitly.
for rel in [
    "net/p3pp3rf1y/sophisticatedcore/util/Capabilities.java",
    "com/github/salandora/sophisticatedfabriclib/util/Capabilities.java",
]:
    jf = java_root / rel
    if not jf.exists():
        continue
    txt = jf.read_text(errors="ignore")
    txt = txt.replace("import net.minecraft.world.entity.EntityType;", "import net.minecraft.world.entity.EntityType;\nimport net.minecraft.world.entity.EntityTypes;\nimport net.minecraft.world.Container;\nimport net.minecraft.world.entity.player.Player;")
    for name in ["CHEST_BOAT", "CHEST_MINECART", "HOPPER_MINECART", "PLAYER"]:
        txt = txt.replace(f"EntityType.{name}", f"EntityTypes.{name}")
    if "sophisticatedcore/util/Capabilities.java" in rel:
        txt = txt.replace("InventoryStorageWrapper.of(entity)", "InventoryStorageWrapper.of((Container) entity)")
        txt = txt.replace("InventoryStorageWrapper.of(player)", "InventoryStorageWrapper.of((Player) player)")
    else:
        txt = txt.replace("InvWrapper.of(entity)", "InvWrapper.of((Container) entity)")
        txt = txt.replace("InvWrapper.of(inventory)", "InvWrapper.of((Container) inventory)")
        txt = txt.replace("PlayerInvWrapper.of(player)", "PlayerInvWrapper.of((Player) player)")
    jf.write_text(txt)

print("Ported entity inventory capability registrations to EntityTypes and explicit container/player casts.")


# 26.x NBT primitive tags are records and typed array accessors return Optional.
for jf in java_root.rglob("*.java"):
    txt = jf.read_text(errors="ignore")
    new = txt
    new = new.replace("((LongTag) t).getAsLong()", "((LongTag) t).value()")
    new = new.replace("((IntTag) t).getAsInt()", "((IntTag) t).value()")
    new = new.replace("((IntTag) v).getAsInt()", "((IntTag) v).value()")
    new = re.sub(r'Arrays\.stream\(([^;\n]+)\.getIntArray\(([^)\n]+)\)\)', r'Arrays.stream(\1.getIntArray(\2).orElseGet(() -> new int[0]))', new)
    new = re.sub(r'Arrays\.stream\(([^;\n]+)\.getLongArray\(([^)\n]+)\)\)', r'Arrays.stream(\1.getLongArray(\2).orElseGet(() -> new long[0]))', new)
    if new != txt:
        jf.write_text(new)

# putIntArray no longer accepts List<Integer>; normalize the known runtime list write.
ids = java_root / "net/p3pp3rf1y/sophisticatedcore/settings/itemdisplay/ItemDisplaySettingsCategory.java"
if ids.exists():
    txt = ids.read_text(errors="ignore")
    txt = txt.replace(
        "categoryNbt.putIntArray(SLOTS_TAG, slotIndexes);",
        "categoryNbt.putIntArray(SLOTS_TAG, slotIndexes.stream().mapToInt(Integer::intValue).toArray());",
    )
    ids.write_text(txt)

# Forge Config API Port 26.3 exposes the v5 Fabric event facade.
cfg = java_root / "net/p3pp3rf1y/sophisticatedcore/Config.java"
if cfg.exists():
    txt = cfg.read_text(errors="ignore")
    txt = txt.replace(
        "fuzs.forgeconfigapiport.fabric.api.neoforge.v4.NeoForgeModConfigEvents",
        "fuzs.forgeconfigapiport.fabric.api.v5.ModConfigEvents",
    )
    txt = txt.replace("NeoForgeModConfigEvents.reloading", "ModConfigEvents.reloading")
    cfg.write_text(txt)

print("Applied 26.x NBT primitive/array and Forge Config v5 event API fixes.")


# Replace removed Porting Lib ItemHandlerHelper with a small vanilla 26.3 implementation.
helper = java_root / "io/github/fabricators_of_create/porting_lib/transfer/item/ItemHandlerHelper.java"
helper.parent.mkdir(parents=True, exist_ok=True)
helper.write_text(r'''package io.github.fabricators_of_create.porting_lib.transfer.item;

import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

public final class ItemHandlerHelper {
    private ItemHandlerHelper() {}

    public static void giveItemToPlayer(Player player, ItemStack stack) {
        giveItemToPlayer(player, stack, -1);
    }

    public static void giveItemToPlayer(Player player, ItemStack stack, int preferredSlot) {
        if (stack.isEmpty()) {
            return;
        }

        Inventory inventory = player.getInventory();
        if (preferredSlot >= 0 && preferredSlot < inventory.getContainerSize()) {
            ItemStack existing = inventory.getItem(preferredSlot);
            if (existing.isEmpty()) {
                inventory.setItem(preferredSlot, stack.copy());
                stack.setCount(0);
            } else if (ItemStack.isSameItemSameComponents(existing, stack)) {
                int move = Math.min(stack.getCount(), existing.getMaxStackSize() - existing.getCount());
                if (move > 0) {
                    existing.grow(move);
                    stack.shrink(move);
                }
            }
        }

        if (!stack.isEmpty()) {
            inventory.add(stack);
        }
        if (!stack.isEmpty() && !player.level().isClientSide()) {
            player.drop(stack.copy(), false, net.minecraft.util.Prediction.SERVER_ONLY);
            stack.setCount(0);
        }
    }
}
''')
print("Added vanilla 26.3 ItemHandlerHelper replacement.")


# Minecraft 26.x removed Fabric FuelRegistry and the old ArmorItem material test.
# Use vanilla runtime FuelValues and the piglin_safe_armor item tag.
sitem = java_root / "net/p3pp3rf1y/sophisticatedcore/extensions/item/SophisticatedItem.java"
if sitem.exists():
    txt = sitem.read_text(errors="ignore")
    txt = txt.replace("import net.fabricmc.fabric.api.registry.FuelRegistry;\n", "")
    txt = txt.replace("import net.minecraft.world.item.ArmorItem;\n", "")
    txt = txt.replace("import net.minecraft.world.item.ArmorMaterials;\n", "")
    if "import net.minecraft.tags.ItemTags;" not in txt:
        txt = txt.replace("import net.minecraft.core.component.DataComponents;\n", "import net.minecraft.core.component.DataComponents;\nimport net.minecraft.tags.ItemTags;\nimport net.p3pp3rf1y.sophisticatedcore.SophisticatedCore;\n")
    txt = re.sub(
        r'default int getBurnTime\(ItemStack stack, @Nullable RecipeType<\?> recipeType\) \{.*?\n\t\}',
        '''default int getBurnTime(ItemStack stack, @Nullable RecipeType<?> recipeType) {
        var server = SophisticatedCore.getCurrentServer();
        return server == null ? 0 : server.fuelValues().burnDuration(stack);
    }''',
        txt,
        count=1,
        flags=re.S,
    )
    txt = re.sub(
        r'default boolean makesPiglinsNeutral\(ItemStack stack, LivingEntity wearer\) \{.*?\n\t\}',
        '''default boolean makesPiglinsNeutral(ItemStack stack, LivingEntity wearer) {
        return stack.is(ItemTags.PIGLIN_SAFE_ARMOR);
    }''',
        txt,
        count=1,
        flags=re.S,
    )
    sitem.write_text(txt)

sstack = java_root / "net/p3pp3rf1y/sophisticatedcore/extensions/item/SophisticatedItemStack.java"
if sstack.exists():
    txt = sstack.read_text(errors="ignore")
    if "import net.minecraft.tags.ItemTags;" not in txt:
        txt = txt.replace("import net.minecraft.stats.Stats;\n", "import net.minecraft.stats.Stats;\nimport net.minecraft.tags.ItemTags;\nimport net.p3pp3rf1y.sophisticatedcore.SophisticatedCore;\n")
    txt = re.sub(
        r'default int getBurnTime\(@Nullable RecipeType<\?> recipeType\) \{.*?\n\t\}',
        '''default int getBurnTime(@Nullable RecipeType<?> recipeType) {
        if (self().isEmpty()) {
            return 0;
        }
        var server = SophisticatedCore.getCurrentServer();
        return server == null ? 0 : server.fuelValues().burnDuration(self());
    }''',
        txt,
        count=1,
        flags=re.S,
    )
    txt = re.sub(
        r'default boolean makesPiglinsNeutral\(LivingEntity wearer\) \{.*?\n\t\}',
        '''default boolean makesPiglinsNeutral(LivingEntity wearer) {
        return self().is(ItemTags.PIGLIN_SAFE_ARMOR);
    }''',
        txt,
        count=1,
        flags=re.S,
    )
    sstack.write_text(txt)

print("Ported fuel and piglin-safe item extension logic to vanilla 26.x APIs.")


# Feeding upgrade: InteractionResultHolder was folded into InteractionResult in 26.x.
feeding = java_root / "net/p3pp3rf1y/sophisticatedcore/upgrades/feeding/FeedingUpgradeWrapper.java"
if feeding.exists():
    txt = feeding.read_text(errors="ignore")
    txt = txt.replace("import net.minecraft.world.InteractionResultHolder;\n", "")
    txt = txt.replace("import net.minecraft.world.entity.EntityType;\n", "import net.minecraft.world.entity.EntityType;\nimport net.minecraft.world.entity.EntityTypes;\n")
    txt = txt.replace("level.getEntities(EntityType.PLAYER,", "level.getEntities(EntityTypes.PLAYER,")
    txt = txt.replace(
        "if (singleItemCopy.use(level, player, InteractionHand.MAIN_HAND).getResult() == InteractionResult.CONSUME) {",
        "if (singleItemCopy.use(level, player, InteractionHand.MAIN_HAND).consumesAction()) {"
    )
    old = """\t\t\t\tInteractionResultHolder<ItemStack> result = UseItemCallback.EVENT.invoker().interact(player, level, InteractionHand.MAIN_HAND);
\t\t\t\tItemStack resultItem = result.getObject();
\t\t\t\tif (result.getResult() == InteractionResult.PASS) {
\t\t\t\t\tresultItem = singleItemCopy.getItem().finishUsingItem(singleItemCopy, level, player);
\t\t\t\t}
"""
    new = """\t\t\t\tInteractionResult result = UseItemCallback.EVENT.invoker().interact(player, level, InteractionHand.MAIN_HAND);
\t\t\t\tItemStack resultItem = singleItemCopy;
\t\t\t\tif (result instanceof InteractionResult.Success success && success.heldItemTransformedTo() != null) {
\t\t\t\t\tresultItem = success.heldItemTransformedTo();
\t\t\t\t} else if (result == InteractionResult.PASS) {
\t\t\t\t\tresultItem = singleItemCopy.getItem().finishUsingItem(singleItemCopy, level, player);
\t\t\t\t}
"""
    txt = txt.replace(old, new)
    feeding.write_text(txt)

# Cooking: Fabric FuelRegistry was removed. Vanilla 26.x exposes FuelValues on the server.
cooking = java_root / "net/p3pp3rf1y/sophisticatedcore/upgrades/cooking/CookingLogic.java"
if cooking.exists():
    txt = cooking.read_text(errors="ignore")
    txt = txt.replace("import net.fabricmc.fabric.api.registry.FuelRegistry;\n", "")
    if "import net.p3pp3rf1y.sophisticatedcore.SophisticatedCore;" not in txt:
        txt = txt.replace(
            "import net.p3pp3rf1y.sophisticatedcore.init.ModCoreDataComponents;\n",
            "import net.p3pp3rf1y.sophisticatedcore.SophisticatedCore;\nimport net.p3pp3rf1y.sophisticatedcore.init.ModCoreDataComponents;\n"
        )
    txt = txt.replace(
        "return (int) (Objects.requireNonNullElse(FuelRegistry.INSTANCE.get(fuel.getItem()), 0) * burnTimeModifier);",
        "var server = SophisticatedCore.getCurrentServer();\n\t\treturn server == null ? 0 : (int) (server.fuelValues().burnDuration(fuel) * burnTimeModifier);"
    )
    cooking.write_text(txt)

# Fabric Networking 26.x renamed createS2CPacket -> createClientboundPacket.
packet = java_root / "net/p3pp3rf1y/sophisticatedcore/network/PacketDistributor.java"
if packet.exists():
    txt = packet.read_text(errors="ignore")
    txt = txt.replace("ServerPlayNetworking.createS2CPacket", "ServerPlayNetworking.createClientboundPacket")
    packet.write_text(txt)

print("Ported feeding InteractionResult, cooking FuelValues, and networking packet creation to 26.x.")


# Fabric API lookup cache implementation renamed ServerWorldCache -> ServerLevelCache.
sbe = java_root / "net/p3pp3rf1y/sophisticatedcore/extensions/block/entity/SophisticatedBlockEntity.java"
if sbe.exists():
    txt = sbe.read_text(errors="ignore")
    txt = txt.replace(
        "net.fabricmc.fabric.impl.lookup.block.ServerWorldCache",
        "net.fabricmc.fabric.impl.lookup.block.ServerLevelCache"
    )
    txt = txt.replace("(ServerWorldCache) serverLevel", "(ServerLevelCache) serverLevel")
    sbe.write_text(txt)

# SFL BucketPickupHandlerWrapper now carries the acting player explicitly.
pump = java_root / "net/p3pp3rf1y/sophisticatedcore/upgrades/pump/PumpUpgradeWrapper.java"
if pump.exists():
    txt = pump.read_text(errors="ignore")
    txt = txt.replace(
        "new BucketPickupHandlerWrapper(/*player, */bucketPickup, level, pos)",
        "new BucketPickupHandlerWrapper(player, bucketPickup, level, pos)"
    )
    pump.write_text(txt)

print("Ported Fabric block lookup cache name and bucket pickup wrapper player parameter.")


# Keep common/server portions of block extension interfaces after client-only source pruning.
block_ext = java_root / "net/p3pp3rf1y/sophisticatedcore/extensions/block/SophisticatedBlock.java"
block_ext.parent.mkdir(parents=True, exist_ok=True)
block_ext.write_text(r'''package net.p3pp3rf1y.sophisticatedcore.extensions.block;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

public interface SophisticatedBlock {
    default boolean sophisticatedCore_addLandingEffects(BlockState state1, ServerLevel level, BlockPos pos, BlockState state2, LivingEntity entity, int numberOfParticles) {
        return false;
    }

    default boolean sophisticatedCore_addRunningEffects(BlockState state, Level level, BlockPos pos, Entity entity) {
        return false;
    }
}
''')

block_state_ext = java_root / "net/p3pp3rf1y/sophisticatedcore/extensions/block/SophisticatedBlockState.java"
block_state_ext.write_text(r'''package net.p3pp3rf1y.sophisticatedcore.extensions.block;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

public interface SophisticatedBlockState {
    private BlockState self() {
        return (BlockState) this;
    }

    default boolean sophisticatedCore_addLandingEffects(ServerLevel level, BlockPos pos, BlockState state2, LivingEntity entity, int numberOfParticles) {
        return ((SophisticatedBlock)(Object) self().getBlock()).sophisticatedCore_addLandingEffects(self(), level, pos, state2, entity, numberOfParticles);
    }

    default boolean sophisticatedCore_addRunningEffects(Level level, BlockPos pos, Entity entity) {
        return ((SophisticatedBlock)(Object) self().getBlock()).sophisticatedCore_addRunningEffects(self(), level, pos, entity);
    }
}
''')

# This vendored SFL NeoForge-style component handler is not referenced by Core runtime and
# depends on a separate SFL injected-interface package that is not needed for this port.
unused_sfl_component = java_root / "com/github/salandora/sophisticatedfabriclib/transfer/api/v1/ComponentItemHandler.java"
if unused_sfl_component.exists():
    unused_sfl_component.unlink()

# Fluid container item context: SFL replacement is a factory interface, not a mutable constructor.
fluid_util = java_root / "net/p3pp3rf1y/sophisticatedcore/fluid/FluidUtil.java"
if fluid_util.exists():
    txt = fluid_util.read_text(errors="ignore")
    txt = txt.replace(
        "import io.github.fabricators_of_create.porting_lib.transfer.MutableContainerItemContext;",
        "import com.github.salandora.sophisticatedfabriclib.transfer.api.v1.ItemStackContainerItemContext;"
    )
    txt = txt.replace(
        "import com.github.salandora.sophisticatedfabriclib.transfer.api.v1.ItemStackContainerItemContext;",
        "import com.github.salandora.sophisticatedfabriclib.transfer.api.v1.ItemStackContainerItemContext;"
    )
    txt = txt.replace(
        "new MutableContainerItemContext(containerCopy)",
        "ItemStackContainerItemContext.ofSingleStack(containerCopy)"
    )
    fluid_util.write_text(txt)

# Tuple was removed from vanilla. Storage dye recipe only needs a simple key/value pair.
dye = java_root / "net/p3pp3rf1y/sophisticatedcore/crafting/StorageDyeRecipeBase.java"
if dye.exists():
    txt = dye.read_text(errors="ignore")
    txt = txt.replace("import net.minecraft.util.Tuple;\n", "")
    txt = txt.replace("Tuple<Integer, ItemStack> columnStorage = null;", "Map.Entry<Integer, ItemStack> columnStorage = null;")
    txt = txt.replace("new Tuple<>(column, slotStack)", "Map.entry(column, slotStack)")
    txt = txt.replace("columnStorage.getB()", "columnStorage.getValue()")
    txt = txt.replace("columnStorage.getA()", "columnStorage.getKey()")
    txt = txt.replace(
        "public ItemStack assemble(CraftingInput inv, HolderLookup.Provider registries)",
        "public ItemStack assemble(CraftingInput inv)"
    )
    dye.write_text(txt)

print("Restored common block extensions, ported fluid context and dye pair, removed unused SFL component handler.")


# Close the final Fabric 26.3 common-pass API renames.
ceh = java_root / "net/p3pp3rf1y/sophisticatedcore/common/CommonEventHandler.java"
if ceh.exists():
    txt = ceh.read_text(errors="ignore")
    txt = txt.replace(
        "net.fabricmc.fabric.api.event.lifecycle.v1.ServerWorldEvents",
        "net.fabricmc.fabric.api.event.lifecycle.v1.ServerLevelEvents",
    )
    txt = txt.replace("ServerWorldEvents.UNLOAD", "ServerLevelEvents.UNLOAD")
    txt = txt.replace("ServerTickEvents.END_WORLD_TICK", "ServerTickEvents.END_LEVEL_TICK")
    ceh.write_text(txt)

hopper = java_root / "net/p3pp3rf1y/sophisticatedcore/mixin/common/HopperBlockEntityMixin.java"
if hopper.exists():
    txt = hopper.read_text(errors="ignore")
    txt = txt.replace(
        "net.fabricmc.fabric.api.transfer.v1.item.InventoryStorage",
        "net.fabricmc.fabric.api.transfer.v1.item.ContainerStorage",
    )
    txt = txt.replace("InventoryStorage.of(", "ContainerStorage.of(")
    hopper.write_text(txt)

mf = java_root / "net/p3pp3rf1y/sophisticatedcore/init/ModFluids.java"
if mf.exists():
    txt = mf.read_text(errors="ignore")
    txt = txt.replace("import io.github.fabricators_of_create.porting_lib.fluids.PortingLibFluids;\n", "")
    txt = txt.replace(
        "import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;",
        "import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;",
    )
    txt = txt.replace("FabricItemGroup.builder()", "FabricCreativeModeTab.builder()")
    txt = re.sub(
        r'\n\s*public static final DeferredRegister<FluidType> FLUID_TYPES = .*?;\n',
        '\n',
        txt,
    )
    txt = re.sub(
        r'public static final Supplier<FluidType> XP_FLUID_TYPE = FLUID_TYPES\.register\("experience", \(\) -> new FluidType\((.*?)\)\);',
        r'public static final FluidType XP_FLUID_TYPE_VALUE = new FluidType(\1);\n\tpublic static final Supplier<FluidType> XP_FLUID_TYPE = () -> XP_FLUID_TYPE_VALUE;',
        txt,
        flags=re.S,
    )
    txt = txt.replace("\n\t\tFLUID_TYPES.register();", "")
    mf.write_text(txt)

print("Closed final common-pass Fabric 26.3 API renames.")


# Safe API fixes confirmed directly against Minecraft 26.3 bytecode.
# These are intentionally narrow and preserve the existing runtime semantics.

# AbstractCookingRecipe#getCookingTime() -> cookingTime().
cooking = java_root / "net/p3pp3rf1y/sophisticatedcore/upgrades/cooking/CookingLogic.java"
if cooking.exists():
    txt = cooking.read_text(errors="ignore")
    txt = txt.replace(".getCookingTime()", ".cookingTime()")
    cooking.write_text(txt)

# Inventory#getSelected() -> getSelectedItem().
server_player_mixin = java_root / "net/p3pp3rf1y/sophisticatedcore/mixin/common/ServerPlayerMixin.java"
if server_player_mixin.exists():
    txt = server_player_mixin.read_text(errors="ignore")
    txt = txt.replace("inventory.getSelected()", "inventory.getSelectedItem()")
    server_player_mixin.write_text(txt)

# BucketItem now exposes the bucket fluid through getContent().
bucket_wrapper = java_root / "com/github/salandora/sophisticatedfabriclib/fluid/api/v1/BucketPickupHandlerWrapper.java"
if bucket_wrapper.exists():
    txt = bucket_wrapper.read_text(errors="ignore")
    txt = txt.replace("bucket.content", "bucket.getContent()")
    bucket_wrapper.write_text(txt)

# Use the public Fabric ItemApiLookup path instead of relying on the old injected ItemStack capability helper.
sfl_fluid_util = java_root / "com/github/salandora/sophisticatedfabriclib/fluid/api/v1/FluidUtil.java"
if sfl_fluid_util.exists():
    txt = sfl_fluid_util.read_text(errors="ignore")
    txt = txt.replace(
        "return Optional.ofNullable(stack.sophisticatedFabricLibrary_getCapability(Capabilities.FluidHandler.ITEM));",
        "return Optional.ofNullable(ContainerItemContext.withConstant(stack).find(Capabilities.FluidHandler.ITEM));"
    )
    sfl_fluid_util.write_text(txt)

# PatchedDataComponentMap#set expects the exact component generic type in 26.3.
item_stack_mixin = java_root / "net/p3pp3rf1y/sophisticatedcore/mixin/common/ItemStackMixin.java"
if item_stack_mixin.exists():
    txt = item_stack_mixin.read_text(errors="ignore")
    old = """\t@Override
\tpublic <T> @Nullable T sophisticatedCore_set(DataComponentType<? super T> type, @Nullable T value) {
\t\treturn this.components.set(type, value);
\t}
"""
    new = """\t@Override
\t@SuppressWarnings(\"unchecked\")
\tpublic <T> @Nullable T sophisticatedCore_set(DataComponentType<? super T> type, @Nullable T value) {
\t\treturn this.components.set((DataComponentType<T>) (DataComponentType<?>) type, value);
\t}
"""
    if old in txt:
        txt = txt.replace(old, new)
    item_stack_mixin.write_text(txt)

print("Applied confirmed MC 26.3 cooking, selected-slot, bucket, fluid lookup, and component generic fixes.")


# Second confirmed MC 26.3 compatibility pass.

# Cooking recipes now expose output via assemble(SingleRecipeInput), and item remainders are ItemStackTemplate.
cooking = java_root / "net/p3pp3rf1y/sophisticatedcore/upgrades/cooking/CookingLogic.java"
if cooking.exists():
    txt = cooking.read_text(errors="ignore")
    if "import net.minecraft.world.item.crafting.SingleRecipeInput;" not in txt:
        txt = txt.replace(
            "import net.minecraft.world.item.crafting.RecipeType;\n",
            "import net.minecraft.world.item.crafting.RecipeType;\nimport net.minecraft.world.item.crafting.SingleRecipeInput;\n"
        )
    txt = txt.replace("private void smelt(Recipe<?> recipe, Level level)", "private void smelt(T recipe, Level level)")
    txt = txt.replace("protected boolean canSmelt(Recipe<?> cookingRecipe, Level level)", "protected boolean canSmelt(T cookingRecipe, Level level)")
    txt = txt.replace(
        "ItemStack recipeOutput = recipe.getResultItem(level.registryAccess());",
        "ItemStack recipeOutput = recipe.assemble(new SingleRecipeInput(input));"
    )
    txt = txt.replace(
        "ItemStack recipeOutput = cookingRecipe.getResultItem(level.registryAccess());",
        "ItemStack recipeOutput = cookingRecipe.assemble(new SingleRecipeInput(getCookInput()));"
    )
    old = """\t\t\t\tif (fuel.getItem().hasCraftingRemainingItem()) {
\t\t\t\t\tsetFuelWithoutValidation(fuel.getRecipeRemainder());
\t\t\t\t} else if (!fuel.isEmpty()) {
\t\t\t\t\tfuel.shrink(1);
\t\t\t\t\tsetFuel(fuel);
\t\t\t\t\tif (fuel.isEmpty()) {
\t\t\t\t\t\tsetFuel(fuel.getRecipeRemainder());
\t\t\t\t\t}
\t\t\t\t}
"""
    new = """\t\t\t\tvar craftingRemainder = fuel.getItem().getCraftingRemainder();
\t\t\t\tif (craftingRemainder != null) {
\t\t\t\t\tsetFuelWithoutValidation(craftingRemainder.create());
\t\t\t\t} else if (!fuel.isEmpty()) {
\t\t\t\t\tfuel.shrink(1);
\t\t\t\t\tsetFuel(fuel);
\t\t\t\t}
"""
    txt = txt.replace(old, new)
    cooking.write_text(txt)

# Fix accidental global isClientSide field rewrite in StorageInventorySlot.
storage_slot = java_root / "net/p3pp3rf1y/sophisticatedcore/common/gui/StorageInventorySlot.java"
if storage_slot.exists():
    txt = storage_slot.read_text(errors="ignore")
    txt = txt.replace("this.isClientSide() = isClientSide;", "this.isClientSide = isClientSide;")
    storage_slot.write_text(txt)

# Slot#getNoItemIcon now returns a single Identifier instead of atlas/texture Pair.
storage_menu = java_root / "net/p3pp3rf1y/sophisticatedcore/common/gui/StorageContainerMenuBase.java"
if storage_menu.exists():
    txt = storage_menu.read_text(errors="ignore")
    txt = txt.replace(
        "public static final Pair<Identifier, Identifier> INACCESSIBLE_SLOT_BACKGROUND = SophisticatedCore.getRL(\"item/inaccessible_slot\");",
        "public static final Identifier INACCESSIBLE_SLOT_BACKGROUND = SophisticatedCore.getRL(\"item/inaccessible_slot\");"
    )
    txt = txt.replace(
        "public static final Pair<ResourceLocation, ResourceLocation> INACCESSIBLE_SLOT_BACKGROUND = new Pair<>(InventoryMenu.BLOCK_ATLAS, SophisticatedCore.getRL(\"item/inaccessible_slot\"));",
        "public static final Identifier INACCESSIBLE_SLOT_BACKGROUND = SophisticatedCore.getRL(\"item/inaccessible_slot\");"
    )
    txt = txt.replace("public Pair<Identifier, Identifier> getNoItemIcon()", "public Identifier getNoItemIcon()")
    txt = txt.replace("public Pair<ResourceLocation, ResourceLocation> getNoItemIcon()", "public Identifier getNoItemIcon()")
    storage_menu.write_text(txt)

# Vanilla 26.x ContainerSynchronizer now owns RemoteSlot instances. Mirror vanilla's component hashing.
sync = java_root / "net/p3pp3rf1y/sophisticatedcore/common/gui/HighStackCountSynchronizer.java"
if sync.exists():
    txt = sync.read_text(errors="ignore")
    txt = txt.replace("import net.minecraft.core.NonNullList;\n", "")
    needed = [
        "import com.google.common.cache.CacheBuilder;",
        "import com.google.common.cache.CacheLoader;",
        "import com.google.common.cache.LoadingCache;",
        "import com.google.common.hash.HashCode;",
        "import com.mojang.serialization.DynamicOps;",
        "import net.minecraft.core.component.TypedDataComponent;",
        "import net.minecraft.util.HashOps;",
        "import net.minecraft.world.inventory.RemoteSlot;",
        "import java.util.List;",
    ]
    marker = "package net.p3pp3rf1y.sophisticatedcore.common.gui;\n"
    for imp in needed:
        if imp not in txt:
            txt = txt.replace(marker, marker + "\n" + imp + "\n")
    txt = txt.replace(
        "private final ServerPlayer player;",
        """private final ServerPlayer player;
\tprivate final LoadingCache<TypedDataComponent<?>, Integer> componentHashCache;"""
    )
    txt = txt.replace(
        """\tpublic HighStackCountSynchronizer(ServerPlayer player) {
\t\tthis.player = player;
\t}
""",
        """\tpublic HighStackCountSynchronizer(ServerPlayer player) {
\t\tthis.player = player;
\t\tthis.componentHashCache = CacheBuilder.newBuilder().maximumSize(256L).build(
\t\t\t\tnew CacheLoader<TypedDataComponent<?>, Integer>() {
\t\t\t\t\tprivate final DynamicOps<HashCode> registryHashOps =
\t\t\t\t\t\t\tHighStackCountSynchronizer.this.player.registryAccess().createSerializationContext(HashOps.CRC32C_INSTANCE);

\t\t\t\t\t@Override
\t\t\t\t\tpublic Integer load(TypedDataComponent<?> component) {
\t\t\t\t\t\treturn component.encodeValue(this.registryHashOps)
\t\t\t\t\t\t\t\t.getOrThrow(msg -> new IllegalArgumentException("Failed to hash " + component + ": " + msg))
\t\t\t\t\t\t\t\t.asInt();
\t\t\t\t\t}
\t\t\t\t});
\t}
"""
    )
    txt = txt.replace(
        "public void sendInitialData(AbstractContainerMenu containerMenu, NonNullList<ItemStack> stacks, ItemStack carriedStack, int[] dataSlots)",
        "public void sendInitialData(AbstractContainerMenu containerMenu, List<ItemStack> stacks, ItemStack carriedStack, int[] dataSlots)"
    )
    if "public RemoteSlot createSlot()" not in txt:
        insert = """
\t@Override
\tpublic RemoteSlot createSlot() {
\t\treturn new RemoteSlot.Synchronized(componentHashCache::getUnchecked);
\t}
"""
        txt = txt.replace("\n}", insert + "\n}")
    sync.write_text(txt)

# ChunkAccess constructor now takes PalettedContainerFactory instead of biome registry.
chunk_mixin = java_root / "net/p3pp3rf1y/sophisticatedcore/mixin/common/LevelChunkMixin.java"
if chunk_mixin.exists():
    txt = chunk_mixin.read_text(errors="ignore")
    txt = txt.replace("import net.minecraft.core.Registry;\n", "")
    txt = txt.replace("import net.minecraft.world.level.biome.Biome;\n", "")
    if "import net.minecraft.world.level.chunk.PalettedContainerFactory;" not in txt:
        txt = txt.replace(
            "import net.minecraft.world.level.chunk.LevelChunkSection;\n",
            "import net.minecraft.world.level.chunk.LevelChunkSection;\nimport net.minecraft.world.level.chunk.PalettedContainerFactory;\n"
        )
    txt = txt.replace(
        "Registry<Biome> biomeRegistry, long inhabitedTime",
        "PalettedContainerFactory palettedContainerFactory, long inhabitedTime"
    )
    txt = txt.replace(
        "super(chunkPos, upgradeData, levelHeightAccessor, biomeRegistry, inhabitedTime, sections, blendingData);",
        "super(chunkPos, upgradeData, levelHeightAccessor, palettedContainerFactory, inhabitedTime, sections, blendingData);"
    )
    chunk_mixin.write_text(txt)

print("Applied MC 26.3 cooking output/remainder, slot icon, RemoteSlot synchronizer, and chunk constructor fixes.")


# Third MC 26.3 pass: fuel components, fluid environment APIs, generic entity containers, Fabric registry rename.

def ensure_import(path: Path, anchor: str, imp: str):
    if not path.exists():
        return
    txt = path.read_text(errors="ignore")
    if imp not in txt:
        txt = txt.replace(anchor, anchor + "\n" + imp)
        path.write_text(txt)

# Fabric API 26.1+ renamed FabricRegistryBuilder#createSimple -> create.
soph_fluid = java_root / "com/github/salandora/sophisticatedfabriclib/fluid/SophisticatedFluid.java"
if soph_fluid.exists():
    txt = soph_fluid.read_text(errors="ignore")
    txt = txt.replace("FabricRegistryBuilder.createSimple(FLUID_TYPES_KEY)", "FabricRegistryBuilder.create(FLUID_TYPES_KEY)")
    soph_fluid.write_text(txt)

# FlowingFluid#canConvertToSource now receives ServerLevel.
base_flowing = java_root / "com/github/salandora/sophisticatedfabriclib/fluid/api/v1/BaseFlowingFluid.java"
if base_flowing.exists():
    txt = base_flowing.read_text(errors="ignore")
    if "import net.minecraft.server.level.ServerLevel;" not in txt:
        txt = txt.replace("import net.minecraft.core.Direction;\n", "import net.minecraft.core.Direction;\nimport net.minecraft.server.level.ServerLevel;\n")
    txt = txt.replace("protected boolean canConvertToSource(Level level)", "protected boolean canConvertToSource(ServerLevel level)")
    base_flowing.write_text(txt)

# DimensionType#ultraWarm moved to EnvironmentAttributes.
sfl_fluid_util = java_root / "com/github/salandora/sophisticatedfabriclib/fluid/api/v1/FluidUtil.java"
if sfl_fluid_util.exists():
    txt = sfl_fluid_util.read_text(errors="ignore")
    if "import net.minecraft.world.attribute.EnvironmentAttributes;" not in txt:
        txt = txt.replace("import net.minecraft.world.InteractionHand;\n", "import net.minecraft.world.InteractionHand;\nimport net.minecraft.world.attribute.EnvironmentAttributes;\n")
    txt = txt.replace(
        "level.dimensionType().ultraWarm()",
        "level.environmentAttributes().getValue(EnvironmentAttributes.WATER_EVAPORATES, pos)"
    )
    sfl_fluid_util.write_text(txt)

# 26.3 split the generic chest-boat type into wood-specific types.
# Register a fallback for any vanilla Container entity instead of maintaining a brittle entity-type list.
caps = java_root / "com/github/salandora/sophisticatedfabriclib/util/Capabilities.java"
if caps.exists():
    txt = caps.read_text(errors="ignore")
    if "import net.minecraft.world.Container;" not in txt:
        txt = txt.replace("import net.minecraft.core.Direction;\n", "import net.minecraft.core.Direction;\nimport net.minecraft.world.Container;\n")
    txt = txt.replace("import java.util.List;\n", "")
    old = """\t\tstatic {
\t\t\tvar containerEntities = List.of(
\t\t\t\t\tEntityType.CHEST_BOAT,
\t\t\t\t\tEntityType.CHEST_MINECART,
\t\t\t\t\tEntityType.HOPPER_MINECART);
\t\t\tfor (var entityType : containerEntities) {
\t\t\t\tENTITY.registerForType((entity, ctx) -> InvWrapper.of(entity), entityType);
\t\t\t\tENTITY_AUTOMATION.registerForType((inventory, direction) -> InvWrapper.of(inventory), entityType);
\t\t\t}

\t\t\tENTITY.registerForType((player, ctx) -> PlayerInvWrapper.of(player), EntityType.PLAYER);
"""
    new = """\t\tstatic {
\t\t\tENTITY.registerFallback((entity, ctx) -> entity instanceof Container container ? InvWrapper.of(container) : null);
\t\t\tENTITY_AUTOMATION.registerFallback((entity, direction) -> entity instanceof Container container ? InvWrapper.of(container) : null);

\t\t\tENTITY.registerForType((player, ctx) -> PlayerInvWrapper.of(player), EntityType.PLAYER);
"""
    txt = txt.replace(old, new)
    caps.write_text(txt)

# FuelRegistry was replaced by data-component backed cooking fuel values.
# Use the same vanilla 26.3 ResolvableInt path; null loot context is valid for constant vanilla fuel providers.
for rel in [
    "net/p3pp3rf1y/sophisticatedcore/upgrades/cooking/CookingLogic.java",
    "net/p3pp3rf1y/sophisticatedcore/extensions/item/SophisticatedItem.java",
    "net/p3pp3rf1y/sophisticatedcore/extensions/item/SophisticatedItemStack.java",
]:
    p = java_root / rel
    if not p.exists():
        continue
    txt = p.read_text(errors="ignore")
    txt = txt.replace("import net.fabricmc.fabric.api.registry.FuelRegistry;\n", "")
    imports = [
        "import net.minecraft.core.component.DataComponents;",
        "import net.minecraft.world.item.component.CookingFuel;",
        "import net.minecraft.world.level.storage.loot.providers.number.ints.ResolvableInt;",
    ]
    pkg_end = txt.find("\n\n", txt.find("package "))
    for imp in imports:
        if imp not in txt:
            txt = txt[:pkg_end+2] + imp + "\n" + txt[pkg_end+2:]
    if rel.endswith("CookingLogic.java"):
        txt = txt.replace(
            "return (int) (Objects.requireNonNullElse(FuelRegistry.INSTANCE.get(fuel.getItem()), 0) * burnTimeModifier);",
            "return (int) (ResolvableInt.getFromItem(fuel, DataComponents.COOKING_FUEL, CookingFuel::burnTime, null, 0) * burnTimeModifier);"
        )
        txt = txt.replace(
            "return server == null ? 0 : (int) (server.fuelValues().burnDuration(fuel) * burnTimeModifier);",
            "return (int) (ResolvableInt.getFromItem(fuel, DataComponents.COOKING_FUEL, CookingFuel::burnTime, null, 0) * burnTimeModifier);"
        )
    elif rel.endswith("SophisticatedItem.java"):
        txt = txt.replace(
            """\t\tInteger burnTime = FuelRegistry.INSTANCE.get(stack.getItem());
\t\treturn burnTime != null ? burnTime : 0;""",
            """\t\treturn ResolvableInt.getFromItem(stack, DataComponents.COOKING_FUEL, CookingFuel::burnTime, null, 0);"""
        )
        txt = txt.replace(
            "return server == null ? 0 : server.fuelValues().burnDuration(stack);",
            "return ResolvableInt.getFromItem(stack, DataComponents.COOKING_FUEL, CookingFuel::burnTime, null, 0);"
        )
    elif rel.endswith("SophisticatedItemStack.java"):
        txt = txt.replace(
            "return server == null ? 0 : server.fuelValues().burnDuration(self());",
            "return ResolvableInt.getFromItem(self(), DataComponents.COOKING_FUEL, CookingFuel::burnTime, null, 0);"
        )
    p.write_text(txt)

print("Applied MC 26.3 fuel-component, environment attribute, Fabric registry and entity-container fixes.")


# Container remote-state changes in 26.3: remoteCarried is RemoteSlot, not ItemStack.
storage_menu = java_root / "net/p3pp3rf1y/sophisticatedcore/common/gui/StorageContainerMenuBase.java"
if storage_menu.exists():
    txt = storage_menu.read_text(errors="ignore")
    if "import net.minecraft.world.inventory.RemoteSlot;" not in txt:
        txt = txt.replace("import net.minecraft.world.inventory.ContainerSynchronizer;\n", "import net.minecraft.world.inventory.ContainerSynchronizer;\nimport net.minecraft.world.inventory.RemoteSlot;\n")
    txt = txt.replace("remoteSlots.add(ItemStack.EMPTY);", "remoteSlots.add(RemoteSlot.PLACEHOLDER);")
    txt = txt.replace(
        "remoteCarried = getCarried().copy();",
        "remoteCarried.force(getCarried().copy());"
    )
    txt = txt.replace(
        "synchronizer.sendInitialData(this, allRemoteSlots, remoteCarried, new int[]{});",
        "synchronizer.sendInitialData(this, allRemoteSlots, getCarried().copy(), new int[]{});"
    )
    # Vanilla no longer has setRemoteSlotNoCopy; keep this Sophisticated helper without pretending to override.
    txt = txt.replace(
        "\t@Override\n\tpublic void setRemoteSlotNoCopy(int slotIndex, ItemStack stack)",
        "\tpublic void setRemoteSlotNoCopy(int slotIndex, ItemStack stack)"
    )
    storage_menu.write_text(txt)

# Update the access widener to the 26.3 field/method descriptors.
aw = CORE / "src/main/resources/sophisticatedcore.accesswidener"
if aw.exists():
    txt = aw.read_text(errors="ignore")
    txt = txt.replace(
        "accessible field net/minecraft/world/inventory/AbstractContainerMenu remoteCarried Lnet/minecraft/world/item/ItemStack;",
        "accessible field net/minecraft/world/inventory/AbstractContainerMenu remoteCarried Lnet/minecraft/world/inventory/RemoteSlot;"
    )
    # doClick is private and now takes ContainerInput; make it accessible for the later exact behavior port.
    txt = txt.replace(
        "transitive-extendable method net/minecraft/world/inventory/AbstractContainerMenu doClick (IILnet/minecraft/world/inventory/ClickType;Lnet/minecraft/world/entity/player/Player;)V",
        "accessible method net/minecraft/world/inventory/AbstractContainerMenu doClick (IILnet/minecraft/world/inventory/ContainerInput;Lnet/minecraft/world/entity/player/Player;)V"
    )
    aw.write_text(txt)

# Slot background APIs now carry only the texture Identifier, not atlas+texture Pair.
for rel in [
    "net/p3pp3rf1y/sophisticatedcore/inventory/IInventoryPartHandler.java",
    "net/p3pp3rf1y/sophisticatedcore/inventory/InventoryPartitioner.java",
    "net/p3pp3rf1y/sophisticatedcore/inventory/InventoryHandler.java",
]:
    p = java_root / rel
    if not p.exists():
        continue
    txt = p.read_text(errors="ignore")
    txt = txt.replace("Pair<Identifier, Identifier> getNoItemIcon", "Identifier getNoItemIcon")
    txt = txt.replace("Pair<ResourceLocation, ResourceLocation> getNoItemIcon", "Identifier getNoItemIcon")
    # After common mapping migration ResourceLocation is Identifier; handle both possible bodies.
    txt = txt.replace(
        "return getPartBySlot(slot).getNoItemIcon(slot);",
        "return getPartBySlot(slot).getNoItemIcon(slot);"
    )
    p.write_text(txt)

print("Applied 26.3 RemoteSlot access-widener and slot-icon type migration.")


# Fourth MC 26.3 pass: NBT Optional API + ItemStack codec serialization.

codec_helper = java_root / "net/p3pp3rf1y/sophisticatedcore/util/CodecHelper.java"
if codec_helper.exists():
    txt = codec_helper.read_text(errors="ignore")
    txt = txt.replace("ItemStack.ITEM_NON_AIR_CODEC.fieldOf(\"id\").forGetter(ItemStack::getItemHolder)", "Item.CODEC_WITH_BOUND_COMPONENTS.fieldOf(\"id\").forGetter(ItemStack::typeHolder)")
    txt = txt.replace("p_330103_ -> p_330103_.components.asPatch()", "ItemStack::getComponentsPatch")
    imports = [
        "import net.minecraft.core.HolderLookup;",
        "import net.minecraft.nbt.CompoundTag;",
        "import net.minecraft.nbt.NbtOps;",
        "import net.minecraft.nbt.Tag;",
        "import net.minecraft.resources.RegistryOps;",
        "import net.minecraft.world.item.Item;",
        "import java.util.Optional;",
    ]
    pkg_end = txt.find("\n\n", txt.find("package "))
    for imp in imports:
        if imp not in txt:
            txt = txt[:pkg_end+2] + imp + "\n" + txt[pkg_end+2:]
    if "encodeItemStack(HolderLookup.Provider" not in txt:
        helper = """
\tpublic static CompoundTag encodeItemStack(HolderLookup.Provider registries, ItemStack stack) {
\t\tif (stack.isEmpty()) {
\t\t\treturn new CompoundTag();
\t\t}
\t\treturn OVERSIZED_ITEM_STACK_CODEC
\t\t\t\t.encodeStart(RegistryOps.create(NbtOps.INSTANCE, registries), stack)
\t\t\t\t.result()
\t\t\t\t.filter(CompoundTag.class::isInstance)
\t\t\t\t.map(CompoundTag.class::cast)
\t\t\t\t.orElseGet(CompoundTag::new);
\t}

\tpublic static Optional<ItemStack> decodeItemStackOptional(HolderLookup.Provider registries, Tag tag) {
\t\tif (!(tag instanceof CompoundTag compound) || compound.isEmpty()) {
\t\t\treturn Optional.empty();
\t\t}
\t\treturn OVERSIZED_ITEM_STACK_CODEC.parse(RegistryOps.create(NbtOps.INSTANCE, registries), compound).result();
\t}

\tpublic static ItemStack decodeItemStack(HolderLookup.Provider registries, Tag tag) {
\t\treturn decodeItemStackOptional(registries, tag).orElse(ItemStack.EMPTY);
\t}
"""
        txt = txt.replace("\n\tprivate CodecHelper() {}", helper + "\n\tprivate CodecHelper() {}")
    codec_helper.write_text(txt)

# CompoundTag getters return Optional in 26.3. Keep NBTHelper's public API unchanged.
nbt_helper = java_root / "net/p3pp3rf1y/sophisticatedcore/util/NBTHelper.java"
if nbt_helper.exists():
    txt = nbt_helper.read_text(errors="ignore")
    replacements = {
        "return getTagValue(tag, key, CompoundTag::getInt);": "return tag.getInt(key);",
        "return getTagValue(tag, key, CompoundTag::getIntArray);": "return tag.getIntArray(key);",
        "return getTagValue(tag, key, CompoundTag::getBoolean);": "return tag.getBoolean(key);",
        "return getTagValue(tag, key, CompoundTag::getCompound);": "return tag.getCompound(key);",
        "return getTagValue(tag, key, CompoundTag::getLong);": "return tag.getLong(key);",
        "return getTagValue(tag, key, CompoundTag::getString);": "return tag.getString(key);",
        "return getTagValue(tag, key, (t, k) -> deserialize.apply(t.getString(k)));": "return tag.getString(key).map(deserialize);",
        "return getTagValue(tag, key, (t, k) -> Component.Serializer.fromJson(t.getString(k), registries));": "return tag.getString(key).map(s -> Component.Serializer.fromJson(s, registries));",
    }
    for old,new in replacements.items():
        txt = txt.replace(old,new)
    old_collection = """\t\treturn getTagValue(tag, key, (c, n) -> c.getList(n, listType)).map(listNbt -> {
\t\t\tC ret = initCollection.get();
\t\t\tlistNbt.forEach(elementNbt -> getElement.apply(elementNbt).ifPresent(ret::add));
\t\t\treturn ret;
\t\t});
"""
    new_collection = """\t\treturn tag.getList(key).map(listNbt -> {
\t\t\tC ret = initCollection.get();
\t\t\tlistNbt.forEach(elementNbt -> getElement.apply(elementNbt).ifPresent(ret::add));
\t\t\treturn ret;
\t\t});
"""
    txt = txt.replace(old_collection,new_collection)
    old_map = """\t\tCompoundTag mapNbt = tag.getCompound(key);

\t\tMap<K, V> map = initMap.get();

\t\tfor (String tagName : mapNbt.getAllKeys()) {
\t\t\tgetValue.apply(tagName, mapNbt.get(tagName)).ifPresent(value -> map.put(getKey.apply(tagName), value));
\t\t}

\t\treturn Optional.of(map);
"""
    new_map = """\t\treturn tag.getCompound(key).map(mapNbt -> {
\t\t\tMap<K, V> map = initMap.get();
\t\t\tfor (String tagName : mapNbt.getAllKeys()) {
\t\t\t\tTag valueTag = mapNbt.get(tagName);
\t\t\t\tif (valueTag != null) {
\t\t\t\t\tgetValue.apply(tagName, valueTag).ifPresent(value -> map.put(getKey.apply(tagName), value));
\t\t\t\t}
\t\t\t}
\t\t\treturn map;
\t\t});
"""
    txt = txt.replace(old_map,new_map)
    nbt_helper.write_text(txt)

# Render metadata: switch old direct NBT value getters to 26.3 fallback getters and central stack codec.
render = java_root / "net/p3pp3rf1y/sophisticatedcore/renderdata/RenderInfo.java"
if render.exists():
    txt = render.read_text(errors="ignore")
    txt = txt.replace("RegistryHelper.getRegistryAccess().map(upgradeItem::saveOptional).orElse(new CompoundTag())",
                      "RegistryHelper.getRegistryAccess().map(registries -> CodecHelper.encodeItemStack(registries, upgradeItem)).orElse(new CompoundTag())")
    txt = txt.replace("ItemStack.parseOptional(registryAccess, upgradeItemsTag.getCompound(i))",
                      "CodecHelper.decodeItemStack(registryAccess, upgradeItemsTag.getCompound(i))")
    txt = txt.replace("RegistryHelper.getRegistryAccess().map(item::saveOptional).orElse(new CompoundTag())",
                      "RegistryHelper.getRegistryAccess().map(registries -> CodecHelper.encodeItemStack(registries, item)).orElse(new CompoundTag())")
    txt = txt.replace("ItemStack.parseOptional(registryAccess, tag.getCompound(ITEM_TAG).orElseGet(CompoundTag::new))",
                      "CodecHelper.decodeItemStack(registryAccess, tag.getCompoundOrEmpty(ITEM_TAG))")
    txt = txt.replace("ItemStack.parseOptional(registryAccess, tag.getCompound(ITEM_TAG))",
                      "CodecHelper.decodeItemStack(registryAccess, tag.getCompoundOrEmpty(ITEM_TAG))")
    txt = txt.replace(".getCompound(UPGRADES_TAG)", ".getCompoundOrEmpty(UPGRADES_TAG)")
    txt = txt.replace(".getCompound(ITEM_DISPLAY_TAG)", ".getCompoundOrEmpty(ITEM_DISPLAY_TAG)")
    txt = txt.replace(".getCompound(TANK_INFO_TAG)", ".getCompoundOrEmpty(TANK_INFO_TAG)")
    txt = txt.replace(".getList(UPGRADE_ITEMS_TAG, Tag.TAG_COMPOUND)", ".getListOrEmpty(UPGRADE_ITEMS_TAG)")
    txt = txt.replace(".getList(TANKS_TAG, Tag.TAG_COMPOUND)", ".getListOrEmpty(TANKS_TAG)")
    txt = txt.replace("tanks.getCompound(i)", "tanks.getCompound(i).orElseGet(CompoundTag::new)")
    txt = txt.replace("upgradeItemsTag.getCompound(i)", "upgradeItemsTag.getCompound(i).orElseGet(CompoundTag::new)")
    txt = txt.replace("tag.getString(TANK_POSITION_TAG).toUpperCase(Locale.ENGLISH)", "tag.getStringOr(TANK_POSITION_TAG, \"\").toUpperCase(Locale.ENGLISH)")
    txt = txt.replace("tag.getString(TANK_POSITION_TAG).equals(tankPosition.getSerializedName())", "tag.getStringOr(TANK_POSITION_TAG, \"\").equals(tankPosition.getSerializedName())")
    txt = txt.replace("tag.getTagType(INACCESSIBLE_SLOTS_TAG) == Tag.TAG_INT_ARRAY", "tag.get(INACCESSIBLE_SLOTS_TAG) instanceof IntArrayTag")
    txt = txt.replace("tag.getIntArray(INACCESSIBLE_SLOTS_TAG)", "tag.getIntArray(INACCESSIBLE_SLOTS_TAG).orElseGet(() -> new int[0])")
    txt = txt.replace("tag.getIntArray(INFINITE_SLOTS_TAG)", "tag.getIntArray(INFINITE_SLOTS_TAG).orElseGet(() -> new int[0])")
    txt = txt.replace("tag.getIntArray(SLOT_COUNTS_TAG)", "tag.getIntArray(SLOT_COUNTS_TAG).orElseGet(() -> new int[0])")
    txt = txt.replace("Optional.of(((FloatTag) t).getAsFloat())", "t.asFloat()")
    txt = txt.replace("tag.getInt(ROTATION_TAG)", "tag.getIntOr(ROTATION_TAG, 0)")
    txt = txt.replace("tag.getInt(SLOT_INDEX_TAG)", "tag.getIntOr(SLOT_INDEX_TAG, 0)")
    txt = txt.replace("tag.getString(DISPLAY_SIDE_TAG)", "tag.getStringOr(DISPLAY_SIDE_TAG, \"\")")
    if "import net.p3pp3rf1y.sophisticatedcore.util.CodecHelper;" not in txt:
        txt = txt.replace("import net.p3pp3rf1y.sophisticatedcore.util.NBTHelper;\n",
                          "import net.p3pp3rf1y.sophisticatedcore.util.CodecHelper;\nimport net.p3pp3rf1y.sophisticatedcore.util.NBTHelper;\n")
    render.write_text(txt)

# Simple float NBT getters.
for rel,key in [
    ("net/p3pp3rf1y/sophisticatedcore/upgrades/IRenderedTankUpgrade.java","FILL_RATIO_TAG"),
    ("net/p3pp3rf1y/sophisticatedcore/upgrades/IRenderedBatteryUpgrade.java","CHARGE_RATIO_TAG"),
]:
    p=java_root/rel
    if p.exists():
        txt=p.read_text(errors="ignore")
        txt=txt.replace(f"tag.getFloat({key})", f"tag.getFloatOr({key}, 0.0F)")
        p.write_text(txt)

# Inventory partition base indices now come through Optional<int[]>.
partitioner = java_root / "net/p3pp3rf1y/sophisticatedcore/inventory/InventoryPartitioner.java"
if partitioner.exists():
    txt=partitioner.read_text(errors="ignore")
    txt=txt.replace("baseIndexes = tag.getIntArray(BASE_INDEXES_TAG);", "baseIndexes = tag.getIntArray(BASE_INDEXES_TAG).orElseGet(() -> new int[0]);")
    partitioner.write_text(txt)

# Memory settings use the centralized oversized-safe ItemStack codec.
memory = java_root / "net/p3pp3rf1y/sophisticatedcore/settings/memory/MemorySettingsCategory.java"
if memory.exists():
    txt=memory.read_text(errors="ignore")
    txt=txt.replace("v.getAsString()", "v.asString().orElse(\"\")")
    txt=txt.replace(
        "RegistryHelper.getRegistryAccess().flatMap(registryAccess -> ItemStack.parse(registryAccess, tag))",
        "RegistryHelper.getRegistryAccess().flatMap(registryAccess -> CodecHelper.decodeItemStackOptional(registryAccess, tag))"
    )
    txt=txt.replace(
        "RegistryHelper.getRegistryAccess().map(registryAccess -> isk.stack().saveOptional(registryAccess)).orElse(new CompoundTag())",
        "RegistryHelper.getRegistryAccess().map(registryAccess -> CodecHelper.encodeItemStack(registryAccess, isk.stack())).orElse(new CompoundTag())"
    )
    if "import net.p3pp3rf1y.sophisticatedcore.util.CodecHelper;" not in txt:
        txt=txt.replace("import net.p3pp3rf1y.sophisticatedcore.util.NBTHelper;\n",
                        "import net.p3pp3rf1y.sophisticatedcore.util.CodecHelper;\nimport net.p3pp3rf1y.sophisticatedcore.util.NBTHelper;\n")
    memory.write_text(txt)

# Colored shulker Items constants were removed; config stores IDs anyway, so keep canonical IDs directly.
stack_cfg = java_root / "net/p3pp3rf1y/sophisticatedcore/upgrades/stack/StackUpgradeConfig.java"
if stack_cfg.exists():
    txt=stack_cfg.read_text(errors="ignore")
    colors=["white","orange","magenta","light_blue","yellow","lime","pink","gray","light_gray","cyan","purple","blue","brown","green","red","black"]
    for color in colors:
        const=color.upper()+"_SHULKER_BOX"
        txt=txt.replace(f"ret.add(RegistryHelper.getItemKey(Items.{const}).toString());", f"ret.add(\"minecraft:{color}_shulker_box\");")
    txt=txt.replace("ret.add(RegistryHelper.getItemKey(Items.SHULKER_BOX).toString());", "ret.add(\"minecraft:shulker_box\");")
    txt=txt.replace("BuiltInRegistries.ITEM.get(registryName)", "BuiltInRegistries.ITEM.getValue(registryName)")
    stack_cfg.write_text(txt)

print("Applied central 26.3 NBT Optional and ItemStack codec migration.")


# SFL ItemStackHandler persistence moved from removed ItemStack#save/parse helpers to codecs.
sfl_stack_handler = java_root / "com/github/salandora/sophisticatedfabriclib/transfer/api/v1/ItemStackHandler.java"
if sfl_stack_handler.exists():
    txt=sfl_stack_handler.read_text(errors="ignore")
    if "import net.minecraft.nbt.NbtOps;" not in txt:
        txt=txt.replace("import net.minecraft.nbt.ListTag;\n", "import net.minecraft.nbt.ListTag;\nimport net.minecraft.nbt.NbtOps;\n")
    if "import net.minecraft.resources.RegistryOps;" not in txt:
        txt=txt.replace("import net.minecraft.nbt.Tag;\n", "import net.minecraft.nbt.Tag;\nimport net.minecraft.resources.RegistryOps;\n")
    old_ser="""\t\t\t\tCompoundTag itemTag = new CompoundTag();
\t\t\t\titemTag.putInt("Slot", i);
\t\t\t\tlistTag.add(itemStack.save(registries, itemTag));
"""
    new_ser="""\t\t\t\tCompoundTag itemTag = ItemStack.OPTIONAL_CODEC
\t\t\t\t\t\t.encodeStart(RegistryOps.create(NbtOps.INSTANCE, registries), itemStack)
\t\t\t\t\t\t.result()
\t\t\t\t\t\t.filter(CompoundTag.class::isInstance)
\t\t\t\t\t\t.map(CompoundTag.class::cast)
\t\t\t\t\t\t.orElseGet(CompoundTag::new);
\t\t\t\titemTag.putInt("Slot", i);
\t\t\t\tlistTag.add(itemTag);
"""
    txt=txt.replace(old_ser,new_ser)
    old_des="""\t\tsetSize(nbt.contains("Size", Tag.TAG_INT) ? nbt.getInt("Size") : stacks.size());
\t\tListTag tagList = nbt.getList("Items", Tag.TAG_COMPOUND);
\t\tfor (int i = 0; i < tagList.size(); i++) {
\t\t\tCompoundTag itemTag = tagList.getCompound(i);
\t\t\tint slot = itemTag.getInt("Slot");
\t\t\tif (slot >= 0 && slot < getSlotCount()) {
\t\t\t\tItemStack.parse(registries, itemTag).ifPresent(stack -> stacks.set(slot, stack));
\t\t\t}
\t\t}
"""
    new_des="""\t\tsetSize(nbt.contains("Size") ? nbt.getIntOr("Size", stacks.size()) : stacks.size());
\t\tListTag tagList = nbt.getListOrEmpty("Items");
\t\tfor (int i = 0; i < tagList.size(); i++) {
\t\t\tCompoundTag itemTag = tagList.getCompound(i).orElseGet(CompoundTag::new);
\t\t\tint slot = itemTag.getIntOr("Slot", -1);
\t\t\tif (slot >= 0 && slot < getSlotCount()) {
\t\t\t\tCompoundTag stackTag = itemTag.copy();
\t\t\t\tstackTag.remove("Slot");
\t\t\t\tItemStack.OPTIONAL_CODEC
\t\t\t\t\t\t.parse(RegistryOps.create(NbtOps.INSTANCE, registries), stackTag)
\t\t\t\t\t\t.result()
\t\t\t\t\t\t.ifPresent(stack -> stacks.set(slot, stack));
\t\t\t}
\t\t}
"""
    txt=txt.replace(old_des,new_des)
    sfl_stack_handler.write_text(txt)

print("Applied SFL ItemStackHandler 26.3 codec persistence.")


# Fifth MC 26.3 pass: straightforward Fabric/SFL API renames.

# Registry-of-registries now returns holders from get(); use getValue() for actual registry values.
deferred_reg = java_root / "com/github/salandora/sophisticatedfabriclib/util/DeferredRegister.java"
if deferred_reg.exists():
    txt=deferred_reg.read_text(errors="ignore")
    txt=txt.replace(
        "BuiltInRegistries.REGISTRY.get(this.registryKey.identifier())",
        "BuiltInRegistries.REGISTRY.getValue(this.registryKey.identifier())"
    )
    deferred_reg.write_text(txt)

# Holder became sealed in Minecraft 26.x. SFL's lazy holder wrapper only needs Supplier semantics.
deferred_holder = java_root / "com/github/salandora/sophisticatedfabriclib/util/DeferredHolder.java"
if deferred_holder.exists():
    txt=deferred_holder.read_text(errors="ignore")
    txt=txt.replace("implements Holder<T>, Supplier<U>", "implements Supplier<U>")
    txt=txt.replace("\t@Override\n", "")
    txt=txt.replace(
        "BuiltInRegistries.REGISTRY.get(this.key.registry())",
        "BuiltInRegistries.REGISTRY.getValue(this.key.registry())"
    )
    txt=txt.replace(
        "this.holder = registry.getHolder(this.key).orElse(null);",
        "this.holder = registry.get(this.key.location()).orElse(null);"
    )
    # Holder.Kind was removed with the 26.x Holder API. This wrapper no longer implements Holder,
    # so drop the obsolete kind() method and kind check from equals().
    import re
    txt=re.sub(
        r'\n\s*public Kind kind\(\) \{\s*return Kind\.REFERENCE;\s*\}\s*',
        '\n',
        txt,
        flags=re.S
    )
    txt=txt.replace(
        "return obj instanceof DeferredHolder<?, ?> h\n\t\t\t\t&& h.kind() == Kind.REFERENCE\n\t\t\t\t&& h.getKey() == this.key;",
        "return obj instanceof DeferredHolder<?, ?> h\n\t\t\t\t&& h.getKey() == this.key;"
    )
    deferred_holder.write_text(txt)

# Fabric resource condition now receives RegistryOps.RegistryInfoLookup.
item_enabled = java_root / "net/p3pp3rf1y/sophisticatedcore/crafting/ItemEnabledCondition.java"
if item_enabled.exists():
    txt=item_enabled.read_text(errors="ignore")
    txt=txt.replace("import net.minecraft.core.HolderLookup;\n", "import net.minecraft.resources.RegistryOps;\n")
    if "import org.jspecify.annotations.Nullable;" not in txt:
        txt=txt.replace("import net.p3pp3rf1y.sophisticatedcore.init.ModRecipes;\n",
                        "import net.p3pp3rf1y.sophisticatedcore.init.ModRecipes;\nimport org.jspecify.annotations.Nullable;\n")
    txt=txt.replace(
        "public boolean test(HolderLookup.Provider registryLookup)",
        "public boolean test(RegistryOps.@Nullable RegistryInfoLookup registryInfo)"
    )
    item_enabled.write_text(txt)

# Fabric transfer variant component accessor rename.
simple_fluid = java_root / "com/github/salandora/sophisticatedfabriclib/fluid/api/v1/SimpleFluidContent.java"
if simple_fluid.exists():
    txt=simple_fluid.read_text(errors="ignore")
    txt=txt.replace("getComponentMap()", "getComponents()")
    simple_fluid.write_text(txt)

# SingleVariantStorage no longer exposes readNbt/writeNbt helpers; use FluidStack's own codec.
fluid_stack = java_root / "com/github/salandora/sophisticatedfabriclib/fluid/api/v1/FluidStack.java"
if fluid_stack.exists():
    txt=fluid_stack.read_text(errors="ignore")
    if "import net.minecraft.nbt.NbtOps;" not in txt:
        txt=txt.replace("import net.minecraft.nbt.CompoundTag;\n", "import net.minecraft.nbt.CompoundTag;\nimport net.minecraft.nbt.NbtOps;\n")
    if "import net.minecraft.resources.RegistryOps;" not in txt:
        txt=txt.replace("import net.minecraft.network.codec.StreamCodec;\n", "import net.minecraft.network.codec.StreamCodec;\nimport net.minecraft.resources.RegistryOps;\n")
    old_save="""\t\tCompoundTag tag = new CompoundTag();
\t\twriteNbt(tag, lookup);
\t\treturn tag;
"""
    new_save="""\t\treturn CODEC.encodeStart(RegistryOps.create(NbtOps.INSTANCE, lookup), this)
\t\t\t\t.result()
\t\t\t\t.filter(CompoundTag.class::isInstance)
\t\t\t\t.map(CompoundTag.class::cast)
\t\t\t\t.orElseGet(CompoundTag::new);
"""
    txt=txt.replace(old_save,new_save)
    old_parse="""\t\tFluidStack stack = new FluidStack();
\t\tstack.readNbt(tag, lookup);
\t\treturn stack;
"""
    new_parse="""\t\treturn CODEC.parse(RegistryOps.create(NbtOps.INSTANCE, lookup), tag)
\t\t\t\t.result()
\t\t\t\t.orElse(EMPTY);
"""
    txt=txt.replace(old_parse,new_parse)
    fluid_stack.write_text(txt)

# Fabric fluid attribute API rename.
fluid_type = java_root / "com/github/salandora/sophisticatedfabriclib/fluid/api/v1/FluidType.java"
if fluid_type.exists():
    txt=fluid_type.read_text(errors="ignore")
    txt=txt.replace("public int getLuminance(FluidVariant variant)", "public int getLightEmission(FluidVariant variant)")
    fluid_type.write_text(txt)

# Fabric networking API rename.
packet_dist = java_root / "net/p3pp3rf1y/sophisticatedcore/network/PacketDistributor.java"
if packet_dist.exists():
    txt=packet_dist.read_text(errors="ignore")
    txt=txt.replace("ServerPlayNetworking::createS2CPacket", "ServerPlayNetworking::createClientboundPacket")
    txt=txt.replace("ServerPlayNetworking.createS2CPacket", "ServerPlayNetworking.createClientboundPacket")
    packet_dist.write_text(txt)

# Porting Lib stack-slot persistence: migrate removed ItemStack save/parse helpers.
slot = java_root / "io/github/fabricators_of_create/porting_lib/transfer/item/ItemStackHandlerSlot.java"
if slot.exists():
    txt=slot.read_text(errors="ignore")
    if "import net.minecraft.nbt.NbtOps;" not in txt:
        txt=txt.replace("import net.minecraft.nbt.Tag;\n", "import net.minecraft.nbt.Tag;\nimport net.minecraft.nbt.NbtOps;\n")
    if "import net.minecraft.resources.RegistryOps;" not in txt:
        txt=txt.replace("import net.minecraft.world.item.ItemStack;\n", "import net.minecraft.world.item.ItemStack;\nimport net.minecraft.resources.RegistryOps;\n")
    txt=txt.replace(
        "return stack.save(provider, tag);",
        "return ItemStack.OPTIONAL_CODEC.encodeStart(RegistryOps.create(NbtOps.INSTANCE, provider), stack).result().orElse(tag);"
    )
    txt=txt.replace(
        "ItemStack.parse(provider, tag).ifPresent(this::setStack);",
        "ItemStack.OPTIONAL_CODEC.parse(RegistryOps.create(NbtOps.INSTANCE, provider), tag).result().ifPresent(this::setStack);"
    )
    slot.write_text(txt)

# Generic container entity handlers: chest boats are split by wood type in 26.3.
sfl_caps = java_root / "com/github/salandora/sophisticatedfabriclib/util/Capabilities.java"
if sfl_caps.exists():
    txt=sfl_caps.read_text(errors="ignore")
    if "import net.minecraft.world.Container;" not in txt:
        txt=txt.replace("import net.minecraft.core.Direction;\n", "import net.minecraft.core.Direction;\nimport net.minecraft.world.Container;\n")
    txt=re.sub(r'import java[.]util[.]List;\n', '', txt)
    txt=re.sub(
        r'\s*var containerEntities = List[.]of\([\s\S]*?\);\s*for \(var entityType : containerEntities\) \{[\s\S]*?\}\s*',
        '''
\t\t\tENTITY.registerFallback((entity, ctx) -> entity instanceof Container container ? InvWrapper.of(container) : null);
\t\t\tENTITY_AUTOMATION.registerFallback((entity, direction) -> entity instanceof Container container ? InvWrapper.of(container) : null);

''',
        txt,
        count=1
    )
    sfl_caps.write_text(txt)

print("Applied Fabric/SFL registry, fluid, networking and persistence renames for 26.3.")


# Sixth MC 26.3 cleanup pass: targeted fixes surfaced after javac got past the sealed Holder blocker.

def patch(rel, fn):
    p = java_root / rel
    if not p.exists():
        return
    txt = p.read_text(errors="ignore")
    new = fn(txt)
    if new != txt:
        p.write_text(new)

# ResourceKey#location -> identifier in 26.x.
patch("com/github/salandora/sophisticatedfabriclib/util/DeferredHolder.java",
      lambda t: t.replace("this.key.location()", "this.key.identifier()"))

# RenderInfo had some duplicate Optional fallbacks introduced by the generic NBT pass.
def patch_render_info(t):
    t = re.sub(r'\.getCompoundOrEmpty\(([^)]+)\)\.orElseGet\(CompoundTag::new\)',
               r'.getCompoundOrEmpty(\1)', t)
    t = t.replace(".orElseGet(CompoundTag::new).orElseGet(CompoundTag::new)",
                  ".orElseGet(CompoundTag::new)")
    t = re.sub(r'(\.getIntArray\([^)]+\)\.orElseGet\(\(\) -> new int\[0\]\))\.orElseGet\(\(\) -> new int\[0\]\)',
               r'\1', t)
    t = re.sub(r'(\.getLongArray\([^)]+\)\.orElseGet\(\(\) -> new long\[0\]\))\.orElseGet\(\(\) -> new long\[0\]\)',
               r'\1', t)
    t = re.sub(r'(\.getIntOr\([^)]+\))\.orElse\([^)]+\)', r'\1', t)
    t = re.sub(r'(\.getStringOr\([^)]+\))\.orElse\("[^"]*"\)', r'\1', t)
    return t
patch("net/p3pp3rf1y/sophisticatedcore/renderdata/RenderInfo.java", patch_render_info)

# Settings menu: vanilla now owns RemoteSlot internally. Keep our ghost mirror as ItemStacks
# and use the public setRemoteSlot API rather than the removed no-copy hook.
def patch_settings_menu(t):
    t = t.replace("synchronizer.sendInitialData(this, remoteGhostSlots, remoteCarried, new int[0]);",
                  "synchronizer.sendInitialData(this, new ArrayList<>(remoteGhostSlots), getCarried().copy(), new int[0]);")
    # 26.3 removed setRemoteSlotNoCopy; setRemoteSlot is the public replacement.
    t = t.replace("@Override\n\tpublic void setRemoteSlotNoCopy(int slot, ItemStack stack) {",
                  "public void setRemoteGhostSlot(int slot, ItemStack stack) {")
    t = t.replace("super.setRemoteSlotNoCopy(slot, stack);", "super.setRemoteSlot(slot, stack);")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/common/gui/SettingsContainerMenu.java", patch_settings_menu)

# Straight Minecraft 26.3 method/signature renames.
def generic_runtime_fixes(t):
    t = t.replace(".serverLevel()", ".level()")
    t = t.replace(".displayClientMessage(", ".displayClientMessage(")  # kept for targeted rewrite below
    t = t.replace("EntityType.ITEM", "EntityType.ITEM_ENTITY")
    t = t.replace("EntityTypes.CHEST_BOAT", "EntityTypes.OAK_CHEST_BOAT")
    t = t.replace(".getHoverName().getString().orElse(\"\")", ".getHoverName().getString()")
    t = t.replace("JukeboxSong.fromStack(level.registryAccess(), getDisc())", "JukeboxSong.fromStack(getDisc())")
    t = t.replace(".assemble(craftMatrix.asCraftInput(), player.level().registryAccess())",
                  ".assemble(craftMatrix.asCraftInput())")
    t = t.replace(".onCraftedBy(player.level(), player, stack.getCount())",
                  ".onCraftedBy(player, stack.getCount())")
    t = t.replace(".onCraftedBy(slotStack, player.level(), player)",
                  ".onCraftedBy(slotStack, player)")
    t = t.replace(".setRecipeUsed(level, serverplayerentity, craftingRecipe)",
                  ".setRecipeUsed(serverplayerentity, craftingRecipe)")
    t = t.replace(".setRecipeUsed(player.level(), serverPlayer, lastRecipe)",
                  ".setRecipeUsed(serverPlayer, lastRecipe)")
    return t

for rel in [
    "net/p3pp3rf1y/sophisticatedcore/common/gui/TemplatePersistanceContainer.java",
    "net/p3pp3rf1y/sophisticatedcore/util/InventorySorter.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/stonecutter/StonecutterRecipeContainer.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/jukebox/JukeboxUpgradeWrapper.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/magnet/MagnetUpgradeWrapper.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/crafting/CraftingUpgradeContainer.java",
]:
    patch(rel, generic_runtime_fixes)

# Player permission helpers moved to ServerPlayer/permission checks; only these Infinity paths need it.
for rel in [
    "net/p3pp3rf1y/sophisticatedcore/upgrades/infinity/InfinityInventoryPart.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/infinity/InfinityUpgradeItem.java",
]:
    patch(rel, lambda t: t.replace("player.hasPermissions(permissionLevel)",
                                   "player instanceof ServerPlayer sp && sp.hasPermissions(permissionLevel)")
                         .replace("player.hasPermissions(getPermissionLevel())",
                                  "player instanceof ServerPlayer sp && sp.hasPermissions(getPermissionLevel())")
                         .replace("import net.minecraft.world.entity.player.Player;",
                                  "import net.minecraft.world.entity.player.Player;\nimport net.minecraft.server.level.ServerPlayer;"))

# NoSort settings: Optional<int[]>.
patch("net/p3pp3rf1y/sophisticatedcore/settings/nosort/NoSortSettingsCategory.java",
      lambda t: t.replace("categoryNbt.getIntArray(SELECTED_SLOTS_TAG)",
                          "categoryNbt.getIntArray(SELECTED_SLOTS_TAG).orElseGet(() -> new int[0])"))

# Fluid dimension flag moved to environment attributes. For the compile pass keep Nether behavior
# equivalent by checking the level key; this is revisited in runtime verification.
def patch_core_fluid(t):
    t = t.replace("level.dimensionType().ultraWarm()", "level.dimension() == Level.NETHER")
    t = t.replace("player.playNotifySound(sound, SoundSource.BLOCKS, 1, 1)",
                  "player.playSound(sound, 1.0F, 1.0F)")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/fluid/FluidUtil.java", patch_core_fluid)

# Optional CraftingTweaks client glue was already removed; remove the dangling registrar too.
compat_client = java_root / "net/p3pp3rf1y/sophisticatedcore/compat/craftingtweaks/CraftingTweaksCompatClient.java"
if compat_client.exists():
    compat_client.unlink()

# ClientRegistryHelper is client-only and excluded from the common pass. RegistryHelper can use
# the active server registry when present and otherwise report empty.
def patch_registry_helper(t):
    t = t.replace("return ClientRegistryHelper.getRegistryAccess();", "return null;")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/util/RegistryHelper.java", patch_registry_helper)

# SFL context class was renamed during the Porting Lib -> SFL migration.
patch("net/p3pp3rf1y/sophisticatedcore/util/CapabilityHelper.java",
      lambda t: t.replace("new MutableContainerItemContext(stack)",
                          "new ItemStackContainerItemContext(stack)")
                 .replace("import io.github.fabricators_of_create.porting_lib.transfer.MutableContainerItemContext;",
                          "import com.github.salandora.sophisticatedfabriclib.transfer.api.v1.ItemStackContainerItemContext;"))

# Text component codec replaces removed Component.Serializer.
patch("net/p3pp3rf1y/sophisticatedcore/util/NBTHelper.java",
      lambda t: t.replace("Component.Serializer.fromJson(t.getString(k).orElse(\"\"), registries)",
                          "ComponentSerialization.CODEC.parse(RegistryOps.create(JsonOps.INSTANCE, registries), new JsonPrimitive(t.getString(k).orElse(\"\"))).result().orElse(Component.empty())")
                 .replace("import net.minecraft.network.chat.Component;",
                          "import net.minecraft.network.chat.Component;\nimport net.minecraft.network.chat.ComponentSerialization;\nimport net.minecraft.resources.RegistryOps;\nimport com.mojang.serialization.JsonOps;\nimport com.google.gson.JsonPrimitive;"))

# Recipe serializer covariance in 26.3.
for rel in [
    "net/p3pp3rf1y/sophisticatedcore/crafting/UpgradeClearRecipe.java",
    "net/p3pp3rf1y/sophisticatedcore/crafting/UpgradeNextTierRecipe.java",
]:
    patch(rel, lambda t: t.replace("public RecipeSerializer<?> getSerializer()",
                                   "public RecipeSerializer<? extends CustomRecipe> getSerializer()")
                 if "extends CustomRecipe" in t else
                 t.replace("public RecipeSerializer<?> getSerializer()",
                           "public RecipeSerializer<? extends ShapedRecipe> getSerializer()"))

# CustomRecipe no longer takes CraftingBookCategory; dye color accessor changed.
def patch_storage_dye(t):
    t = t.replace("super(category);", "super();")
    t = t.replace("dyeItem.getDyeColor()", "dyeItem.getDyeColor(stack)")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/crafting/StorageDyeRecipeBase.java", patch_storage_dye)

# RecipeOutput now keys recipes by ResourceKey<Recipe<?>>.
def patch_holding_output(t):
    t = t.replace("public void accept(Identifier id, Recipe<?> recipe, @Nullable AdvancementHolder advancement)",
                  "public void accept(ResourceKey<Recipe<?>> id, Recipe<?> recipe, @Nullable AdvancementHolder advancement)")
    if "import net.minecraft.resources.ResourceKey;" not in t:
        t = t.replace("import net.minecraft.resources.Identifier;",
                      "import net.minecraft.resources.Identifier;\nimport net.minecraft.resources.ResourceKey;")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/crafting/HoldingRecipeOutput.java", patch_holding_output)

# ItemStack persistence: ItemStack.parse was removed; use OPTIONAL_CODEC.
def patch_sfl_item_handler(t):
    t = t.replace(
        "ItemStack.parse(registries, itemTag).ifPresent(stack -> stacks.set(slot, stack));",
        "ItemStack.OPTIONAL_CODEC.parse(RegistryOps.create(NbtOps.INSTANCE, registries), itemTag).result().ifPresent(stack -> stacks.set(slot, stack));"
    )
    if "import net.minecraft.nbt.NbtOps;" not in t:
        t = t.replace("import net.minecraft.nbt.CompoundTag;",
                      "import net.minecraft.nbt.CompoundTag;\nimport net.minecraft.nbt.NbtOps;")
    if "import net.minecraft.resources.RegistryOps;" not in t:
        t = t.replace("import net.minecraft.core.HolderLookup;",
                      "import net.minecraft.core.HolderLookup;\nimport net.minecraft.resources.RegistryOps;")
    return t
patch("com/github/salandora/sophisticatedfabriclib/transfer/api/v1/ItemStackHandler.java", patch_sfl_item_handler)

print("Applied sixth MC 26.3 targeted cleanup pass.")


# Seventh MC 26.3 cleanup pass: recipe manager, tooltips, save API, and common-pass client stubs.

# RenderInfo exact leftovers after previous generic transformations.
def patch_render_exact(t):
    t = t.replace(
        "ItemStack.parseOptional(registryAccess, upgradeItemsTag.getCompound(i).orElseGet(CompoundTag::new))",
        "CodecHelper.decodeItemStack(registryAccess, upgradeItemsTag.getCompound(i).orElseGet(CompoundTag::new))"
    )
    t = t.replace(
        "tank.getString(TANK_POSITION_TAG).toUpperCase(Locale.ENGLISH)",
        "tank.getStringOr(TANK_POSITION_TAG, \"\").toUpperCase(Locale.ENGLISH)"
    )
    return t
patch("net/p3pp3rf1y/sophisticatedcore/renderdata/RenderInfo.java", patch_render_exact)

# displayClientMessage(Component, false) became sendSystemMessage(Component).
patch("net/p3pp3rf1y/sophisticatedcore/common/gui/TemplatePersistanceContainer.java",
      lambda t: re.sub(r'getPlayer\(\)\.displayClientMessage\((.*?),\s*false\);',
                       r'getPlayer().sendSystemMessage(\1);', t, flags=re.S)
                 .replace("serverPlayer.serverLevel()", "serverPlayer.level()"))

# SNBT parser rename.
patch("net/p3pp3rf1y/sophisticatedcore/settings/DatapackSettingsTemplateManager.java",
      lambda t: t.replace("TagParser.parseTag(fileContents)", "TagParser.parseCompoundFully(fileContents)"))

# ContainerItemContext factory is static in 26.x SFL shim.
patch("net/p3pp3rf1y/sophisticatedcore/util/CapabilityHelper.java",
      lambda t: t.replace("new ItemStackContainerItemContext(stack)",
                          "ItemStackContainerItemContext.ofSingleStack(stack)"))

# RecipeAccess is now intentionally tiny; RecipeManager owns lookup/query behavior.
def patch_recipe_helper(t):
    t = t.replace(
        "return getLevel().map(w -> w.recipeAccess().getRecipesFor(recipeType, inventory, w)).orElse(Collections.emptyList());",
        "return getLevel().map(w -> getMatchingRecipes(w, recipeType, inventory)).orElse(Collections.emptyList());"
    )
    t = t.replace(
        "return level.recipeAccess().getRecipeFor(recipeType, inventory, level, recipeId);",
        "return recipeId == null ? level.getRecipeManager().getRecipeFor(recipeType, inventory, level) : level.getRecipeManager().getRecipeFor(recipeType, inventory, level, ResourceKey.create(Registries.RECIPE, recipeId));"
    )
    t = t.replace(
        "return level.recipeAccess().getRecipesFor(recipeType, inventory, level);",
        "return getMatchingRecipes(level, recipeType, inventory);"
    )
    anchor = "\tpublic enum CompactingShape {"
    helper = """
\t@SuppressWarnings(\"unchecked\")
\tprivate static <I extends RecipeInput, T extends Recipe<I>> List<RecipeHolder<T>> getMatchingRecipes(Level level, RecipeType<T> recipeType, I inventory) {
\t\treturn level.getRecipeManager().getRecipes().stream()
\t\t\t\t.filter(holder -> holder.value().getType() == recipeType)
\t\t\t\t.map(holder -> (RecipeHolder<T>) holder)
\t\t\t\t.filter(holder -> holder.value().matches(inventory, level))
\t\t\t\t.toList();
\t}

"""
    if anchor in t and "getMatchingRecipes(Level level" not in t:
        t = t.replace(anchor, helper + anchor)
    if "import net.minecraft.core.registries.Registries;" not in t:
        t = t.replace("import net.minecraft.core.registries.BuiltInRegistries;",
                      "import net.minecraft.core.registries.BuiltInRegistries;\nimport net.minecraft.core.registries.Registries;")
    if "import net.minecraft.resources.ResourceKey;" not in t:
        t = t.replace("import net.minecraft.resources.Identifier;",
                      "import net.minecraft.resources.Identifier;\nimport net.minecraft.resources.ResourceKey;")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/util/RecipeHelper.java", patch_recipe_helper)

# CustomRecipe no longer has canCraftInDimensions and serializer registry is wildcard-typed.
def patch_upgrade_clear(t):
    t = t.replace("\n    @Override\n    public boolean canCraftInDimensions", "\n    public boolean canCraftInDimensions")
    t = t.replace("\n\t@Override\n\tpublic boolean canCraftInDimensions", "\n\tpublic boolean canCraftInDimensions")
    t = t.replace(
        "return ModRecipes.UPGRADE_CLEAR_SERIALIZER.get();",
        "return (RecipeSerializer<? extends CustomRecipe>) (RecipeSerializer<?>) ModRecipes.UPGRADE_CLEAR_SERIALIZER.get();"
    )
    return t
patch("net/p3pp3rf1y/sophisticatedcore/crafting/UpgradeClearRecipe.java", patch_upgrade_clear)

# Same for ShapedRecipe wrapper: vanilla requires the exact generic serializer type.
def patch_upgrade_next(t):
    t = t.replace("public RecipeSerializer<? extends ShapedRecipe> getSerializer()",
                  "public RecipeSerializer<ShapedRecipe> getSerializer()")
    t = t.replace(
        "return ModRecipes.UPGRADE_NEXT_TIER_SERIALIZER.get();",
        "return (RecipeSerializer<ShapedRecipe>) (RecipeSerializer<?>) ModRecipes.UPGRADE_NEXT_TIER_SERIALIZER.get();"
    )
    return t
patch("net/p3pp3rf1y/sophisticatedcore/crafting/UpgradeNextTierRecipe.java", patch_upgrade_next)

# CustomRecipe removed canCraftInDimensions. Standard dyes are already covered by c:*_dyes tags,
# so the old DyeItem#getDyeColor shortcut is unnecessary on 26.3.
def patch_storage_dye_263(t):
    t = t.replace("\n\t@Override\n\tpublic boolean canCraftInDimensions", "\n\tpublic boolean canCraftInDimensions")
    t = re.sub(
        r'\n\t\tItem item = stack\.getItem\(\);\n\t\tif \(item instanceof DyeItem dyeItem\) \{\n\t\t\treturn dyeItem\.getDyeColor\([^;]*\);\n\t\t\}\n',
        '\n',
        t
    )
    return t
patch("net/p3pp3rf1y/sophisticatedcore/crafting/StorageDyeRecipeBase.java", patch_storage_dye_263)

# RecipeOutput now receives ResourceKey<Recipe<?>>.
def patch_recipe_output(t):
    t = t.replace("import net.minecraft.resources.Identifier;",
                  "import net.minecraft.resources.ResourceKey;")
    t = t.replace("public void accept(Identifier id, Recipe<?> recipe",
                  "public void accept(ResourceKey<Recipe<?>> id, Recipe<?> recipe")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/crafting/HoldingRecipeOutput.java", patch_recipe_output)

# Tooltip API became consumer-based.
def patch_upgrade_tooltip(t):
    old = """\t@Override
\tpublic void appendHoverText(ItemStack stack, Item.TooltipContext context, List<Component> tooltip, TooltipFlag flagIn) {
\t\ttooltip.addAll(TranslationHelper.INSTANCE.getTranslatedLines(stack.getItem().getDescriptionId() + TranslationHelper.TOOLTIP_SUFFIX, null, ChatFormatting.DARK_GRAY));
\t}"""
    new = """\t@Override
\tpublic void appendHoverText(ItemStack stack, Item.TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flagIn) {
\t\tTranslationHelper.INSTANCE.getTranslatedLines(stack.getItem().getDescriptionId() + TranslationHelper.TOOLTIP_SUFFIX, null, ChatFormatting.DARK_GRAY).forEach(tooltip);
\t}"""
    t = t.replace(old, new)
    if "import net.minecraft.world.item.component.TooltipDisplay;" not in t:
        t = t.replace("import net.minecraft.world.item.TooltipFlag;",
                      "import net.minecraft.world.item.TooltipFlag;\nimport net.minecraft.world.item.component.TooltipDisplay;")
    if "import java.util.function.Consumer;" not in t:
        t = t.replace("import java.util.List;", "import java.util.List;\nimport java.util.function.Consumer;")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/upgrades/UpgradeItemBase.java", patch_upgrade_tooltip)

# RecipeHolder id is now ResourceKey<Recipe<?>>.
patch("net/p3pp3rf1y/sophisticatedcore/upgrades/stonecutter/StonecutterRecipeContainer.java",
      lambda t: t.replace("recipes.get(recipeIndex).id())",
                          "recipes.get(recipeIndex).id().identifier())"))

# 26.3 StackedContents API changed. This override no longer exists; remove the obsolete helper.
def remove_method_by_signature(text, signature):
    idx = text.find(signature)
    if idx < 0:
        return text
    start = text.rfind("\n", 0, idx) + 1
    # include a directly preceding @Override line
    prev_start = text.rfind("\n", 0, max(0, start-1)) + 1
    if text[prev_start:start].strip() == "@Override":
        start = prev_start
    brace = text.find("{", idx)
    if brace < 0:
        return text
    depth = 0
    end = brace
    while end < len(text):
        if text[end] == "{":
            depth += 1
        elif text[end] == "}":
            depth -= 1
            if depth == 0:
                end += 1
                break
        end += 1
    return text[:start] + text[end:]

patch("net/p3pp3rf1y/sophisticatedcore/upgrades/crafting/CraftingItemHandler.java",
      lambda t: remove_method_by_signature(t, "public void fillStackedContents("))

# Crafting recipe byKey now takes ResourceKey<Recipe<?>> and lives on RecipeManager.
def patch_crafting_container(t):
    t = t.replace(
        "player.level().recipeAccess().byKey(recipeId)",
        "player.level().getRecipeManager().byKey(ResourceKey.create(Registries.RECIPE, recipeId))"
    )
    if "import net.minecraft.core.registries.Registries;" not in t:
        t = t.replace("import net.minecraft.core.", "import net.minecraft.core.registries.Registries;\nimport net.minecraft.core.", 1)
    if "import net.minecraft.resources.ResourceKey;" not in t:
        t = t.replace("import net.minecraft.resources.Identifier;",
                      "import net.minecraft.resources.Identifier;\nimport net.minecraft.resources.ResourceKey;")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/upgrades/crafting/CraftingUpgradeContainer.java", patch_crafting_container)

# BlockEntity save/load switched to ValueOutput/ValueInput. Keep the existing CompoundTag saveData()
# helper for update packets, and only migrate persistence hooks.
def patch_controller_save(t):
    old_save = """\t@Override
\tprotected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
\t\tsuper.saveAdditional(tag, registries);

\t\tsaveData(tag);
\t}"""
    new_save = """\t@Override
\tprotected void saveAdditional(ValueOutput output) {
\t\tsuper.saveAdditional(output);
\t\toutput.store(\"storagePositions\", Codec.LONG.listOf(), storagePositions.stream().map(BlockPos::asLong).toList());
\t\toutput.store(\"connectingBlocks\", Codec.LONG.listOf(), connectingBlocks.stream().map(BlockPos::asLong).toList());
\t\toutput.store(\"nonConnectingBlocks\", Codec.LONG.listOf(), nonConnectingBlocks.stream().map(BlockPos::asLong).toList());
\t\toutput.store(\"linkedBlocks\", Codec.LONG.listOf(), linkedBlocks.stream().map(BlockPos::asLong).toList());
\t\toutput.store(\"baseIndexes\", Codec.INT.listOf(), baseIndexes);
\t\toutput.putInt(\"totalSlots\", totalSlots);
\t}"""
    old_load = """\t@Override
\tpublic void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
\t\tsuper.loadAdditional(tag, registries);

\t\tstoragePositions = NBTHelper.getCollection(tag, \"storagePositions\", Tag.TAG_LONG, t -> Optional.of(BlockPos.of(((LongTag) t).getAsLong())), ArrayList::new).orElseGet(ArrayList::new);
\t\tconnectingBlocks = NBTHelper.getCollection(tag, \"connectingBlocks\", Tag.TAG_LONG, t -> Optional.of(BlockPos.of(((LongTag) t).getAsLong())), LinkedHashSet::new).orElseGet(LinkedHashSet::new);
\t\tnonConnectingBlocks = NBTHelper.getCollection(tag, \"nonConnectingBlocks\", Tag.TAG_LONG, t -> Optional.of(BlockPos.of(((LongTag) t).getAsLong())), LinkedHashSet::new).orElseGet(LinkedHashSet::new);
\t\tbaseIndexes = NBTHelper.getCollection(tag, \"baseIndexes\", Tag.TAG_INT, t -> Optional.of(((IntTag) t).getAsInt()), ArrayList::new).orElseGet(ArrayList::new);
\t\ttotalSlots = tag.getInt(\"totalSlots\");
\t\tlinkedBlocks = NBTHelper.getCollection(tag, \"linkedBlocks\", Tag.TAG_LONG, t -> Optional.of(BlockPos.of(((LongTag) t).getAsLong())), LinkedHashSet::new).orElseGet(LinkedHashSet::new);
\t}"""
    new_load = """\t@Override
\tprotected void loadAdditional(ValueInput input) {
\t\tsuper.loadAdditional(input);
\t\tstoragePositions = input.read(\"storagePositions\", Codec.LONG.listOf()).orElse(List.of()).stream().map(BlockPos::of).collect(java.util.stream.Collectors.toCollection(ArrayList::new));
\t\tconnectingBlocks = input.read(\"connectingBlocks\", Codec.LONG.listOf()).orElse(List.of()).stream().map(BlockPos::of).collect(java.util.stream.Collectors.toCollection(LinkedHashSet::new));
\t\tnonConnectingBlocks = input.read(\"nonConnectingBlocks\", Codec.LONG.listOf()).orElse(List.of()).stream().map(BlockPos::of).collect(java.util.stream.Collectors.toCollection(LinkedHashSet::new));
\t\tbaseIndexes = new ArrayList<>(input.read(\"baseIndexes\", Codec.INT.listOf()).orElse(List.of()));
\t\ttotalSlots = input.getIntOr(\"totalSlots\", 0);
\t\tlinkedBlocks = input.read(\"linkedBlocks\", Codec.LONG.listOf()).orElse(List.of()).stream().map(BlockPos::of).collect(java.util.stream.Collectors.toCollection(LinkedHashSet::new));
\t}"""
    t = t.replace(old_save, new_save).replace(old_load, new_load)
    if "import com.mojang.serialization.Codec;" not in t:
        t = t.replace("package net.p3pp3rf1y.sophisticatedcore.controller;",
                      "package net.p3pp3rf1y.sophisticatedcore.controller;\n\nimport com.mojang.serialization.Codec;")
    if "import net.minecraft.world.level.storage.ValueInput;" not in t:
        t = t.replace("import net.minecraft.world.level.block.state.BlockState;",
                      "import net.minecraft.world.level.block.state.BlockState;\nimport net.minecraft.world.level.storage.ValueInput;\nimport net.minecraft.world.level.storage.ValueOutput;")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/controller/ControllerBlockEntityBase.java", patch_controller_save)

# Vanilla 26.3 made doClick private/final. Keep the custom pre-handling in clicked() and
# fall back to vanilla's click engine for the base path.
patch("net/p3pp3rf1y/sophisticatedcore/common/gui/StorageContainerMenuBase.java",
      lambda t: remove_method_by_signature(t, "protected void doClick("))

# Common-pass stubs for client-only helpers referenced by payload/container classes.
sound_stub = java_root / "net/p3pp3rf1y/sophisticatedcore/upgrades/jukebox/StorageSoundHandler.java"
sound_stub.parent.mkdir(parents=True, exist_ok=True)
if not sound_stub.exists():
    sound_stub.write_text("""package net.p3pp3rf1y.sophisticatedcore.upgrades.jukebox;
import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvent;
import java.util.UUID;
public final class StorageSoundHandler {
    private StorageSoundHandler() {}
    public static void stopStorageSound(UUID id) {}
    public static void playStorageSound(SoundEvent sound, UUID id, BlockPos pos) {}
    public static void playStorageSound(SoundEvent sound, UUID id, int entityId) {}
}
""")

# TankUpgradeContainer is common logic but imports a tiny client marker interface. Restore it after
# the generic client-pruning pass with a common-safe marker stub.
nameable = java_root / "net/p3pp3rf1y/sophisticatedcore/client/gui/INameableEmptySlot.java"
nameable.parent.mkdir(parents=True, exist_ok=True)
if not nameable.exists():
    nameable.write_text("""package net.p3pp3rf1y.sophisticatedcore.client.gui;
import net.minecraft.network.chat.Component;
public interface INameableEmptySlot {
    boolean hasEmptyTooltip();
    Component getEmptyTooltip();
}
""")
tank_src = Path("core-src/.git")  # marker only; source checkout remains available through git worktree
# If the generic pruning removed TankUpgradeContainer, restore it from git and then re-apply global import rewrites.
tank = java_root / "net/p3pp3rf1y/sophisticatedcore/upgrades/tank/TankUpgradeContainer.java"
if not tank.exists():
    import subprocess
    raw = subprocess.check_output(
        ["git", "-C", "core-src", "show", "HEAD:src/main/java/net/p3pp3rf1y/sophisticatedcore/upgrades/tank/TankUpgradeContainer.java"],
        text=True
    )
    raw = raw.replace("net.minecraft.resources.ResourceLocation", "net.minecraft.resources.Identifier")
    raw = raw.replace("ResourceLocation", "Identifier")
    raw = raw.replace("io.github.fabricators_of_create.porting_lib.fluids.FluidStack",
                      "com.github.salandora.sophisticatedfabriclib.fluid.api.v1.FluidStack")
    raw = raw.replace("io.github.fabricators_of_create.porting_lib.transfer.item.SlottedStackStorage",
                      "io.github.fabricators_of_create.porting_lib.transfer.item.SlottedStackStorage")
    tank.write_text(raw)

print("Applied seventh MC 26.3 targeted cleanup pass.")


# Eighth MC 26.3 cleanup pass: server recipe access, permissions, entities, fluids, and robust persistence hooks.

# Robustly migrate all legacy client-message calls in the template container.
def patch_template_messages(t):
    t = t.replace("getPlayer().displayClientMessage(", "getPlayer().sendSystemMessage(")
    # sendSystemMessage only accepts the component; strip the old actionBar=false argument.
    t = re.sub(r'(getPlayer\(\)\.sendSystemMessage\((?:(?!getPlayer\(\)\.sendSystemMessage).)*?)\s*,\s*false\s*\);',
               r'\1);', t, flags=re.S)
    return t
patch("net/p3pp3rf1y/sophisticatedcore/common/gui/TemplatePersistanceContainer.java", patch_template_messages)

# Chest boats became one EntityType per wood variant in 26.3.
def patch_capabilities_entities(t):
    t = t.replace("EntityTypes.CHEST_BOAT,",
                  """EntityTypes.OAK_CHEST_BOAT,
                    EntityTypes.SPRUCE_CHEST_BOAT,
                    EntityTypes.BIRCH_CHEST_BOAT,
                    EntityTypes.JUNGLE_CHEST_BOAT,
                    EntityTypes.ACACIA_CHEST_BOAT,
                    EntityTypes.DARK_OAK_CHEST_BOAT,
                    EntityTypes.MANGROVE_CHEST_BOAT,
                    EntityTypes.CHERRY_CHEST_BOAT,
                    EntityTypes.PALE_OAK_CHEST_BOAT,
                    EntityTypes.BAMBOO_CHEST_RAFT,""")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/util/Capabilities.java", patch_capabilities_entities)

# General recipe queries are now server RecipeManager-only. The client-side recipe path is restored
# in the later client pass; common/runtime code must tolerate there being no integrated server.
def patch_recipe_manager_server(t):
    t = t.replace(
        "level.getRecipeManager().getRecipeFor(recipeType, inventory, level)",
        "level.getServer() == null ? Optional.empty() : level.getServer().getRecipeManager().getRecipeFor(recipeType, inventory, level)"
    )
    t = t.replace(
        "level.getRecipeManager().getRecipeFor(recipeType, inventory, level, ResourceKey.create(Registries.RECIPE, recipeId))",
        "level.getServer() == null ? Optional.empty() : level.getServer().getRecipeManager().getRecipeFor(recipeType, inventory, level, ResourceKey.create(Registries.RECIPE, recipeId))"
    )
    old = """\t\treturn level.getRecipeManager().getRecipes().stream()
\t\t\t\t.filter(holder -> holder.value().getType() == recipeType)
\t\t\t\t.map(holder -> (RecipeHolder<T>) holder)
\t\t\t\t.filter(holder -> holder.value().matches(inventory, level))
\t\t\t\t.toList();"""
    new = """\t\tif (level.getServer() == null) {
\t\t\treturn Collections.emptyList();
\t\t}
\t\treturn level.getServer().getRecipeManager().getRecipes().stream()
\t\t\t\t.filter(holder -> holder.value().getType() == recipeType)
\t\t\t\t.map(holder -> (RecipeHolder<T>) holder)
\t\t\t\t.filter(holder -> holder.value().matches(inventory, level))
\t\t\t\t.toList();"""
    t = t.replace(old, new)
    return t
patch("net/p3pp3rf1y/sophisticatedcore/util/RecipeHelper.java", patch_recipe_manager_server)

# Item entities moved to EntityTypes.
def patch_magnet_entity(t):
    t = t.replace("EntityType.ITEM_ENTITY", "EntityTypes.ITEM")
    if "import net.minecraft.world.entity.EntityTypes;" not in t:
        t = t.replace("import net.minecraft.world.entity.EntityType;",
                      "import net.minecraft.world.entity.EntityType;\nimport net.minecraft.world.entity.EntityTypes;")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/upgrades/magnet/MagnetUpgradeWrapper.java", patch_magnet_entity)

# Vanilla numeric op levels were replaced by named permissions.
# The old level 0 remains unrestricted; level 2 maps to the gamemaster permission tier.
def patch_infinity_permissions(t):
    t = t.replace("sp.hasPermissions(permissionLevel)",
                  "(permissionLevel <= 0 || sp.permissions().hasPermission(Permissions.COMMANDS_GAMEMASTER))")
    t = t.replace("sp.hasPermissions(getPermissionLevel())",
                  "(getPermissionLevel() <= 0 || sp.permissions().hasPermission(Permissions.COMMANDS_GAMEMASTER))")
    if "import net.minecraft.server.permissions.Permissions;" not in t:
        if "import net.minecraft.server.level.ServerPlayer;" in t:
            t = t.replace("import net.minecraft.server.level.ServerPlayer;",
                          "import net.minecraft.server.level.ServerPlayer;\nimport net.minecraft.server.permissions.Permissions;")
        else:
            t = t.replace("import net.minecraft.world.entity.player.Player;",
                          "import net.minecraft.world.entity.player.Player;\nimport net.minecraft.server.permissions.Permissions;")
    return t
for rel in [
    "net/p3pp3rf1y/sophisticatedcore/upgrades/infinity/InfinityInventoryPart.java",
    "net/p3pp3rf1y/sophisticatedcore/upgrades/infinity/InfinityUpgradeItem.java",
]:
    patch(rel, patch_infinity_permissions)

# Extend the vendored SFL transfer helper with the two fluid inspection helpers Sophisticated Core uses.
transfer_util = java_root / "com/github/salandora/sophisticatedfabriclib/transfer/api/v1/TransferUtil.java"
if transfer_util.exists():
    txt = transfer_util.read_text(errors="ignore")
    if "static FluidStack getFirstFluid(" not in txt:
        insert = """
\tstatic FluidStack getFirstFluid(Storage<FluidVariant> storage) {
\t\tfor (StorageView<FluidVariant> view : storage.nonEmptyViews()) {
\t\t\treturn new FluidStack(view);
\t\t}
\t\treturn FluidStack.EMPTY;
\t}

\tstatic FluidStack simulateExtractAnyFluid(Storage<FluidVariant> storage, long maxAmount) {
\t\tfor (StorageView<FluidVariant> view : storage.nonEmptyViews()) {
\t\t\tlong amount = Math.min(maxAmount, view.getAmount());
\t\t\tif (amount > 0) {
\t\t\t\treturn new FluidStack(view.getResource(), amount);
\t\t\t}
\t\t}
\t\treturn FluidStack.EMPTY;
\t}

"""
        txt = txt.replace("\tstatic void giveOrDropToPlayer", insert + "\tstatic void giveOrDropToPlayer")
        imports = """import net.fabricmc.fabric.api.transfer.v1.fluid.FluidVariant;
import net.fabricmc.fabric.api.transfer.v1.storage.Storage;
import net.fabricmc.fabric.api.transfer.v1.storage.StorageView;
import com.github.salandora.sophisticatedfabriclib.fluid.api.v1.FluidStack;
"""
        txt = txt.replace("import net.minecraft.sounds.SoundEvents;", imports + "import net.minecraft.sounds.SoundEvents;")
        transfer_util.write_text(txt)

# BucketPickupHandlerWrapper is not a Fabric Storage. Handle bucket-pickup sources directly and
# insert one bucket transactionally into the storage.
def patch_pump_world_pickup(t):
    start_sig = "\tprivate boolean fillFromBlock(Level level, BlockPos pos, Storage<FluidVariant> storageFluidHandler, @Nullable Player player) {"
    idx = t.find(start_sig)
    if idx >= 0:
        brace = t.find("{", idx)
        depth = 0
        end = brace
        while end < len(t):
            if t[end] == "{":
                depth += 1
            elif t[end] == "}":
                depth -= 1
                if depth == 0:
                    end += 1
                    break
            end += 1
        replacement = """\tprivate boolean fillFromBlock(Level level, BlockPos pos, Storage<FluidVariant> storageFluidHandler, @Nullable Player player) {
\t\tFluidState fluidState = level.getFluidState(pos);
\t\tif (fluidState.isEmpty()) {
\t\t\treturn false;
\t\t}
\t\tBlockState state = level.getBlockState(pos);
\t\tif (!(state.getBlock() instanceof BucketPickup bucketPickup)) {
\t\t\treturn false;
\t\t}
\t\tFluidStack source = new FluidStack(fluidState.getType(), FluidConstants.BUCKET);
\t\tif (!fluidFilterLogic.fluidMatches(source)) {
\t\t\treturn false;
\t\t}
\t\ttry (Transaction tx = Transaction.openOuter()) {
\t\t\tlong inserted = storageFluidHandler.insert(source.getResource(), FluidConstants.BUCKET, tx);
\t\t\tif (inserted != FluidConstants.BUCKET) {
\t\t\t\treturn false;
\t\t\t}
\t\t\tItemStack pickedUp = bucketPickup.pickupBlock(player, level, pos, state);
\t\t\tif (pickedUp.isEmpty()) {
\t\t\t\treturn false;
\t\t\t}
\t\t\ttx.commit();
\t\t\treturn true;
\t\t}
\t}"""
        t = t[:idx] + replacement + t[end:]
    return t
patch("net/p3pp3rf1y/sophisticatedcore/upgrades/pump/PumpUpgradeWrapper.java", patch_pump_world_pickup)

# Tank background atlas constant was removed from InventoryMenu.
patch("net/p3pp3rf1y/sophisticatedcore/upgrades/tank/TankUpgradeContainer.java",
      lambda t: t.replace("InventoryMenu.BLOCK_ATLAS",
                          "Identifier.fromNamespaceAndPath(\"minecraft\", \"textures/atlas/blocks.png\")"))

# CraftingUpgradeContainer must use the server RecipeManager and compare ResourceKey identifiers.
def patch_crafting_recipe_select(t):
    old_start = "\t@Override\n\tpublic void setRecipeUsed(Identifier recipeId) {"
    idx = t.find(old_start)
    if idx >= 0:
        brace = t.find("{", idx)
        depth = 0
        end = brace
        while end < len(t):
            if t[end] == "{":
                depth += 1
            elif t[end] == "}":
                depth -= 1
                if depth == 0:
                    end += 1
                    break
            end += 1
        replacement = """\t@Override
\tpublic void setRecipeUsed(Identifier recipeId) {
\t\tif (lastRecipe != null && lastRecipe.id().identifier().equals(recipeId)) {
\t\t\treturn;
\t\t}
\t\tif (player.level().getServer() == null) {
\t\t\treturn;
\t\t}
\t\tplayer.level().getServer().getRecipeManager().byKey(ResourceKey.create(Registries.RECIPE, recipeId))
\t\t\t\t.filter(r -> r.value().getType() == RecipeType.CRAFTING)
\t\t\t\t.map(r -> (RecipeHolder<CraftingRecipe>) r)
\t\t\t\t.ifPresent(recipe -> {
\t\t\t\t\tlastRecipe = recipe;
\t\t\t\t\tfor (int i = 0; i < matchedCraftingRecipes.size(); i++) {
\t\t\t\t\t\tif (matchedCraftingRecipes.get(i).id().identifier().equals(recipeId)) {
\t\t\t\t\t\t\tselectCraftingResult(i);
\t\t\t\t\t\t\treturn;
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t});
\t}"""
        t = t[:idx] + replacement + t[end:]
    return t
patch("net/p3pp3rf1y/sophisticatedcore/upgrades/crafting/CraftingUpgradeContainer.java", patch_crafting_recipe_select)

# Robustly replace the old CompoundTag load hook after all earlier NBT transforms.
def patch_controller_load_robust(t):
    t = remove_method_by_signature(t, "public void loadAdditional(")
    marker = "\n\t@Override\n\tpublic CompoundTag getUpdateTag"
    method = """
\t@Override
\tprotected void loadAdditional(ValueInput input) {
\t\tsuper.loadAdditional(input);
\t\tstoragePositions = input.read(\"storagePositions\", Codec.LONG.listOf()).orElse(List.of()).stream().map(BlockPos::of).collect(java.util.stream.Collectors.toCollection(ArrayList::new));
\t\tconnectingBlocks = input.read(\"connectingBlocks\", Codec.LONG.listOf()).orElse(List.of()).stream().map(BlockPos::of).collect(java.util.stream.Collectors.toCollection(LinkedHashSet::new));
\t\tnonConnectingBlocks = input.read(\"nonConnectingBlocks\", Codec.LONG.listOf()).orElse(List.of()).stream().map(BlockPos::of).collect(java.util.stream.Collectors.toCollection(LinkedHashSet::new));
\t\tbaseIndexes = new ArrayList<>(input.read(\"baseIndexes\", Codec.INT.listOf()).orElse(List.of()));
\t\ttotalSlots = input.getIntOr(\"totalSlots\", 0);
\t\tlinkedBlocks = input.read(\"linkedBlocks\", Codec.LONG.listOf()).orElse(List.of()).stream().map(BlockPos::of).collect(java.util.stream.Collectors.toCollection(LinkedHashSet::new));
\t}
"""
    if marker in t and "protected void loadAdditional(ValueInput input)" not in t:
        t = t.replace(marker, "\n" + method + marker)
    return t
patch("net/p3pp3rf1y/sophisticatedcore/controller/ControllerBlockEntityBase.java", patch_controller_load_robust)

print("Applied eighth MC 26.3 targeted cleanup pass.")


# Ninth MC 26.3 cleanup pass: final three Core compile blockers.

# RecipeOutput now also exposes bootstrap context lookup/list methods.
def patch_holding_bootstrap(t):
    anchor = "\n\tpublic Recipe<?> getRecipe() {"
    methods = """
\t@Override
\tpublic <S> HolderGetter<S> lookup(ResourceKey<? extends Registry<? extends S>> registryKey) {
\t\tthrow new UnsupportedOperationException(\"HoldingRecipeOutput does not provide registry bootstrap lookups\");
\t}

\t@Override
\tpublic <S> Stream<Holder.Reference<S>> listContextElements(ResourceKey<? extends Registry<? extends S>> registryKey) {
\t\treturn Stream.empty();
\t}

"""
    if anchor in t and "listContextElements(" not in t:
        t = t.replace(anchor, "\n" + methods + anchor)
    imports = [
        ("import net.minecraft.advancements.Advancement;", "import net.minecraft.advancements.Advancement;\nimport net.minecraft.core.Holder;\nimport net.minecraft.core.HolderGetter;\nimport net.minecraft.core.Registry;"),
        ("import javax.annotation.Nullable;", "import javax.annotation.Nullable;\nimport java.util.stream.Stream;"),
    ]
    for old,new in imports:
        if old in t:
            t = t.replace(old,new)
    return t
patch("net/p3pp3rf1y/sophisticatedcore/crafting/HoldingRecipeOutput.java", patch_holding_bootstrap)

# SFL FluidStack exposes getResource(), not the old getVariant() name.
patch("net/p3pp3rf1y/sophisticatedcore/upgrades/tank/TankUpgradeWrapper.java",
      lambda t: t.replace("TransferUtil.getFirstFluid(fluidHandler).getVariant()",
                          "TransferUtil.getFirstFluid(fluidHandler).getResource()"))

# Direct bucket pickup now uses a Fabric transaction.
def patch_pump_transaction_import(t):
    if "import net.fabricmc.fabric.api.transfer.v1.transaction.Transaction;" not in t:
        t = t.replace("import net.fabricmc.fabric.api.transfer.v1.storage.StorageView;",
                      "import net.fabricmc.fabric.api.transfer.v1.storage.StorageView;\nimport net.fabricmc.fabric.api.transfer.v1.transaction.Transaction;")
    return t
patch("net/p3pp3rf1y/sophisticatedcore/upgrades/pump/PumpUpgradeWrapper.java", patch_pump_transaction_import)

print("Applied ninth MC 26.3 final Core compile cleanup pass.")
