#!/usr/bin/env python3
"""Developer-only Alpha7 UI regression tests for reported item disappearance.
Applied *after* release JAR compilation. Exercises the actual Menu#quickMoveStack
without relying on a graphical client (GUI mouse packet still needs client test).
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/"src/main/java/com/titammods/compat/port/validation/ForgeSmokeTest.java"
s=p.read_text(encoding="utf-8")
anchor='        System.out.println("HEPHAESTUS_VERIFY_SUCCESS recipes, table, basin, melter");'
assert s.count(anchor)==1
s=s.replace(anchor,"        verifyPlayerShiftClickAndBucketSafety(level,y);\n"+anchor)
marker="    public static void check(MinecraftServer server) {"
assert s.count(marker)==1
s=s.replace(marker,"""    private static void verifyPlayerShiftClickAndBucketSafety(ServerLevel level,int y) {
        BlockPos pos=new BlockPos(56,y,46);
        level.setBlockAndUpdate(pos,ModBlocks.SMELTERY_CONTROLLER.get().defaultBlockState());
        require(level.getBlockEntity(pos) instanceof SmelteryControllerBlockEntity,
                "Alpha7 controller fixture failed");
        var be=(SmelteryControllerBlockEntity)level.getBlockEntity(pos);
        be.itemHandler=new com.titammods.compat.port.legacy.ItemStackHandler(70) {
            @Override public int getSlotLimit(int slot) {return 1;}
        };
        be.meltingProgress=new int[70];
        be.meltingTime=new int[70];
        be.meltingState=new int[70];
        be.fluidTank.setCapacity(8000);
        var user=net.neoforged.neoforge.common.util.FakePlayerFactory.get(level,
                new com.mojang.authlib.GameProfile(
                    java.util.UUID.nameUUIDFromBytes("Alpha7Transfer".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                    "Alpha7Transfer"));
        user.getInventory().clearContent();
        user.setPos(pos.getX()+0.5,pos.getY()+1,pos.getZ()+0.5);
        var menu=new com.titammods.menu.SmelteryMenu(70,user.getInventory(),be);
        require(menu.slots.size()==70,
                "Controller menu still creates hidden slots: "+menu.slots.size());
        // 32 virtual visible slots, then bucket input/output, then 36 player.
        final int hotbar0=34;
        require(com.titammods.common.recipe.HephaestusRecipeCache.melting(
                level,new ItemStack(Items.RAW_IRON)) != null,
                "Raw iron recipe missing, controller shouldn't eat unsupported ore blocks");
        user.getInventory().setItem(0,new ItemStack(Items.RAW_IRON,64));
        require(menu.quickMoveStack(user,hotbar0).getCount()==64,
                "Shift-click failed to transfer iron ore");
        require(user.getInventory().getItem(0).isEmpty(),
                "Player source ore stack not decremented");
        int ore=0;
        for(int i=0;i<be.itemHandler.getSlots();i++) {
            ItemStack item=be.itemHandler.getStackInSlot(i);
            require(item.getCount()<=1,"Controller slot overflow");
            if(item.is(Items.RAW_IRON)) ore+=item.getCount();
        }
        require(ore==64,"ORE LOST: 64 shift-click ore input => "+ore+" ore in controller");
        System.out.println("HEPHAESTUS_ALPHA7 full 64 ore shift-click conserved in controller");

        // Repeat when only 10 slots are free: source MUST retain the remainder.
        be.itemHandler=new com.titammods.compat.port.legacy.ItemStackHandler(10) {
            @Override public int getSlotLimit(int slot) {return 1;}
        };
        be.meltingProgress=new int[10];
        be.meltingTime=new int[10];
        be.meltingState=new int[10];
        menu=new com.titammods.menu.SmelteryMenu(71,user.getInventory(),be);
        user.getInventory().setItem(0,new ItemStack(Items.RAW_IRON,64));
        require(menu.quickMoveStack(user,hotbar0).getCount()==64,
                "Partial ore shift-click failed");
        require(user.getInventory().getItem(0).getCount()==54,
                "Partial ore transfer ate source remainder: expected 54, got "+
                  user.getInventory().getItem(0).getCount());
        int inMachine=0;
        for(int i=0;i<be.itemHandler.getSlots();i++)
            inMachine+=be.itemHandler.getStackInSlot(i).getCount();
        require(inMachine==10,"Partial ore transfer machine count "+inMachine);
        System.out.println("HEPHAESTUS_ALPHA7 partial stack 10 in smeltery + 54 retained");

        user.getInventory().setItem(0,new ItemStack(Items.DIRT,64));
        require(menu.quickMoveStack(user,hotbar0).isEmpty(),"Dirt falsely accepted as melting ingredient");
        require(user.getInventory().getItem(0).getCount()==64,
                "Non-melting stack was deleted");
        user.getInventory().setItem(0,new ItemStack(Items.IRON_ORE,64));
        require(menu.quickMoveStack(user,hotbar0).isEmpty(),
                "Iron ore block without a recipe was accepted");
        require(user.getInventory().getItem(0).getCount()==64,
                "Unsupported iron ore blocks were deleted");
        System.out.println("HEPHAESTUS_ALPHA7 unsupported ore blocks retained");
        System.out.println("HEPHAESTUS_ALPHA7 unrelated full stack not consumed");

        // Verify when user has 1,000s of internal smeltery slots: menu size
        // must remain 70 (bounded, unlike previous O(n^2) dummy containers).
        be.itemHandler=new com.titammods.compat.port.legacy.ItemStackHandler(2048);
        be.meltingProgress=new int[2048];
        be.meltingTime=new int[2048];
        be.meltingState=new int[2048];
        menu=new com.titammods.menu.SmelteryMenu(72,user.getInventory(),be);
        require(menu.slots.size()==70,
                "Large Smeltery created "+menu.slots.size()+" menu slots, wanted 70");
        System.out.println("HEPHAESTUS_ALPHA7 large 2048-slot GUI has constant 70 menu slots");

        // Shift full lava bucket into existing lava; must return empty bucket.
        be.fluidTank.setCapacity(8000);
        be.fluidTank.fill(new FluidStack(Fluids.LAVA,1000), IFluidHandler.FluidAction.EXECUTE);
        user.getInventory().setItem(0,new ItemStack(Items.LAVA_BUCKET));
        require(!menu.quickMoveStack(user,hotbar0).isEmpty(),
                "Shift-click lava bucket refused");
        require(user.getInventory().getItem(0).isEmpty(),
                "Player lava bucket wasn't consumed on a successful transfer");
        require(menu.bucketHandler.getStackInSlot(1).is(Items.BUCKET),
                "Lava bucket disappeared: no empty bucket returned");
        require(be.fluidTank.getTotalFluid()==2000,
                "Lava bucket failed to add exactly 1000mB");
        System.out.println("ALPHA7_DEBUG bucketDirect="+menu.bucketHandler.getStackInSlot(1)
                +" menuSlot33="+menu.slots.get(33).getItem()
                +" hasItem="+menu.slots.get(33).hasItem()
                +" hasCurrent="+(menu.blockEntity.itemHandler==be.itemHandler)
                +" playerSlot34="+menu.slots.get(34).getItem()
                +" playerSlot69="+menu.slots.get(69).getItem()
                +" slot34MayPlace="+menu.slots.get(34).mayPlace(new ItemStack(Items.BUCKET)));
        var retBucket=menu.quickMoveStack(user,33);
        System.out.println("ALPHA7_DEBUG return="+retBucket
                +" bucketSlot="+menu.bucketHandler.getStackInSlot(1)
                +" playerBucket0="+user.getInventory().getItem(0));
        require(retBucket.is(Items.BUCKET),
                "Shift-click returned empty bucket failed");
        require(menu.bucketHandler.getStackInSlot(1).isEmpty(),
                "Empty bucket output was duplicated");
        System.out.println("HEPHAESTUS_ALPHA7 lava bucket shift-click returned empty bucket");

        user.getInventory().setItem(1,new ItemStack(Items.BUCKET));
        require(!menu.quickMoveStack(user,35).isEmpty(),"Shift empty bucket refused");
        require(menu.bucketHandler.getStackInSlot(1).is(Items.LAVA_BUCKET),
                "Empty bucket disappeared: no lava bucket returned");
        require(be.fluidTank.getTotalFluid()==1000,
                "Empty bucket did not drain exactly 1000mB");
        menu.quickMoveStack(user,33);
        System.out.println("HEPHAESTUS_ALPHA7 empty bucket shift-click returned lava bucket");

        // A full tank MUST leave a lava bucket in the player inventory.
        be.fluidTank.fill(new FluidStack(Fluids.LAVA,7000),IFluidHandler.FluidAction.EXECUTE);
        require(be.fluidTank.getTotalFluid()==8000,"Full-tank fixture invalid");
        user.getInventory().setItem(2,new ItemStack(Items.LAVA_BUCKET));
        require(menu.quickMoveStack(user,36).isEmpty(),
                "Full tank accepted another bucket");
        require(user.getInventory().getItem(2).is(Items.LAVA_BUCKET),
                "Full tank deleted a player's lava bucket");
        require(menu.bucketHandler.getStackInSlot(0).isEmpty() &&
                menu.bucketHandler.getStackInSlot(1).isEmpty(),
                "Full tank left an untracked bucket in menu");
        require(be.fluidTank.getTotalFluid()==8000,
                "Full tank changed capacity illegally");
        System.out.println("HEPHAESTUS_ALPHA7 full tank refuses bucket safely");

        // Manual left click insertion into the bucket input must convert as well.
        be.fluidTank.drain(1000,IFluidHandler.FluidAction.EXECUTE);
        menu.bucketHandler.setStackInSlot(0,new ItemStack(Items.LAVA_BUCKET));
        require(menu.bucketHandler.getStackInSlot(1).is(Items.BUCKET),
                "Manual bucket input returned no empty bucket");
        require(be.fluidTank.getTotalFluid()==8000,
                "Manual bucket input did not insert lava");
        menu.removed(user);
        require(menu.bucketHandler.getStackInSlot(1).isEmpty(),
                "Menu close retained converted bucket");
        menu.removed(user);
        require(menu.bucketHandler.getStackInSlot(1).isEmpty(),
                "Second menu close duplicated converted bucket");
        System.out.println("HEPHAESTUS_ALPHA7 manual bucket insertion and repeated close OK");
    }

"""+marker)
p.write_text(s,encoding="utf-8")
print("ALPHA7_TESTS: added full/partial/dirt/fulltank/bucket/massive menu regression tests")
