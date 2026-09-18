package fi.dy.masa.litematica.mixin.easyplace;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import fi.dy.masa.litematica.config.Configs;
import fi.dy.masa.litematica.util.EasyPlaceUtils;
import net.minecraft.client.multiplayer.MultiPlayerGameMode;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Post Re-Write code
 */
@Mixin(value = MultiPlayerGameMode.class, priority = 980)
public class MixinClientPlayerInteractionManager_easyPlace
{
    @Inject(method = "useItemOn", at = @At("HEAD"), cancellable = true)
    private void litematica_onInteractBlock(LocalPlayer player, InteractionHand hand, BlockHitResult blockHit, CallbackInfoReturnable<InteractionResult> cir)
    {
        if (Configs.Generic.EASY_PLACE_MODE.getBooleanValue() &&
            Configs.Generic.EASY_PLACE_POST_REWRITE.getBooleanValue())
        {
            // Prevent recursion, since the Easy Place mode can call this code again
            if (EasyPlaceUtils.isHandling() == false)
            {
                if (EasyPlaceUtils.shouldDoEasyPlaceActions())
                {
                    boolean handled = EasyPlaceUtils.handleEasyPlaceWithMessage();

                    // When Easy Place is actively being used, never let the original
                    // vanilla block placement fall through outside the schematic.
                    // The actual Easy Place placement re-enters this method while
                    // EasyPlaceUtils.isHandling() is true, so that placement is not blocked.
                    if (handled || player.getItemInHand(hand).getItem() instanceof BlockItem)
                    {
                        cir.setReturnValue(InteractionResult.FAIL);
                    }
                }
                else
                {
                    if (Configs.Generic.PLACEMENT_RESTRICTION.getBooleanValue())
                    {
                        if (EasyPlaceUtils.handlePlacementRestriction())
                        {
                            cir.setReturnValue(InteractionResult.FAIL);
                        }
                    }
                }
            }
        }
    }

    // This causes double-placements
    @Inject(method = "performUseItemOn",
            at = @At(value = "INVOKE",
                     target = "Lnet/minecraft/client/player/LocalPlayer;getItemInHand(Lnet/minecraft/world/InteractionHand;)Lnet/minecraft/world/item/ItemStack;",
                     shift = At.Shift.BEFORE), cancellable = true)
    private void litematica_onInteractBlockInternal(LocalPlayer player, InteractionHand hand, BlockHitResult blockHit, CallbackInfoReturnable<InteractionResult> cir)
    {
        if (Configs.Generic.EASY_PLACE_MODE.getBooleanValue() &&
            Configs.Generic.EASY_PLACE_POST_REWRITE.getBooleanValue())
        {
            // Prevent recursion, since the Easy Place mode can call this code again
            if (EasyPlaceUtils.isHandling() == false)
            {
                if (EasyPlaceUtils.shouldDoEasyPlaceActions())
                {
                    boolean handled = EasyPlaceUtils.handleEasyPlaceWithMessage();

                    if (handled || player.getItemInHand(hand).getItem() instanceof BlockItem)
                    {
                        cir.setReturnValue(InteractionResult.FAIL);
                    }
                }
            }
        }
    }
}
