#!/usr/bin/env python3
"""Alpha7 critical NeoForge 26.3 slot mapping hotfix.

Minecraft AbstractContainerMenu.addSlot() assigns a MENU index to Slot.index.
The 26.3 compatibility bridge accidentally used that menu index as the
IItemHandler's INVENTORY index, breaking every appended handler slot:
especially the bucket input/output, and some offscreen inventory menus.
Keep a separate immutable realSlot captured before the menu registers slot.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/"src/main/java/com/titammods/compat/port/legacy/SlotItemHandler.java"
s=p.read_text(encoding="utf-8")
needle="    protected final IItemHandler handler;"
assert s.count(needle)==1
s=s.replace(needle,needle+"\n    private final int realHandlerSlot;")
needle="        this.handler=handler;"
assert s.count(needle)==1
s=s.replace(needle,needle+"\n        this.realHandlerSlot=index;")
for a,b in [
("handler.getStackInSlot(index)","handler.getStackInSlot(realHandlerSlot)"),
("m.setStackInSlot(index,stack)","m.setStackInSlot(realHandlerSlot,stack)"),
("handler.extractItem(index,count,false)","handler.extractItem(realHandlerSlot,count,false)"),
("handler.isItemValid(index,stack)","handler.isItemValid(realHandlerSlot,stack)"),
("handler.getSlotLimit(index)","handler.getSlotLimit(realHandlerSlot)")
]:
    assert a in s,("Old slot mapping not present",a)
    s=s.replace(a,b)
p.write_text(s,encoding="utf-8")
assert "handler.getStackInSlot(index)" not in s
print("ALPHA7_SLOT_MAP_FIXED: immutable handler index independent of menu Slot.index")
