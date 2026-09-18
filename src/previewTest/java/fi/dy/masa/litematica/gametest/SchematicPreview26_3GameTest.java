package fi.dy.masa.litematica.gametest;

import fi.dy.masa.litematica.config.Configs;
import fi.dy.masa.litematica.data.DataManager;
import fi.dy.masa.litematica.schematic.LitematicaSchematic;
import fi.dy.masa.litematica.schematic.placement.SchematicPlacement;
import fi.dy.masa.litematica.selection.AreaSelection;
import fi.dy.masa.litematica.selection.Box;
import fi.dy.masa.litematica.world.SchematicWorldHandler;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.Blocks;

@SuppressWarnings("UnstableApiUsage")
public final class SchematicPreview26_3GameTest implements FabricClientGameTest {
    @Override
    public void runTest(ClientGameTestContext context) {
        try (var world = context.worldBuilder().create()) {
            world.getServer().runCommand("gamemode creative @a");
            world.getServer().runCommand("fill 20 99 20 32 99 32 stone");
            world.getServer().runCommand("fill 20 100 20 32 104 32 air");

            String[] models = {
                    "bricks",
                    "glass",
                    "red_stained_glass",
                    "glass_pane",
                    "oak_leaves[persistent=true]",
                    "poppy",
                    "short_grass",
                    "oak_stairs[facing=east,half=bottom]",
                    "stone_slab[type=top]",
                    "oak_trapdoor[open=true,facing=west]",
                    "oak_fence",
                    "cobblestone_wall",
                    "repeater[facing=east,delay=3]",
                    "comparator[facing=west,mode=subtract]",
                    "redstone_wire",
                    "oak_door[half=lower,facing=south]",
                    "chest[facing=south]",
                    "oak_sign",
                    "water",
                    "stone_button[face=floor]"
            };

            for (int i = 0; i < models.length; i++) {
                int x = 20 + (i % 5) * 2;
                int z = 20 + (i / 5) * 3;
                world.getServer().runCommand("setblock " + x + " 100 " + z + " " + models[i]);
            }
            world.getServer().runCommand("setblock 20 101 29 oak_door[half=upper,facing=south]");

            context.waitFor(client -> client.level != null
                    && client.level.getBlockState(new BlockPos(20, 100, 20)).is(Blocks.BRICKS));

            context.computeOnClient(client -> {
                var area = new AreaSelection();
                area.setName("Litematica 26.3 preview render coverage");
                area.addSubRegionBox(new Box(new BlockPos(20, 100, 20),
                        new BlockPos(28, 102, 29), "models"), false);

                var schematic = LitematicaSchematic.createFromWorld(
                        client.level,
                        area,
                        new LitematicaSchematic.SchematicSaveInfo(false, true),
                        "Litematica CI",
                        message -> { throw new AssertionError(message); });

                if (schematic == null) {
                    throw new AssertionError("Failed to create real Litematica schematic");
                }

                var placement = SchematicPlacement.createFor(
                        schematic,
                        new BlockPos(-5, 100, 6),
                        "26.3 preview fixture",
                        true,
                        true);

                DataManager.getSchematicPlacementManager().addSchematicPlacement(placement, false);

                Configs.Visuals.ENABLE_RENDERING.setBooleanValue(true);
                Configs.Visuals.ENABLE_SCHEMATIC_RENDERING.setBooleanValue(true);
                Configs.Visuals.ENABLE_SCHEMATIC_BLOCKS.setBooleanValue(true);
                Configs.Visuals.ENABLE_SCHEMATIC_FLUIDS.setBooleanValue(true);
                Configs.Visuals.ENABLE_SCHEMATIC_OVERLAY.setBooleanValue(false);
                Configs.Visuals.RENDER_BLOCKS_AS_TRANSLUCENT.setBooleanValue(false);

                return placement;
            });

            context.waitFor(client -> SchematicWorldHandler.getSchematicWorld() != null
                    && SchematicWorldHandler.getSchematicWorld()
                    .getBlockState(new BlockPos(-5, 100, 6)).is(Blocks.BRICKS));

            // Remove the source fixture. From here on, the camera sees only the schematic preview.
            world.getServer().runCommand("fill 20 100 20 32 104 32 air");
            world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().forEach(player -> {
                player.getAbilities().flying = true;
                player.onUpdateAbilities();
            }));
            world.getServer().runCommand("tp @a -0.5 105 0.5");

            context.waitTicks(10);
            context.getInput().lookAt(new BlockPos(-1, 100, 10));
            context.waitTicks(140);
            context.takeScreenshot("litematica-26.3-preview-solid-overlay-off");

            context.runOnClient(client ->
                    Configs.Visuals.RENDER_BLOCKS_AS_TRANSLUCENT.setBooleanValue(true));
            context.waitTicks(100);
            context.takeScreenshot("litematica-26.3-preview-translucent-overlay-off");

            context.runOnClient(client ->
                    Configs.Visuals.ENABLE_SCHEMATIC_OVERLAY.setBooleanValue(true));
            context.waitTicks(60);
            context.takeScreenshot("litematica-26.3-preview-overlay-on");
        }
    }
}
