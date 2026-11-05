#!/usr/bin/env python3
"""Add real server regression tests to ephemeral debug source (never packaged into JAR).
Requires inject_smoke_test.py + audit_integrity.py to have run first.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/"src/main/java/com/titammods/compat/port/validation/ForgeSmokeTest.java"
s=p.read_text(encoding="utf-8")
anchor='        System.out.println("HEPHAESTUS_VERIFY_SUCCESS recipes, table, basin, melter");'
assert s.count(anchor)==1
s=s.replace(anchor,"""        checkFluidNotifications();
        checkSmelteryBucketTransfer(level,y);
"""+anchor)
marker="    public static void check(MinecraftServer server) {"
assert s.count(marker)==1
new="""    // Legacy fluid operations previously bypassed SmelteryControllerBlockEntity.setChanged.
    private static void checkFluidNotifications() {
        int[] changes = {0};
        var tank = new com.titammods.common.blockentities.multiblock.SmelteryFluidHandler(
                () -> changes[0]++);
        tank.setCapacity(4000);
        require(changes[0] == 1, "Fluid capacity change does not notify owner");
        var lava = new FluidStack(Fluids.LAVA, 1000);
        int previous=changes[0];
        require(tank.fill(lava,IFluidHandler.FluidAction.SIMULATE)==1000, "Fluid simulate fill failed");
        require(changes[0]==previous, "Fluid simulate fill changed owner");
        require(tank.fill(lava,IFluidHandler.FluidAction.EXECUTE)==1000, "Fluid fill failed");
        require(changes[0]==previous+1, "Fluid fill failed to mark owner dirty");
        previous=changes[0];
        require(tank.drain(500,IFluidHandler.FluidAction.SIMULATE).getAmount()==500,
                "Fluid simulate drain failed");
        require(changes[0]==previous, "Fluid simulate drain changed owner");
        require(tank.drain(500,IFluidHandler.FluidAction.EXECUTE).getAmount()==500, "Fluid drain failed");
        require(changes[0]==previous+1 && tank.getTotalFluid()==500,
                "Fluid drain did not save the new amount");
        require(tank.drain(new FluidStack(Fluids.LAVA,250),IFluidHandler.FluidAction.EXECUTE)
                .getAmount()==250, "Resource-specific fluid drain failed");
        require(changes[0]==previous+2 && tank.getTotalFluid()==250,
                "Resource-specific fluid drain missed owner notification");
        System.out.println("HEPHAESTUS_ALPHA3 fluid dirty notifications + no changes on simulation OK");
    }

    // This exercises the *actual* menu's new ItemAccess/FluidResource transaction.
    private static void checkSmelteryBucketTransfer(ServerLevel level,int y) {
        BlockPos pos = new BlockPos(29,y,20);
        level.setBlockAndUpdate(pos,ModBlocks.SMELTERY_CONTROLLER.get().defaultBlockState());
        require(level.getBlockEntity(pos) instanceof SmelteryControllerBlockEntity,
                "Smeltery controller test fixture missing");
        var be=(SmelteryControllerBlockEntity)level.getBlockEntity(pos);
        be.fluidTank.setCapacity(8000);
        var player=net.neoforged.neoforge.common.util.FakePlayerFactory.getMinecraft(level);
        var menu=new com.titammods.menu.SmelteryMenu(20,player.getInventory(),be);
        menu.bucketHandler.setStackInSlot(0,new ItemStack(Items.LAVA_BUCKET));
        require(menu.bucketHandler.getStackInSlot(0).isEmpty(), "Lava bucket not processed");
        require(menu.bucketHandler.getStackInSlot(1).is(Items.BUCKET),
                "Lava bucket failed to produce empty bucket");
        require(be.fluidTank.getTotalFluid()==1000,
                "Lava bucket fluid amount did not enter smeltery");
        menu.removed(player);
        require(menu.bucketHandler.getStackInSlot(1).isEmpty(),"Bucket returned without clearing slot");
        menu.removed(player);
        require(menu.bucketHandler.isEmpty() == false ? false : true,
                "Duplicate bucket remained after second menu close");
        var fillMenu=new com.titammods.menu.SmelteryMenu(21,player.getInventory(),be);
        fillMenu.bucketHandler.setStackInSlot(0,new ItemStack(Items.BUCKET));
        require(fillMenu.bucketHandler.getStackInSlot(1).is(Items.LAVA_BUCKET),
                "Empty bucket failed to fill from smeltery");
        require(be.fluidTank.getTotalFluid()==0,
                "Empty bucket did not remove exactly one bucket of lava");
        fillMenu.removed(player);
        System.out.println("HEPHAESTUS_ALPHA3 bucket insert/extract and menu idempotent close OK");
    }

"""
s=s.replace(marker,new+marker)
# Handler name "isEmpty" is not exposed by generated ItemStackHandler, check individual slots.
s=s.replace('menu.bucketHandler.isEmpty() == false ? false : true',
            '(!menu.bucketHandler.getStackInSlot(0).isEmpty() || !menu.bucketHandler.getStackInSlot(1).isEmpty())')
# Existing statement condition inverted? Above boolean true if nonempty, and require true mistakenly.
s=s.replace('require((!menu.bucketHandler.getStackInSlot(0).isEmpty() || !menu.bucketHandler.getStackInSlot(1).isEmpty()),',
            'require(menu.bucketHandler.getStackInSlot(0).isEmpty() && menu.bucketHandler.getStackInSlot(1).isEmpty(),')
p.write_text(s,encoding="utf-8")
print("ALPHA3_REGRESSION: injected fluid dirty/simulation and actual GUI bucket transfer tests")
