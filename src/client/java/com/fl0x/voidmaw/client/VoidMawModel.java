package com.fl0x.voidmaw.client;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

/** Cuboid horror anatomy + procedural idle, locomotion, strike, and shriek animation. */
public final class VoidMawModel extends EntityModel<VoidMawRenderState> {
    private final ModelPart head, jaw, body, leftArm, rightArm, leftLeg, rightLeg;

    public VoidMawModel(ModelPart root) {
        super(root);
        head = root.getChild("head");
        jaw = head.getChild("jaw");
        body = root.getChild("body");
        leftArm = root.getChild("left_arm");
        rightArm = root.getChild("right_arm");
        leftLeg = root.getChild("left_leg");
        rightLeg = root.getChild("right_leg");
    }

    public static LayerDefinition createLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition skull = root.addOrReplaceChild("head",
                CubeListBuilder.create().texOffs(0, 0).addBox(-10F, -23F, -6F, 20F, 23F, 12F),
                PartPose.offset(0F, 0F, 0F));
        skull.addOrReplaceChild("jaw",
                CubeListBuilder.create().texOffs(70, 0).addBox(-8F, 0F, -6.5F, 16F, 7F, 3F),
                PartPose.offset(0F, -7F, 0F));
        float[] fangX = {-7.6F, -4.8F, -1.4F, 2.2F, 5.4F};
        float[] fangLength = {3.9F, 5.1F, 3.2F, 5.3F, 4.0F};
        for (int i = 0; i < fangX.length; i++) {
            skull.addOrReplaceChild("fang_top_" + i,
                    CubeListBuilder.create().texOffs(184, 0).addBox(
                            fangX[i], -11.9F, -6.7F, 1.55F, fangLength[i], 1.4F),
                    PartPose.ZERO);
        }
        for (int i = 0; i < 4; i++) {
            skull.addOrReplaceChild("fang_bottom_" + i,
                    CubeListBuilder.create().texOffs(184, 0).addBox(
                            -6.0F + i * 3.75F, -4.2F, -7F, 1.45F, 3.4F + (i%2), 1.3F),
                    PartPose.ZERO);
        }
        root.addOrReplaceChild("body",
                CubeListBuilder.create().texOffs(120, 0).addBox(-7F, 0F, -4F, 14F, 14F, 8F),
                PartPose.ZERO);
        root.addOrReplaceChild("left_arm",
                CubeListBuilder.create().texOffs(0, 44).addBox(0F, -2F, -3.5F, 6F, 20F, 7F),
                PartPose.offset(8F, 1F, 0F));
        root.addOrReplaceChild("right_arm",
                CubeListBuilder.create().texOffs(35, 44).addBox(-6F, -2F, -3.5F, 6F, 20F, 7F),
                PartPose.offset(-8F, 1F, 0F));
        root.addOrReplaceChild("left_leg",
                CubeListBuilder.create().texOffs(68, 44).addBox(-2.5F, 0F, -3F, 5F, 11F, 6F),
                PartPose.offset(3.5F, 13F, 0F));
        root.addOrReplaceChild("right_leg",
                CubeListBuilder.create().texOffs(96, 44).addBox(-2.5F, 0F, -3F, 5F, 11F, 6F),
                PartPose.offset(-3.5F, 13F, 0F));
        return LayerDefinition.create(mesh, 256, 128);
    }

    @Override
    public void setupAnim(VoidMawRenderState s) {
        super.setupAnim(s);
        float age = s.ageInTicks;
        float move = Math.min(1F, s.walkAnimationSpeed);
        float step = s.walkAnimationPos * 0.7F;
        float stride = (float)Math.cos(step) * 0.8F * move;
        leftLeg.xRot = stride;
        rightLeg.xRot = -stride;
        head.yRot = s.yRot * ((float)Math.PI / 180F);
        head.xRot = s.xRot * ((float)Math.PI / 180F) + 0.035F * (float)Math.sin(age * 0.085F);
        body.xRot = 0.04F * (float)Math.sin(age * 0.07F);
        jaw.xRot = 0.08F + 0.055F * (float)Math.sin(age * 0.17F);
        leftArm.zRot = -1.02F;
        rightArm.zRot = 1.02F;
        leftArm.xRot = -0.16F - stride * 0.55F;
        rightArm.xRot = -0.16F + stride * 0.55F;
        if (s.attackTicks > 0) {
            float phase = (15F - Math.min(15, s.attackTicks)) / 15F;
            float impact = (float)Math.sin(phase * Math.PI);
            leftArm.xRot -= 1.55F * impact;
            rightArm.xRot -= 1.55F * impact;
            leftArm.zRot -= 0.21F * impact;
            rightArm.zRot += 0.21F * impact;
            head.xRot -= 0.32F * impact;
            jaw.xRot += 0.52F * impact;
        }
        if (s.roarTicks > 0) {
            float power = Math.min(1F, s.roarTicks / 6F);
            jaw.xRot += 0.70F * power;
            head.xRot -= 0.19F * power;
            leftArm.zRot -= 0.36F * power;
            rightArm.zRot += 0.36F * power;
            leftArm.xRot += 0.12F * (float)Math.sin(age * 1.1F);
            rightArm.xRot -= 0.12F * (float)Math.sin(age * 1.1F);
        }
    }
}
