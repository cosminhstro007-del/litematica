package fi.dy.masa.litematica.render.schematic;

import java.util.List;
import java.util.Map;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.renderpearl.api.buffers.GpuBuffer;
import com.mojang.renderpearl.api.buffers.GpuBufferSlice;
import com.mojang.renderpearl.api.commands.RenderPass;
import com.mojang.renderpearl.api.pipeline.IndexType;
import com.mojang.renderpearl.api.pipeline.PrimitiveTopology;
import com.mojang.renderpearl.api.pipeline.RenderPipeline;
import com.mojang.renderpearl.api.textures.FilterMode;
import com.mojang.renderpearl.api.textures.GpuSampler;
import com.mojang.renderpearl.api.textures.GpuTextureView;
import net.minecraft.SharedConstants;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.chunk.ChunkSectionLayer;
import net.minecraft.client.renderer.chunk.ChunkSectionLayerGroup;
import net.minecraft.util.profiling.ProfilerFiller;

import fi.dy.masa.litematica.Litematica;

public record ChunkRenderBatchDraw(
        GpuTextureView atlasTexture,
        Map<ChunkSectionLayer, List<RenderPass.Draw<GpuBufferSlice[]>>> drawData,
        boolean renderCollidingBlocks,
        boolean renderTranslucent,
        int maxIndicesRequired,
        GpuBufferSlice[] dynamicTransforms
        )
{
    public void draw(RenderPass pass, final ChunkSectionLayerGroup group, final GpuSampler sampler, ProfilerFiller profiler)
    {
        RenderSystem.AutoStorageIndexBuffer defaultIndices = RenderSystem.getSequentialBuffer(PrimitiveTopology.QUADS);
        GpuBuffer defaultIBO = this.maxIndicesRequired() == 0 ? null : defaultIndices.getBuffer(this.maxIndicesRequired());
        IndexType indexType = this.maxIndicesRequired() == 0 ? null : defaultIndices.type();
        ChunkSectionLayer[] layers = group.layers();
        Minecraft mc = Minecraft.getInstance();
        boolean wf = SharedConstants.DEBUG_HOTKEYS && mc.wireframe;

        profiler.push("draw_group");

        try
        {
            RenderSystem.bindDefaultUniforms(pass);
            pass.setUniform("Sampler0", this.atlasTexture, sampler);
            pass.setUniform("Sampler2", mc.gameRenderer.lightmap(),
                            RenderSystem.getSamplerCache().getClampToEdge(FilterMode.LINEAR));

            for (ChunkSectionLayer layer : layers)
            {
                List<RenderPass.Draw<GpuBufferSlice[]>> draws = this.drawData().get(layer);
                profiler.popPush("draw_group_" + layer.label());

                if (draws == null || draws.isEmpty())
                {
                    continue;
                }

                if (layer.translucent())
                {
                    draws = draws.reversed();
                }

                RenderPipeline pipeline;
                if (wf)
                {
                    pipeline = this.renderCollidingBlocks()
                               ? ChunkRenderLayers.getWireframe().getRight()
                               : ChunkRenderLayers.getWireframe().getLeft();
                }
                else if (this.renderTranslucent())
                {
                    pipeline = this.renderCollidingBlocks()
                               ? ChunkRenderLayers.PIPELINE_MAP.get(ChunkSectionLayer.TRANSLUCENT).getRight()
                               : ChunkRenderLayers.PIPELINE_MAP.get(ChunkSectionLayer.TRANSLUCENT).getLeft();
                }
                else
                {
                    pipeline = this.renderCollidingBlocks()
                               ? ChunkRenderLayers.PIPELINE_MAP.get(layer).getRight()
                               : ChunkRenderLayers.PIPELINE_MAP.get(layer).getLeft();
                }

                pass.setPipeline(RenderSystem.getCompiledPipeline(pipeline));
                pass.drawMultipleIndexed(draws, defaultIBO, indexType,
                                         List.of("DynamicTransforms"), this.dynamicTransforms());
            }
        }
        catch (Exception e)
        {
            Litematica.LOGGER.error("Failed to draw schematic block preview in Minecraft 26.3", e);
        }
        finally
        {
            profiler.pop();
        }
    }
}
