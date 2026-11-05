#!/usr/bin/env python3
"""Minecraft 26.3 APIs: block definitions, UI, fluid/item transfer and render layers.
This follows the current NeoForge 26.3 transfer capability API, preserving original gameplay.
"""
from pathlib import Path
import re,sys

root=Path(sys.argv[1]).resolve()
src=root/"src/main/java/com/titammods"
def modify(rel,fn):
 p=src/rel
 b=p.read_text(encoding="utf-8")
 a=fn(b)
 assert a != b, rel
 p.write_text(a,encoding="utf-8")
def replace_one(rel,changes):
 def fn(s):
  for a,b in changes:
   assert a in s,(rel,a)
   s=s.replace(a,b)
  return s
 modify(rel,fn)

# Removed block codecs in 26.3: vanilla no longer overrides BaseEntityBlock#codec().
blocks=list((src/"common/blocks").glob("*.java"))
n=0
for p in blocks:
 s=p.read_text(encoding="utf-8")
 if "CODEC = simpleCodec(" not in s: continue
 old=s
 s,count=re.subn(r"(?m)^[ \t]*public static final MapCodec<[^;]+> CODEC = simpleCodec\([^\n]+\);\n","",s)
 assert count==1,p
 s,num=re.subn(r"(?ms)^[ \t]*@Override\s+(?:protected|public)\s+MapCodec<[^\n]+>\s+codec\(\)\s*\{\s*return CODEC;\s*\}\s*","",s)
 assert num==1,(p,"codec not found")
 p.write_text(s,encoding="utf-8"); n+=1
print("Removed obsolete BaseEntityBlock codec overrides in",n,"classes")

modify("setup/ModBlocks.java",lambda s:s.replace(".isViewBlocking((state, getter, pos) -> false)",""))
for rel in ["setup/ModFluids.java","registry/fluids/MoltenFluidSet.java"]:
 modify(rel,lambda s:s.replace(".pushReaction(PushReaction.DESTROY)",""))
 
# SDL3 and current screen manager.
for rel in ["client/screen/MelterScreen.java","client/screen/SmelteryScreen.java"]:
 modify(rel,lambda s:s.replace("import org.lwjgl.glfw.GLFW;","")
     .replace("GLFW.GLFW_KEY_LEFT_SHIFT","com.mojang.blaze3d.platform.InputConstants.KEY_LSHIFT")
     .replace("GLFW.GLFW_KEY_RIGHT_SHIFT","com.mojang.blaze3d.platform.InputConstants.KEY_RSHIFT"))
replace_one("client/ClientModEvents.java",[
 ("net.minecraft.client.Minecraft.getInstance().setScreen(","net.minecraft.client.Minecraft.getInstance().gui.setScreen(")
])
replace_one("compat/jei/EntityRenderHelper.java",[
 ("type.create(mc.level, null)","type.create(mc.level, net.minecraft.world.entity.EntitySpawnReason.COMMAND)")
])
replace_one("common/blockentities/render/TableRenderer.java",[
 ("poseStack.mulPose(Axis.XP.rotationDegrees(90f));",
  "poseStack.mulPose(new org.joml.Matrix4f().rotate(Axis.XP.rotationDegrees(90f)));")
])
replace_one("client/model/FluidTextureModel.java",[
 ("mutable.setSpriteAndMoveUv(sprite, mutable.requiredChunkLayer(), mutable.requiredItemRenderType())",
  "mutable.setSpriteAndMoveUv(sprite, mutable.requiredChunkLayer(), mutable.requiredItemRenderType(), mutable.itemGlintRenderType(), mutable.itemGlintSpecialRenderType())")
])
replace_one("compat/port/legacy/ItemHandlerHelper.java",[
 ("player.drop(copy,false)","player.drop(copy,false,net.minecraft.util.Prediction.SERVER_ONLY)")
])
replace_one("menu/SmelteryMenu.java",[
 ("player.drop(s, false)","player.drop(s, false, net.minecraft.util.Prediction.SERVER_ONLY)")
])

# Modern fluid stack capability, no obsolete FluidUtil. The tank is already a
# ResourceHandler<FluidResource> via TransactionalFluidTank.
replace_one("common/blocks/SearedTankBlock.java",[
 ("import net.neoforged.neoforge.fluids.FluidUtil;","import net.neoforged.neoforge.transfer.fluid.FluidUtil;"),
 ("FluidUtil.interactWithFluidHandler(player, hand, handler)",
  "FluidUtil.interactWithFluidHandler(player, hand, pos, tank.getFluidResourceHandler(), null)")
])

# Smeltery bucket slot: use the actual 26.3 resource transfer API,
# and an ItemAccess wrapping slot 0 through the existing transactional adapter.
# Transfer ensures fluid and item changes are atomically committed.
def modern_bucket(s):
 s=s.replace("import net.neoforged.neoforge.fluids.FluidActionResult;","")
 s=s.replace("import net.neoforged.neoforge.fluids.FluidUtil;","")
 anchor="""    @SuppressWarnings("removal")
    private void processBucket() {"""
 start=s.index(anchor)
 finish=s.index("\n    @Override",start)
 replacement="""    private void processBucket() {
        if (isProcessingBucket || blockEntity == null || blockEntity.getLevel() == null
                || blockEntity.getLevel().isClientSide()) return;
        ItemStack input = bucketHandler.getStackInSlot(0);
        if (input.isEmpty() || !bucketHandler.getStackInSlot(1).isEmpty()) return;
        isProcessingBucket = true;
        try {
            var itemHandler = new com.titammods.common.blockentities.TransactionalItemHandler(
                    () -> bucketHandler, true, true);
            var itemAccess = net.neoforged.neoforge.transfer.access.ItemAccess
                    .forHandlerIndexStrict(itemHandler, 0);
            var fluidItem = itemAccess.getCapability(
                    net.neoforged.neoforge.capabilities.Capabilities.Fluid.ITEM);
            if (fluidItem == null) return;
            int moved;
            try (var transaction = net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()) {
                var tank = blockEntity.fluidTank;
                moved = net.neoforged.neoforge.transfer.ResourceHandlerUtil.move(
                        fluidItem, tank, fluid -> true, 1000, transaction);
                if (moved == 0) moved = net.neoforged.neoforge.transfer.ResourceHandlerUtil.move(
                        tank, fluidItem, fluid -> true, 1000, transaction);
                if (moved == 0) return;
                transaction.commit();
            }
            // Changes to the bucket are committed. Move the newly empty/filled
            // bucket to output once, after committing the fluid transaction.
            ItemStack changedBucket = bucketHandler.extractItem(0, 1, false);
            if (!changedBucket.isEmpty()) bucketHandler.setStackInSlot(1, changedBucket);
            blockEntity.setChanged();
        } finally {
            isProcessingBucket = false;
        }
    }
"""
 return s[:start]+replacement+s[finish:]
modify("menu/SmelteryMenu.java",modern_bucket)
print("26.3 API migration applied: block states, graphics, input, bucket transaction, screen.")
