#!/usr/bin/env python3
"""Diagnostic first pass to port Hephaestus Tools 26.1.2 -> NeoForge 26.3.
Original authors: titammods, MIT. Unofficial, experimental adaptation.
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()
assert (root / "build.gradle").is_file()
def read(path):
    return (root / path).read_text(encoding="utf-8")
def write(path, content):
    (root / path).write_text(content, encoding="utf-8")
def disable(path):
    p = root / path
    if p.exists(): p.rename(p.with_suffix(".java.disabled"))

props = read("gradle.properties")
updates = {
    "minecraft_version": "26.3",
    "minecraft_version_range": "[26.3]",
    "neoforge_version": "26.3.0.101",
    "mod_version": "1.0.11-unofficial-port.1",
    "jei_version": "31.17.0.108",
    "pal_version": "1.2.8+mc.26.3",
}
for key, value in updates.items():
    props, n = re.subn(rf"(?m)^{re.escape(key)}=.*$", f"{key}={value}", props)
    if not n: props += f"\n{key}={value}"
write("gradle.properties", props)

gradle = read("build.gradle")
gradle = gradle.replace("id 'net.neoforged.moddev' version '2.0.141'", "id 'net.neoforged.moddev' version '2.0.148'")
gradle = gradle.replace("jei-26.1.2-neoforge", "jei-$" + "{minecraft_version}-neoforge")
lines=[]
for line in gradle.splitlines():
    if "curse.maven:" in line and any(s in line for s in (
        "hephaestus-forge-", "athena-", "jade-", "ftb-materials-",
        "ftb-library-forge-")): continue
    lines.append(line)
gradle = "\n".join(lines) + "\n"
gradle, n = re.subn(
    r'(?ms)^    implementation\("com\.zigythebird\.playeranim:PlayerAnimationLibNeo:\$\{pal_version\}"\) \{.*?^    \}\s*\n',
    '    implementation "curse.maven:player-animation-library-1283899:9080979"\n',
    gradle
)
assert n == 1, "Could not replace old PAL dependency"
write("build.gradle", gradle)

toml = read("src/main/resources/META-INF/neoforge.mods.toml")
toml = toml.replace('license="All rights reserved"', 'license="MIT"')
toml = toml.replace('versionRange="[26.1.1,26.1.2]"', 'versionRange="[26.3]"')
write("src/main/resources/META-INF/neoforge.mods.toml", toml)

for file in (
    "src/main/java/com/titammods/hephaestus_tools/mixin/TableBlockEntityMixin.java",
    "src/main/java/com/titammods/hephaestus_tools/compat/jei/CastingRecipeSync.java",
    "src/main/java/com/titammods/hephaestus_tools/compat/jei/HephaestusToolsJeiPlugin.java",
): disable(file)

main = "src/main/java/com/titammods/hephaestus_tools/HephaestusTools.java"
body = read(main)
body = body.replace("import com.titammods.hephaestus_tools.compat.jei.CastingRecipeSync;\n", "")
body = body.replace("import net.neoforged.fml.ModList;\n", "")
body = body.replace("import net.neoforged.neoforge.common.NeoForge;\n", "")
body = body.replace("""        if (ModList.get().isLoaded(FORGE_MOD_ID)) {
            NeoForge.EVENT_BUS.addListener(CastingRecipeSync::onDatapackSync);
        }
""", "")
write(main, body)

plugin = "src/main/java/com/titammods/hephaestus_tools/compat/ForgeMixinPlugin.java"
s = read(plugin)
s, n = re.subn(r"(?ms)    @Override\s+public List<String> getMixins\(\) \{.*?^    \}", """    @Override
    public List<String> getMixins() {
        return List.of(); // Forge 26.3 integration deferred
    }""", s)
assert n == 1
write(plugin, s)
print("Hephaestus Tools preliminary 26.3 adaptation applied.")
