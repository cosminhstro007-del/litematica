#!/usr/bin/env python3
"""Stage 2: remove old build-only datagen; adapt legacy inventory/tank internals.
Original Hephaestus Forge 1.0.20 remains MIT licensed; gameplay assets untouched.
The mod already exposes NeoForge ResourceHandler for external pipes, while local
legacy handlers are retained only for the author's existing machine logic.
"""
from pathlib import Path
import shutil,sys

root=Path(sys.argv[1]).resolve()
base=root/"src/main/java/com/titammods"
legacy=base/"compat/port/legacy"
legacy.mkdir(parents=True,exist_ok=True)

def put(path,body):
    (legacy/path).parent.mkdir(parents=True,exist_ok=True)
    (legacy/path).write_text(body,encoding="utf-8")

# Datagen is not loaded during normal gameplay; keep the existing generated JSONs.
d=base/"datagen"
if d.exists(): shutil.rmtree(d)
main=base/"TitamMods.java"
s=main.read_text(encoding="utf-8")
s=s.replace("import com.titammods.datagen.DataGenerators;\n","")
s=s.replace("        DataGenerators.register(modEventBus);\n","")
main.write_text(s,encoding="utf-8")

old_prefixes={
"net.neoforged.neoforge.fluids.capability.templates.":"com.titammods.compat.port.legacy.",
"net.neoforged.neoforge.fluids.capability.":"com.titammods.compat.port.legacy.",
"net.neoforged.neoforge.items.":"com.titammods.compat.port.legacy.",
}
for p in base.rglob("*.java"):
    if legacy in p.parents: continue
    s=p.read_text(encoding="utf-8")
    t=s
    for a,b in old_prefixes.items(): t=t.replace(a,b)
    if t!=s: p.write_text(t,encoding="utf-8")

put("IFluidHandler.java", """package com.titammods.compat.port.legacy;
import net.neoforged.neoforge.fluids.FluidStack;
/** Internal 26.1 machine API bridge; external transfer uses NeoForge ResourceHandler. */
public interface IFluidHandler {
    enum FluidAction {
        EXECUTE, SIMULATE;
        public boolean execute() { return this == EXECUTE; }
    }
    int getTanks();
    FluidStack getFluidInTank(int tank);
    int getTankCapacity(int tank);
    boolean isFluidValid(int tank, FluidStack fluid);
    int fill(FluidStack fluid, FluidAction action);
    FluidStack drain(FluidStack fluid, FluidAction action);
    FluidStack drain(int maxAmount, FluidAction action);
}
""")
put("FluidTank.java", """package com.titammods.compat.port.legacy;
import net.neoforged.neoforge.fluids.FluidStack;
import java.util.Objects;
/** Internal tank, preserves original fill/drain semantics without obsolete capability API. */
public class FluidTank implements IFluidHandler {
    protected FluidStack fluid = FluidStack.EMPTY;
    protected final int capacity;
    public FluidTank(int capacity) { this.capacity = Math.max(0,capacity); }
    protected void onContentsChanged() {}
    public FluidStack getFluid() { return fluid; }
    public int getFluidAmount() { return fluid.getAmount(); }
    public int getCapacity() { return capacity; }
    public boolean isEmpty() { return fluid.isEmpty(); }
    public void setFluid(FluidStack stack) {
        fluid = stack == null || stack.isEmpty() ? FluidStack.EMPTY :
                stack.copyWithAmount(Math.min(capacity,Math.max(0,stack.getAmount())));
        onContentsChanged();
    }
    public boolean isFluidValid(FluidStack fluid) { return true; }
    @Override public int getTanks() { return 1; }
    @Override public FluidStack getFluidInTank(int tank) { return tank==0 ? fluid : FluidStack.EMPTY; }
    @Override public int getTankCapacity(int tank) { return tank==0 ? capacity : 0; }
    @Override public boolean isFluidValid(int tank, FluidStack f) { return tank==0 && isFluidValid(f); }
    @Override public int fill(FluidStack resource, FluidAction action) {
        if(resource==null || resource.isEmpty() || !isFluidValid(resource)) return 0;
        if (!fluid.isEmpty() && !FluidStack.isSameFluidSameComponents(fluid,resource)) return 0;
        int inserted=Math.min(resource.getAmount(),capacity-fluid.getAmount());
        if(inserted<=0)return 0;
        if(action.execute()) setFluid(resource.copyWithAmount(fluid.getAmount()+inserted));
        return inserted;
    }
    @Override public FluidStack drain(FluidStack wanted, FluidAction action) {
        if(wanted==null || wanted.isEmpty() || fluid.isEmpty() ||
           !FluidStack.isSameFluidSameComponents(fluid,wanted)) return FluidStack.EMPTY;
        return drain(wanted.getAmount(),action);
    }
    @Override public FluidStack drain(int maxAmount, FluidAction action) {
        if(maxAmount<=0 || fluid.isEmpty()) return FluidStack.EMPTY;
        int extracted=Math.min(maxAmount,fluid.getAmount());
        FluidStack out=fluid.copyWithAmount(extracted);
        if(action.execute()) setFluid(fluid.copyWithAmount(fluid.getAmount()-extracted));
        return out;
    }
}
""")
put("IItemHandler.java", """package com.titammods.compat.port.legacy;
import net.minecraft.world.item.ItemStack;
public interface IItemHandler {
    int getSlots();
    ItemStack getStackInSlot(int slot);
    ItemStack insertItem(int slot, ItemStack stack, boolean simulate);
    ItemStack extractItem(int slot, int amount, boolean simulate);
    int getSlotLimit(int slot);
    boolean isItemValid(int slot, ItemStack stack);
}
""")
put("IItemHandlerModifiable.java", """package com.titammods.compat.port.legacy;
import net.minecraft.world.item.ItemStack;
public interface IItemHandlerModifiable extends IItemHandler {
    void setStackInSlot(int slot, ItemStack stack);
}
""")
put("ItemStackHandler.java", """package com.titammods.compat.port.legacy;
import net.minecraft.world.item.ItemStack;
import java.util.ArrayList;
import java.util.List;
/** Per-machine slot inventory retaining the original event notification contract. */
public class ItemStackHandler implements IItemHandlerModifiable {
    protected final List<ItemStack> stacks;
    public ItemStackHandler(int count) {
        stacks=new ArrayList<>(Math.max(count,0));
        for(int i=0;i<count;i++)stacks.add(ItemStack.EMPTY);
    }
    @Override public int getSlots() { return stacks.size(); }
    public void setStackInSlot(int slot, ItemStack stack) {
        if(slot<0||slot>=getSlots())return;
        ItemStack next=stack==null||stack.isEmpty()? ItemStack.EMPTY:
                stack.copyWithCount(Math.min(getSlotLimit(slot),stack.getCount()));
        stacks.set(slot,next);
        onContentsChanged(slot);
    }
    @Override public ItemStack getStackInSlot(int slot) {
        return slot<0||slot>=getSlots()?ItemStack.EMPTY:stacks.get(slot);
    }
    @Override public int getSlotLimit(int slot) {return 64;}
    @Override public boolean isItemValid(int slot,ItemStack stack){return true;}
    protected void onContentsChanged(int slot) {}
    @Override public ItemStack insertItem(int slot,ItemStack stack,boolean simulate){
        if(stack==null||stack.isEmpty())return ItemStack.EMPTY;
        if(slot<0||slot>=getSlots()||!isItemValid(slot,stack))return stack;
        ItemStack current=getStackInSlot(slot);
        if(!current.isEmpty()&&!ItemStack.isSameItemSameComponents(current,stack))return stack;
        int limit=Math.min(getSlotLimit(slot),stack.getMaxStackSize());
        int moved=Math.min(Math.max(0,limit-current.getCount()),stack.getCount());
        if(moved<=0)return stack;
        if(!simulate) {
            if(current.isEmpty()) setStackInSlot(slot,stack.copyWithCount(moved));
            else setStackInSlot(slot,current.copyWithCount(current.getCount()+moved));
        }
        return moved==stack.getCount()?ItemStack.EMPTY:stack.copyWithCount(stack.getCount()-moved);
    }
    @Override public ItemStack extractItem(int slot,int amount,boolean simulate){
        if(slot<0||slot>=getSlots()||amount<=0)return ItemStack.EMPTY;
        ItemStack curr=getStackInSlot(slot);
        if(curr.isEmpty())return ItemStack.EMPTY;
        int moved=Math.min(amount,curr.getCount());
        ItemStack removed=curr.copyWithCount(moved);
        if(!simulate) {
            if(moved==curr.getCount())setStackInSlot(slot,ItemStack.EMPTY);
            else setStackInSlot(slot,curr.copyWithCount(curr.getCount()-moved));
        }
        return removed;
    }
}
""")
put("SlotItemHandler.java", """package com.titammods.compat.port.legacy;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
/** Slot bridge to the original 26.1 handler, not a separate inventory. */
public class SlotItemHandler extends Slot {
    protected final IItemHandler handler;
    public SlotItemHandler(IItemHandler handler,int index,int x,int y) {
        super(new SimpleContainer(Math.max(handler.getSlots(),index+1)),index,x,y);
        this.handler=handler;
    }
    @Override public ItemStack getItem(){return handler.getStackInSlot(index);}
    @Override public boolean hasItem(){return !getItem().isEmpty();}
    @Override public void set(ItemStack stack) {
        if(handler instanceof IItemHandlerModifiable m) m.setStackInSlot(index,stack);
    }
    @Override public ItemStack remove(int count){return handler.extractItem(index,count,false);}
    @Override public boolean mayPlace(ItemStack stack){return handler.isItemValid(index,stack);}
    @Override public boolean mayPickup(Player p){return true;}
    @Override public int getMaxStackSize(){return handler.getSlotLimit(index);}
    @Override public int getMaxStackSize(ItemStack stack) {
        return Math.min(stack.getMaxStackSize(),handler.getSlotLimit(index));
    }
    @Override public void setChanged(){ }
}
""")
put("ItemHandlerHelper.java", """package com.titammods.compat.port.legacy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
public final class ItemHandlerHelper {
    private ItemHandlerHelper(){}
    public static void giveItemToPlayer(Player player,ItemStack stack,int preferredSlot){
        if(stack==null||stack.isEmpty())return;
        ItemStack copy=stack.copy();
        player.getInventory().add(copy);
        if(!copy.isEmpty())player.drop(copy,false);
    }
}
""")
print("Stage2: machine legacy API adapted via private shims, runtime datagen excluded.")
