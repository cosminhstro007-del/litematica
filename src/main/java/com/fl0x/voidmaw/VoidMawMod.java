package com.fl0x.voidmaw;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.SpawnEggItem;

public final class VoidMawMod implements ModInitializer {
    public static final String MOD_ID = "voidmaw";
    public static Identifier id(String path) { return Identifier.fromNamespaceAndPath(MOD_ID, path); }

    private static final ResourceKey<EntityType<?>> VOID_MAW_KEY = ResourceKey.create(
            Registries.ENTITY_TYPE, id("void_maw"));
    public static final EntityType<VoidMawEntity> VOID_MAW = Registry.register(
            BuiltInRegistries.ENTITY_TYPE,
            VOID_MAW_KEY,
            EntityType.Builder.<VoidMawEntity>of(VoidMawEntity::new, MobCategory.MONSTER)
                    .sized(1.15F, 2.9F)
                    .clientTrackingRange(10)
                    .build(VOID_MAW_KEY));

    private static final ResourceKey<Item> EGG_KEY = ResourceKey.create(
            Registries.ITEM, id("void_maw_spawn_egg"));
    public static final Item SPAWN_EGG = Registry.register(
            BuiltInRegistries.ITEM,
            EGG_KEY,
            new SpawnEggItem(new Item.Properties().setId(EGG_KEY).spawnEgg(VOID_MAW)));

    @Override
    public void onInitialize() {
        FabricDefaultAttributeRegistry.register(VOID_MAW, VoidMawEntity.createAttributes());
        CreativeModeTabEvents.modifyOutputEvent(CreativeModeTabs.SPAWN_EGGS)
                .register(entries -> entries.accept(SPAWN_EGG));
    }
}
