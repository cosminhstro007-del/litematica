package fi.dy.masa.litematica.compat.iris;

import java.lang.reflect.Method;

import com.mojang.renderpearl.api.pipeline.RenderPipeline;

import fi.dy.masa.malilib.MaLiLibFabricData;
import fi.dy.masa.malilib.compat.ModIds;
import fi.dy.masa.litematica.Litematica;
import fi.dy.masa.litematica.render.LitematicaPipelines;

/**
 * Iris compatibility is kept reflection based on purpose.
 *
 * This keeps Litematica usable without Iris installed, while still letting
 * Iris 26.3 map Litematica's custom terrain pipelines to the correct shader
 * programs when Iris is present.
 */
public class IrisCompat
{
    private static boolean isSodiumLoaded = false;
    private static boolean isIrisLoaded = false;
    private static String sodiumVersion = "";
    private static String irisVersion = "";

    private static volatile boolean apiLookupDone = false;
    private static Object irisApi;
    private static Method shaderPackInUseMethod;
    private static Method shadowPassMethod;
    private static Method assignPipelineMethod;
    private static Class<? extends Enum> irisProgramClass;

    static
    {
        if (MaLiLibFabricData.ALL_MOD_VERSIONS.containsKey(ModIds.sodium))
        {
            sodiumVersion = MaLiLibFabricData.ALL_MOD_VERSIONS.get(ModIds.sodium);
            isSodiumLoaded = true;
        }
        if (MaLiLibFabricData.ALL_MOD_VERSIONS.containsKey(ModIds.iris))
        {
            irisVersion = MaLiLibFabricData.ALL_MOD_VERSIONS.get(ModIds.iris);
            isIrisLoaded = true;
        }

        Litematica.LOGGER.info("Sodium: [{}], Iris: [{}]", isSodiumLoaded ? sodiumVersion : "N/F", isIrisLoaded ? irisVersion : "N/F");
    }

    public static boolean hasSodium()
    {
        return isSodiumLoaded;
    }

    public static boolean hasIris()
    {
        return isSodiumLoaded && isIrisLoaded;
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static boolean ensureApi()
    {
        if (!hasIris())
        {
            return false;
        }

        if (apiLookupDone)
        {
            return irisApi != null;
        }

        synchronized (IrisCompat.class)
        {
            if (apiLookupDone)
            {
                return irisApi != null;
            }

            apiLookupDone = true;

            try
            {
                Class<?> apiClass = Class.forName("net.irisshaders.iris.api.v0.IrisApi");
                Class<?> programClass = Class.forName("net.irisshaders.iris.api.v0.IrisProgram");

                irisApi = apiClass.getMethod("getInstance").invoke(null);
                shaderPackInUseMethod = apiClass.getMethod("isShaderPackInUse");
                shadowPassMethod = apiClass.getMethod("isRenderingShadowPass");
                irisProgramClass = (Class<? extends Enum>) programClass.asSubclass(Enum.class);

                for (Method method : apiClass.getMethods())
                {
                    if (method.getName().equals("assignPipeline") && method.getParameterCount() == 2)
                    {
                        assignPipelineMethod = method;
                        break;
                    }
                }

                if (assignPipelineMethod == null)
                {
                    throw new NoSuchMethodException("IrisApi.assignPipeline(RenderPipeline, IrisProgram)");
                }

                Litematica.LOGGER.info("Iris 26.3 API detected; Litematica shader pipeline compatibility enabled");
                return true;
            }
            catch (Throwable t)
            {
                irisApi = null;
                shaderPackInUseMethod = null;
                shadowPassMethod = null;
                assignPipelineMethod = null;
                irisProgramClass = null;
                Litematica.LOGGER.warn("Unable to initialize Iris API compatibility; falling back to vanilla Litematica pipelines", t);
                return false;
            }
        }
    }

    public static boolean isShaderActive()
    {
        if (!ensureApi())
        {
            return false;
        }

        try
        {
            return Boolean.TRUE.equals(shaderPackInUseMethod.invoke(irisApi));
        }
        catch (Throwable t)
        {
            return false;
        }
    }

    public static boolean isShadowPassActive()
    {
        if (!ensureApi())
        {
            return false;
        }

        try
        {
            return Boolean.TRUE.equals(shadowPassMethod.invoke(irisApi));
        }
        catch (Throwable t)
        {
            return false;
        }
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static void assign(RenderPipeline pipeline, String programName) throws Exception
    {
        if (pipeline == null)
        {
            return;
        }

        Object program = Enum.valueOf((Class) irisProgramClass, programName);
        assignPipelineMethod.invoke(irisApi, pipeline, program);
    }

    public static void registerPipelines()
    {
        if (!ensureApi())
        {
            return;
        }

        try
        {
            assign(LitematicaPipelines.LEGACY_SOLID_TERRAIN, "TERRAIN_SOLID");
            assign(LitematicaPipelines.LEGACY_WIREFRAME, "LINES");
            assign(LitematicaPipelines.LEGACY_CUTOUT_TERRAIN, "TERRAIN_CUTOUT");

            assign(LitematicaPipelines.LEGACY_SOLID_TERRAIN_OFFSET, "TERRAIN_SOLID");
            assign(LitematicaPipelines.LEGACY_WIREFRAME_OFFSET, "LINES");
            assign(LitematicaPipelines.LEGACY_CUTOUT_TERRAIN_OFFSET, "TERRAIN_CUTOUT");

            assign(LitematicaPipelines.LEGACY_TRANSLUCENT, "TRANSLUCENT");
            assign(LitematicaPipelines.LEGACY_TRANSLUCENT_OFFSET, "TRANSLUCENT");

            Litematica.LOGGER.info("Assigned Litematica schematic terrain pipelines to Iris shader programs");
        }
        catch (Throwable t)
        {
            Litematica.LOGGER.warn("Failed to assign one or more Litematica pipelines to Iris", t);
        }
    }
}
