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
