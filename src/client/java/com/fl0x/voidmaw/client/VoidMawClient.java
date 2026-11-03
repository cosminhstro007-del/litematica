package com.fl0x.voidmaw.client;

import com.fl0x.voidmaw.VoidMawMod;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.minecraft.client.renderer.entity.EntityRenderers;

public final class VoidMawClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        ModelLayerRegistry.registerModelLayer(VoidMawRenderer.LAYER, VoidMawModel::createLayer);
        EntityRenderers.register(VoidMawMod.VOID_MAW, VoidMawRenderer::new);
    }
}
