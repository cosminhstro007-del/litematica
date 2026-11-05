#!/usr/bin/env python3
"""Forge Alpha3: fix direct (legacy) fluid operations not marking tanks dirty,
and make GUI bucket returns idempotent on menu close.
The original Forge code and all gameplay functionality remain intact.
"""
from pathlib import Path
import sys,re
root=Path(sys.argv[1]).resolve()
src=root/"src/main/java/com/titammods"

p=src/"common/blockentities/multiblock/SmelteryFluidHandler.java"
s=p.read_text(encoding="utf-8")
before=s
def replace(old,new,count=1):
    global s
    assert s.count(old)==count,(p.name,old[:120],s.count(old))
    s=s.replace(old,new)
replace(
    "public void setCapacity(int newCapacity) { this.capacity = newCapacity; }",
    """public void setCapacity(int newCapacity) {
        if (this.capacity != newCapacity) {
            this.capacity = newCapacity;
            onChanged.run();
        }
    }""")
replace(
    """            FluidStack fluid = fluids.remove(index);
            fluids.add(0, fluid);""",
    """            FluidStack fluid = fluids.remove(index);
            fluids.add(0, fluid);
            onChanged.run();""")
replace(
    """                if (FluidStack.isSameFluidSameComponents(f, resource)) {
                    f.grow(amount);
                    return amount;
                }""",
    """                if (FluidStack.isSameFluidSameComponents(f, resource)) {
                    f.grow(amount);
                    onChanged.run();
                    return amount;
                }""")
replace(
    """            copy.setAmount(amount);
            fluids.add(copy);
        }
        return amount;""",
    """            copy.setAmount(amount);
            fluids.add(copy);
            onChanged.run();
        }
        return amount;""")
# Two legacy drain overloads must both mark the owner dirty on executed extraction.
replace(
    """                    if (f.isEmpty()) fluids.remove(i);
                }
                return drained;""",
    """                    if (f.isEmpty()) fluids.remove(i);
                    onChanged.run();
                }
                return drained;""")
replace(
    """            if (f.isEmpty()) fluids.remove(0);
        }
        return drained;""",
    """            if (f.isEmpty()) fluids.remove(0);
            onChanged.run();
        }
        return drained;""")
assert s!=before
p.write_text(s,encoding="utf-8")

p=src/"menu/SmelteryMenu.java"
s=p.read_text(encoding="utf-8")
old="""        for (int i = 0; i < bucketHandler.getSlots(); i++) {
            ItemStack s = bucketHandler.getStackInSlot(i);
            if (!s.isEmpty()) player.drop(s, false, net.minecraft.util.Prediction.SERVER_ONLY);
        }"""
new="""        // Menu-local items are not persisted. Remove them before returning them
        // to the player, otherwise repeated removal can drop the same stack twice.
        isProcessingBucket = true;
        try {
            for (int i = 0; i < bucketHandler.getSlots(); i++) {
                ItemStack stack = bucketHandler.extractItem(i, 1, false);
                if (!stack.isEmpty())
                    player.drop(stack, false, net.minecraft.util.Prediction.SERVER_ONLY);
            }
        } finally {
            isProcessingBucket = false;
        }"""
assert s.count(old)==1,("Bucket close code changed",s[s.index("public void removed("):][:500])
s=s.replace(old,new)
p.write_text(s,encoding="utf-8")

p=root/"gradle.properties"
s=p.read_text(encoding="utf-8")
s,n=re.subn(r"(?m)^mod_version=.*$","mod_version=1.0.20-unofficial-26.3-alpha3",s)
assert n==1
p.write_text(s,encoding="utf-8")
print("ALPHA3_STABILITY: legacy fluids mark dirty, bucket close is idempotent.")
