from pathlib import Path
import subprocess

CORE = Path("core-src")
JAVA = CORE / "src/main/java"

OPTIONAL_IMPORTS = (
    "import mezz.jei.", "import dev.emi.emi.", "import me.shedaniel.rei.",
    "import me.shedaniel.math.", "import earth.terrarium.chipped.",
    "import net.blay09.mods.craftingtweaks.", "import top.theillusivec4.curios.",
    "import dev.emi.trinkets.", "import de.maxhenkel.", "import io.wispforest."
)
OPTIONAL_PATHS = (
    "/compat/jei/", "/compat/rei/", "/compat/emi/", "/compat/jade/",
    "/compat/chipped/", "/compat/craftingtweaks/", "/data/"
)

def git_show(rel: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(CORE), "show", f"HEAD:{rel}"],
        text=True,
        stderr=subprocess.DEVNULL,
    )

tracked = subprocess.check_output(
    ["git", "-C", str(CORE), "ls-files", "src/main/java/**/*.java"],
    text=True,
).splitlines()

restored = []
for rel in tracked:
    normalized = "/" + rel.replace("\\", "/")
    if rel.endswith("package-info.java") or any(token in normalized for token in OPTIONAL_PATHS):
        continue

    dst = CORE / rel
    if dst.exists():
        continue

    try:
        src = git_show(rel)
    except subprocess.CalledProcessError:
        continue

    is_client = (
        "/client/" in normalized
        or "import net.minecraft.client." in src
        or "import com.mojang.blaze3d." in src
        or "net.fabricmc.api.EnvType.CLIENT" in src
        or "@Environment(EnvType.CLIENT)" in src
    )
    if not is_client:
        continue
    if any(prefix in src for prefix in OPTIONAL_IMPORTS):
        continue

    # Keep datagen/recipe-provider-only code out of the runtime client pass.
    if "net.minecraft.data." in src and "/client/" not in normalized:
        continue

    src = src.replace("net.minecraft.resources.ResourceLocation", "net.minecraft.resources.Identifier")
    src = src.replace("ResourceLocation.fromNamespaceAndPath", "Identifier.fromNamespaceAndPath")
    src = src.replace("ResourceLocation.tryParse", "Identifier.tryParse")
    src = src.replace("ResourceLocation.parse", "Identifier.parse")
    src = src.replace("ResourceLocation", "Identifier")

    import_map = {
        "io.github.fabricators_of_create.porting_lib.util.DeferredRegister":
            "com.github.salandora.sophisticatedfabriclib.util.DeferredRegister",
        "io.github.fabricators_of_create.porting_lib.util.DeferredHolder":
            "com.github.salandora.sophisticatedfabriclib.util.DeferredHolder",
        "io.github.fabricators_of_create.porting_lib.fluids.BaseFlowingFluid":
            "com.github.salandora.sophisticatedfabriclib.fluid.api.v1.BaseFlowingFluid",
        "io.github.fabricators_of_create.porting_lib.fluids.FluidStack":
            "com.github.salandora.sophisticatedfabriclib.fluid.api.v1.FluidStack",
        "io.github.fabricators_of_create.porting_lib.fluids.FluidType":
            "com.github.salandora.sophisticatedfabriclib.fluid.api.v1.FluidType",
        "io.github.fabricators_of_create.porting_lib.transfer.fluid.SimpleFluidContent":
            "com.github.salandora.sophisticatedfabriclib.fluid.api.v1.SimpleFluidContent",
        "io.github.fabricators_of_create.porting_lib.transfer.fluid.block.BucketPickupHandlerWrapper":
            "com.github.salandora.sophisticatedfabriclib.fluid.api.v1.BucketPickupHandlerWrapper",
        "io.github.fabricators_of_create.porting_lib.transfer.item.ItemStackHandler":
            "io.github.fabricators_of_create.porting_lib.transfer.item.ItemStackHandler",
        "io.github.fabricators_of_create.porting_lib.transfer.TransferUtil":
            "com.github.salandora.sophisticatedfabriclib.transfer.api.v1.TransferUtil",
        "io.github.fabricators_of_create.porting_lib.transfer.MutableContainerItemContext":
            "com.github.salandora.sophisticatedfabriclib.transfer.api.v1.ItemStackContainerItemContext",
    }
    for old, new in import_map.items():
        src = src.replace(old, new)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src)
    restored.append(rel)

# The common pass deliberately installed safe stubs for these; restore their real client versions.
for rel in [
    "src/main/java/net/p3pp3rf1y/sophisticatedcore/upgrades/jukebox/StorageSoundHandler.java",
    "src/main/java/net/p3pp3rf1y/sophisticatedcore/client/gui/INameableEmptySlot.java",
]:
    dst = CORE / rel
    try:
        src = git_show(rel)
    except subprocess.CalledProcessError:
        continue
    src = src.replace("net.minecraft.resources.ResourceLocation", "net.minecraft.resources.Identifier")
    src = src.replace("ResourceLocation.fromNamespaceAndPath", "Identifier.fromNamespaceAndPath")
    src = src.replace("ResourceLocation", "Identifier")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src)
    if rel not in restored:
        restored.append(rel)

print(f"Restored {len(restored)} client/runtime Java files")
for rel in restored:
    print(rel)
