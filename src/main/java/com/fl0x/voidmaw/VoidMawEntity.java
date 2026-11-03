package com.fl0x.voidmaw;

import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

public final class VoidMawEntity extends Monster {
    private static final EntityDataAccessor<Integer> ATTACK_TICKS =
            SynchedEntityData.defineId(VoidMawEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> ROAR_TICKS =
            SynchedEntityData.defineId(VoidMawEntity.class, EntityDataSerializers.INT);
    private int lungeCooldown = 80;
    private int roarCooldown = 140;

    public VoidMawEntity(EntityType<? extends VoidMawEntity> type, Level level) {
        super(type, level);
        this.xpReward = 14;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 48.0D)
                .add(Attributes.ATTACK_DAMAGE, 9.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.32D)
                .add(Attributes.FOLLOW_RANGE, 36.0D)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.55D);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(ATTACK_TICKS, 0);
        builder.define(ROAR_TICKS, 0);
    }

    public int getAttackTicks() { return this.entityData.get(ATTACK_TICKS); }
    public int getRoarTicks() { return this.entityData.get(ROAR_TICKS); }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(1, new FloatGoal(this));
        goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.18D, true));
        goalSelector.addGoal(4, new WaterAvoidingRandomStrollGoal(this, 0.78D));
        goalSelector.addGoal(5, new LookAtPlayerGoal(this, Player.class, 16.0F));
        goalSelector.addGoal(6, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public void tick() {
        super.tick();
        if (this.level().isClientSide()) return;
        if (getAttackTicks() > 0) entityData.set(ATTACK_TICKS, getAttackTicks()-1);
        if (getRoarTicks() > 0) entityData.set(ROAR_TICKS, getRoarTicks()-1);
        if (lungeCooldown > 0) lungeCooldown--;
        if (roarCooldown > 0) roarCooldown--;

        LivingEntity target = getTarget();
        if (target == null || !target.isAlive()) return;
        double d2 = this.distanceToSqr(target);

        if (roarCooldown <= 0 && d2 < 14*14 && getRoarTicks() == 0) {
            entityData.set(ROAR_TICKS, 28);
            roarCooldown = 190 + random.nextInt(120);
            this.playSound(SoundEvents.WARDEN_ROAR, 1.55F, 0.74F);
        }

        if (lungeCooldown <= 0 && d2 > 4*4 && d2 < 11*11 && this.onGround()) {
            Vec3 towards = target.position().subtract(this.position()).normalize();
            this.setDeltaMovement(towards.x * 0.84D, 0.28D, towards.z * 0.84D);
            this.entityData.set(ATTACK_TICKS, 15);
            this.playSound(SoundEvents.WARDEN_ATTACK_IMPACT, 1.25F, 0.62F);
            lungeCooldown = 125 + random.nextInt(90);
        }
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity victim) {
        entityData.set(ATTACK_TICKS, 14);
        boolean landed = super.doHurtTarget(level, victim);
        if (landed) {
            this.playSound(SoundEvents.WARDEN_ATTACK_IMPACT, 0.95F, 0.85F);
            if (victim instanceof LivingEntity living) {
                living.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 45, 0), this);
            }
        }
        return landed;
    }

    @Override
    protected SoundEvent getAmbientSound() { return SoundEvents.WARDEN_AMBIENT; }
    @Override
    protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.WARDEN_HURT; }
    @Override
    protected SoundEvent getDeathSound() { return SoundEvents.WARDEN_DEATH; }
}
