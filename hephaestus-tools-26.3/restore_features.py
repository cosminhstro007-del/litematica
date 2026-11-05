#!/usr/bin/env python3
"""Restore Hephaestus Tools features to NeoForge 26.3 after first-pass migration.
This patch works on the isolated repository clone; original upstream remains untouched.
Original copyright titammods (MIT); unofficial compatibility adaptation.
"""
from pathlib import Path
import subprocess, sys, re

root=Path(sys.argv[1]).resolve()
base=Path("src/main/java/com/titammods/hephaestus_tools")
def upstream(rel):
    path=str(base/rel)
    return subprocess.check_output(["git","show","HEAD:"+path],cwd=root,text=True)
def write(rel,s):
    p=root/base/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(s,encoding="utf-8")
def assertreplace(s,a,b):
    assert a in s, "Missing source pattern: "+a[:100]
    return s.replace(a,b)

# Upgrade the original ghost/tool collector to the 26.3 submission API.
s=upstream("client/workbench/GhostCollector.java")
s=s.replace("import net.minecraft.client.renderer.texture.TextureAtlasSprite;",
"""import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.renderer.texture.UvMapping;
import net.minecraft.client.renderer.state.level.QuadParticleRenderState;
import net.minecraft.client.renderer.gizmos.DrawableGizmoPrimitives;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.minecraft.client.resources.model.geometry.ItemQuads;""")
s=assertreplace(s,"List<BakedQuad> quads, ItemStackRenderState.FoilType foilType)",
                 "ItemQuads quads, ItemStackRenderState.FoilType foilType)")
s=assertreplace(s,"new ArrayList<>(quads.size())","new ArrayList<>(quads.all().size())")
s=assertreplace(s,"for (BakedQuad quad : quads) if (shown(quad)) kept.add(quad);",
                 "for (BakedQuad quad : quads.all()) if (shown(quad)) kept.add(quad);")
s=assertreplace(s,"tintLayers, kept, foilType);","tintLayers, ItemQuads.split(kept), foilType);")
s,count=re.subn(r'(?ms)    @Override\n    public void submitNameTag\(.*?\n    \}\n(?=\n    @Override\n    public void submitText\()',
"""    @Override
    public void submitNameTag(PoseStack poseStack, @Nullable Vec3 nameTagAttachment, int offset, Component name,
                              boolean seeThrough, int lightCoords, CameraRenderState camera) {
        delegate.submitNameTag(poseStack, nameTagAttachment, offset, name, seeThrough, lightCoords, camera);
    }
""",s)
assert count==1, "submitNameTag"
s,count=re.subn(r'(?ms)    @Override\n    public <S> void submitModel\(.*?\n    \}\n(?=\n    @Override\n    public void submitModelPart\()',
"""    @Override
    public <S> void submitModel(Model<? super S> model, S state, PoseStack poseStack,
                                RenderType renderType, int lightCoords, int overlayCoords,
                                int tintedColor, @Nullable UvMapping uvMapping, int outlineColor) {
        delegate.submitModel(model, state, poseStack, renderType, lightCoords, overlayCoords,
                             tintedColor, uvMapping, outlineColor);
    }
""",s)
assert count==1, "submitModel"
s,count=re.subn(r'(?ms)    @Override\n    public void submitModelPart\(.*?\n    \}\n(?=\n    @Override\n    public void submitMovingBlock\()',
"""    @Override
    public void submitModelPart(ModelPart modelPart, PoseStack poseStack, RenderType renderType,
                                int lightCoords, int overlayCoords, @Nullable UvMapping uvMapping,
                                int tintedColor, int outlineColor) {
        delegate.submitModelPart(modelPart, poseStack, renderType, lightCoords, overlayCoords,
                                 uvMapping, tintedColor, outlineColor);
    }
""",s)
assert count==1, "submitModelPart"
s=s.replace("public void submitMovingBlock(PoseStack poseStack, MovingBlockRenderState movingBlockRenderState) {\n        delegate.submitMovingBlock(poseStack, movingBlockRenderState);",
            "public void submitMovingBlock(PoseStack poseStack, MovingBlockRenderState movingBlockRenderState, int outlineColor) {\n        delegate.submitMovingBlock(poseStack, movingBlockRenderState, outlineColor);")
s=s.replace("public void submitBreakingBlockModel(PoseStack poseStack, BlockStateModel model, long seed, int progress) {\n        delegate.submitBreakingBlockModel(poseStack, model, seed, progress);",
            "public void submitBreakingBlockModel(PoseStack poseStack, List<BlockStateModelPart> parts, int progress, boolean translucent) {\n        delegate.submitBreakingBlockModel(poseStack, parts, progress, translucent);")
s,count=re.subn(r'(?ms)    @Override\n    public void submitParticleGroup\(.*?\n    \}\n',
"""    @Override
    public void submitQuadParticleGroup(QuadParticleRenderState particles) {
        delegate.submitQuadParticleGroup(particles);
    }

    @Override
    public void submitGizmoPrimitives(DrawableGizmoPrimitives.Group group, CameraRenderState camera, boolean onTop) {
        delegate.submitGizmoPrimitives(group, camera, onTop);
    }

    @Override
    public void submitShapeOutline(PoseStack pose, VoxelShape shape, RenderType type, int color,
                                   float width, boolean afterTerrain) {
        delegate.submitShapeOutline(pose, shape, type, color, width, afterTerrain);
    }

    @Override
    public void submitTextBackground(PoseStack pose, float x0, float y0, float x1, float y1,
                                     int color, Font.DisplayMode mode, int lightCoords) {
        delegate.submitTextBackground(pose, x0, y0, x1, y1, color, mode, lightCoords);
    }

    @Override
    public <S> void submitCrumblingOverlay(Model<? super S> model, S state, PoseStack pose,
                                            RenderType type, int light, int overlay, int tint,
                                            ModelFeatureRenderer.CrumblingOverlay crumbling) {
        delegate.submitCrumblingOverlay(model, state, pose, type, light, overlay, tint, crumbling);
    }
""",s)
assert count==1,"submitParticleGroup"
write("client/workbench/GhostCollector.java",s)

# Minecraft 26.3 now offers shape submission in collector, replacing buffer+ShapeRenderer.
s=upstream("client/renderer/HammerAoeRenderer.java")
s=s.replace("import com.mojang.blaze3d.vertex.VertexConsumer;", "")
s=s.replace("import net.minecraft.client.renderer.MultiBufferSource;", "import net.minecraft.client.renderer.SubmitNodeCollector;")
s=s.replace("import net.minecraft.client.renderer.ShapeRenderer;", "")
s=assertreplace(s,"public boolean render(BlockOutlineRenderState renderState, MultiBufferSource.BufferSource buffer,\n                              PoseStack poseStack, boolean translucentPass, LevelRenderState levelRenderState)",
              "public boolean render(BlockOutlineRenderState renderState, SubmitNodeCollector collector,\n                              PoseStack poseStack, LevelRenderState levelRenderState)")
s=assertreplace(s,"            VertexConsumer lineBuilder = buffer.getBuffer(RenderTypes.lines());\n","")
s=assertreplace(s,
"""                ShapeRenderer.renderShape(poseStack, lineBuilder, shape,
                        pos.getX() - camX, pos.getY() - camY, pos.getZ() - camZ,
                        AOE_COLOR, 2f);""",
"""                poseStack.pushPose();
                poseStack.translate(pos.getX() - camX, pos.getY() - camY, pos.getZ() - camZ);
                collector.submitShapeOutline(poseStack, shape, RenderTypes.lines(), AOE_COLOR, 2f, false);
                poseStack.popPose();""")
write("client/renderer/HammerAoeRenderer.java",s)

# Restore JEI material-specific tool-part subtype recognition; original casting interop
# depends on the separate Hephaestus Forge 26.1 module and remains conditional.
plugin="""package com.titammods.hephaestus_tools.compat.jei;

import com.titammods.hephaestus_tools.HephaestusTools;
import com.titammods.hephaestus_tools.materials.MaterialId;
import com.titammods.hephaestus_tools.registry.ModComponents;
import com.titammods.hephaestus_tools.registry.ModItems;
import mezz.jei.api.IModPlugin;
import mezz.jei.api.JeiPlugin;
import mezz.jei.api.ingredients.subtypes.ISubtypeInterpreter;
import mezz.jei.api.registration.ISubtypeRegistration;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import java.util.Set;

@JeiPlugin
public class HephaestusToolsJeiPlugin implements IModPlugin {
    private static final Identifier UID = Identifier.fromNamespaceAndPath(HephaestusTools.MOD_ID, "jei_plugin");
    @Override public Identifier getPluginUid() { return UID; }
    private static Set<Item> partItems() {
        return Set.of(
            ModItems.PICK_HEAD.get(), ModItems.HAMMER_HEAD.get(), ModItems.SMALL_AXE_HEAD.get(),
            ModItems.BROAD_AXE_HEAD.get(), ModItems.ADZE_HEAD.get(), ModItems.LARGE_PLATE.get(),
            ModItems.SMALL_BLADE.get(), ModItems.LARGE_BLADE.get(), ModItems.TOOL_HANDLE.get(),
            ModItems.TOUGH_HANDLE.get(), ModItems.TOOL_BINDING.get(), ModItems.TOUGH_BINDING.get(),
            ModItems.MACE_HEAD.get(), ModItems.SPEAR_HEAD.get(),
            ModItems.BOW_LIMB.get(), ModItems.BOWSTRING.get());
    }
    @Override public void registerItemSubtypes(ISubtypeRegistration reg) {
        ISubtypeInterpreter<ItemStack> interp = (stack, ctx) -> {
            MaterialId id = stack.get(ModComponents.PART_MATERIAL.get());
            return id == null ? "none" : id.toString();
        };
        for (Item part : partItems()) reg.registerSubtypeInterpreter(part, interp);
    }
}
"""
write("compat/jei/HephaestusToolsJeiPlugin.java",plugin)

# Restore the 26.3 data-driven block transformer for axe, shovel and hoe.
path=base/"tools/nbt/ToolStack.java"
p=root/path
s=p.read_text(encoding="utf-8")
old="if (stack.getItem() instanceof ModifiableItem modItem) modItem.applyToolComponents(stack, properties);"
assert s.count(old)>=2
s=s.replace(old,
"""if (stack.getItem() instanceof ModifiableItem modItem) {
            modItem.applyToolComponents(stack, properties);
            applyVanillaBlockTransformers(stack, modItem);
        }""")
token="    private static OptionalInt fingerprint("
assert token in s
s=s.replace(token,
"""    private static void applyVanillaBlockTransformers(ItemStack stack, ModifiableItem item) {
        net.minecraft.world.item.Item vanilla = null;
        if (item.categories().contains(com.titammods.hephaestus_tools.tools.item.ToolCategory.AXE))
            vanilla = net.minecraft.world.item.Items.IRON_AXE;
        else if (item.categories().contains(com.titammods.hephaestus_tools.tools.item.ToolCategory.SHOVEL))
            vanilla = net.minecraft.world.item.Items.IRON_SHOVEL;
        else if (item.categories().contains(com.titammods.hephaestus_tools.tools.item.ToolCategory.HOE))
            vanilla = net.minecraft.world.item.Items.IRON_HOE;
        if (vanilla == null) {
            stack.remove(DataComponents.BLOCK_TRANSFORMER);
            return;
        }
        var transformer = new ItemStack(vanilla).get(DataComponents.BLOCK_TRANSFORMER);
        if (transformer != null) stack.set(DataComponents.BLOCK_TRANSFORMER, transformer);
    }

"""+token)
p.write_text(s,encoding="utf-8")

# Some old calls prevented base item fallback interactions entirely; defer to
# vanilla Item#useOn (which can use BLOCK_TRANSFORMER).
p=root/base/"tools/item/ModifiableItem.java"
s=p.read_text(encoding="utf-8")
old="""        // 26.3: old ItemAbilities are replaced by block transformer data components.
        return InteractionResult.PASS;"""
assert old in s
p.write_text(s.replace(old,
"""        // Minecraft 26.3 uses the BLOCK_TRANSFORMER component for these operations.
        return super.useOn(ctx);"""),encoding="utf-8")

p=root/"gradle.properties"
s=p.read_text(encoding="utf-8").replace("1.0.11-unofficial-26.3-beta2","1.0.11-unofficial-26.3-beta3")
p.write_text(s,encoding="utf-8")
print("Restored ghost tint renderer, AOE outlines, JEI material subtypes, and block transformers.")
