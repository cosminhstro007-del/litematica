package com.fl0x.voidmaw.client;

import com.fl0x.voidmaw.VoidMawEntity;
import com.fl0x.voidmaw.VoidMawMod;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;

public final class VoidMawRenderer extends MobRenderer<VoidMawEntity, VoidMawRenderState, VoidMawModel> {
    public static final ModelLayerLocation LAYER = new ModelLayerLocation(VoidMawMod.id("void_maw"), "main");
    private static final Identifier TEXTURE = VoidMawMod.id("textures/entity/void_maw.png");

    public VoidMawRenderer(EntityRendererProvider.Context context) {
        super(context, new VoidMawModel(context.bakeLayer(LAYER)), 0.8F);
    }

    @Override
    public VoidMawRenderState createRenderState() { return new VoidMawRenderState(); }

    @Override
    public Identifier getTextureLocation(VoidMawRenderState state) { return TEXTURE; }

    @Override
    public void extractRenderState(VoidMawEntity entity, VoidMawRenderState state, float partialTick) {
        super.extractRenderState(entity, state, partialTick);
        state.attackTicks = entity.getAttackTicks();
        state.roarTicks = entity.getRoarTicks();
    }
}
