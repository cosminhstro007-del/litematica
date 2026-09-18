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
