#version 330
#extension GL_ARB_separate_shader_objects : require

#include <minecraft:fog.glsl>
#include <minecraft:dynamictransforms.glsl>
#include <minecraft:oit.glsl>
#include <minecraft:texture_sampling.glsl>
#include <litematica:legacy_terrain_fix.glsl>

uniform sampler2D Sampler0;

layout(location = 0) in float sphericalVertexDistance;
layout(location = 1) in float cylindricalVertexDistance;
layout(location = 2) in vec4 vertexColor;
layout(location = 3) in vec2 texCoord0;
layout(location = 4) in float chunkVisibility;

#ifndef OIT_ALPHA_ONLY
layout(location = 0) out vec4 fragColor;
#endif

vec4 calculateFinalColor(vec4 color) {
    // Schematic preview blocks use camera-relative transforms that are separate from
    // vanilla terrain fog state on 26.3. Applying vanilla terrain fog here can turn
    // the entire schematic into FogColor (blue) even though atlas UVs are correct.
    // Keep OIT accumulation behavior, but do not fog schematic preview pixels.
    #ifdef OIT_ACCUMULATE
    color = sampleColorForAccumulation(color);
    #endif
    return color;
}

void main() {
    vec4 color = vec4(1, 1, 1, 1);
//    vec4 color = sampleNearest(Sampler0, texCoord0, 1.0f / TextureSize) * vertexColor * ColorModulator;
    if (hasShadersOn == 1) {
        color = sampleNearest(Sampler0, texCoord0, 1.0f / TextureSize) * vertexColor * ColorModulator;
    } else {
        color = (UseRgss == 1 ? sampleRGSS(Sampler0, texCoord0, 1.0f / TextureSize) : sampleNearest(Sampler0, texCoord0, 1.0f / TextureSize)) * vertexColor * ColorModulator;
    }
    #ifdef ALPHA_CUTOUT
    if (color.a < ALPHA_CUTOUT) {
        discard;
    }
    #endif
    #ifdef OIT_ALPHA_ONLY
    executeAlphaOnlyPhase(gl_FragCoord.z, color.a);
    #else
    fragColor = calculateFinalColor(color);
    #endif
}
