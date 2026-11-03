# Void Maw - Minecraft Java 26.3 (Fabric)
Custom horror monster with a large square face, hollow eyes, articulated jaw, distinct teeth, long arms, roaming + melee AI, lunge, shriek and Darkness debuff. Also has a pixel-art spawn egg.

**Build:** Java 25, Gradle 9.7.1, Fabric Loader 0.19.5, Fabric API 0.163.0+26.3.

This branch intentionally does not modify the original repository's default branch, which contains Litematica sources. It is an isolated project because the GitHub connector does not support repository creation.

GitHub Actions workflow installs Python/Pillow for deterministic texture generation and compiles the JAR.
After success, use Actions > Build Void Maw Fabric 26.3 > Artifacts.

Commands:
`/give @p voidmaw:void_maw_spawn_egg`
`/summon voidmaw:void_maw`

**Rendering caveat:** the reference picture was only a 2D render; the visible face and body colors are sampled while hidden sides are reconstructed.

## Build from a phone (if Actions did not start automatically)

Open this branch's README.md on the GitHub website, tap the pencil icon, add a blank line, and commit the small edit directly to `voidmaw-fabric-26.3`. A real browser commit triggers the `push` event for `.github/workflows/build.yml`. Then open the repository's **Actions** tab, choose **Build Void Maw Fabric 26.3**, and if successful download the `VoidMaw-Fabric-26.3-JAR` artifact. Use the JAR within that ZIP, not the sources JAR. The project has not yet been compiled or tested.

