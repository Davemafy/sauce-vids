"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.buildMotionEnginePlan = buildMotionEnginePlan;
exports.buildStudioPlan = buildStudioPlan;
/** Unified deterministic bridge. Legacy v1 contract stays backward-compatible.
 * When an explicit preset is selected, include the new FramePlan + FoleyPlan.
 */
const node_fs_1 = require("node:fs");
const types_1 = require("./types");
const timeWarp_1 = require("./timeWarp");
const KineticCallouts_1 = require("./KineticCallouts");
const StudioStage_1 = require("./StudioStage");
const presets_1 = require("./presets");
const autoDirector_1 = require("./autoDirector");
const foleyPlan_1 = require("./foleyPlan");
function parsePreset(input) {
    if (!input.preset)
        throw new Error("A Sauce preset must be selected");
    if (typeof input.preset === "string") {
        if (!presets_1.SAUCE_FLAVORS.includes(input.preset))
            throw new Error("Unsupported Sauce flavor");
        return (0, presets_1.resolvePreset)(input.preset, input.presetOverrides);
    }
    const selected = input.preset;
    if (!presets_1.SAUCE_FLAVORS.includes(selected.id))
        throw new Error("Unsupported Sauce flavor");
    return (0, presets_1.resolvePreset)(selected.id, selected);
}
function validateInput(input) {
    if (!Array.isArray(input.events) || !(0, types_1.finite)(input.startMs) ||
        !(0, types_1.finite)(input.durationMs) || input.durationMs <= 0 ||
        input.durationMs > 600000 || !Number.isInteger(input.fps) ||
        input.fps < 1 || input.fps > 120)
        throw new Error("Malformed bridge trace");
    if (!input.events.every(e => e && typeof e.type === "string" && (0, types_1.finite)(e.t)))
        throw new Error("Invalid trace events");
}
function buildMotionEnginePlan(input) {
    validateInput(input);
    const preset = parsePreset(input);
    if (preset.export.fps !== input.fps)
        throw new Error("Preset FPS must match the source/output render frame rate");
    const direction = (0, autoDirector_1.buildAutoDirector)(input.events, input.startMs, input.durationMs, preset);
    const foley = (0, foleyPlan_1.buildFoleyPlan)(input.events, input.startMs, input.durationMs, direction.framePlan.outputDurationMs, direction.timeWarp.sourceToOutput, preset, direction.framePlan.frames.map(f => f.camera), direction.framePlan.frames.map(f => ({ sourceMs: f.sourceMs, speed: f.speed })));
    return { schema: "sauce-motion-plan-v1", preset,
        framePlan: direction.framePlan, foleyPlan: foley };
}
function buildStudioPlan(input) {
    validateInput(input);
    // The initial rollout is opt-in. Existing Python v1 consumers continue
    // receiving their original layout, time map and silent audio semantics.
    if (input.preset !== undefined) {
        const motion = buildMotionEnginePlan(input);
        const preset = motion.preset, frame = motion.framePlan;
        const floor = (0, StudioStage_1.createStudioStage)(preset.stage.floorReflectionIntensity);
        return {
            schema: "sauce-studio-motion-v1",
            fps: input.fps, sourceDurationMs: input.durationMs,
            outputDurationMs: frame.outputDurationMs,
            frameMap: frame.frames.map(f => ({ sourceMs: f.sourceMs, speed: f.speed })),
            actionWindows: frame.actionWindows, deadZones: frame.deadZones,
            callouts: frame.callouts,
            stage: { width: floor.width, height: floor.height, window: floor.window,
                reflectionIntensity: floor.reflectionIntensity,
                enabled: preset.stage.floorReflectionIntensity > 0 },
            config: {
                enableTimeWarp: preset.director.enabled && preset.director.idleStrategy !== "hold",
                maxWarpSpeed: preset.director.maxWarpSpeed,
                enableStudioFloor: preset.stage.floorReflectionIntensity > 0,
                floorReflectionIntensity: preset.stage.floorReflectionIntensity,
                enableCallouts: preset.director.callouts.enabled,
                calloutCooldownMs: preset.director.callouts.cooldownMs,
                maxCalloutLifetimeMs: preset.director.callouts.maxLifetimeMs
            },
            motionEngine: motion
        };
    }
    const c = { ...types_1.DEFAULT_STUDIO_CONFIG, ...input.config };
    if (!Number.isInteger(c.calloutCooldownMs) || c.calloutCooldownMs < 0)
        throw new Error("Invalid calloutCooldownMs");
    const floor = (0, StudioStage_1.createStudioStage)(c.floorReflectionIntensity);
    const time = (0, timeWarp_1.buildTimeWarp)(input.events, input.startMs, input.durationMs, input.fps, c.maxWarpSpeed, c.enableTimeWarp);
    const callouts = (0, KineticCallouts_1.buildCallouts)(input.events, input.startMs, time.sourceToOutput, { cooldownMs: c.calloutCooldownMs,
        lifetimeMs: c.maxCalloutLifetimeMs, enable: c.enableCallouts });
    return {
        schema: "sauce-studio-motion-v1", fps: input.fps,
        sourceDurationMs: input.durationMs, outputDurationMs: time.outputDurationMs,
        frameMap: time.frameMap, actionWindows: time.actionWindows,
        deadZones: time.deadZones, callouts,
        stage: { width: floor.width, height: floor.height, window: floor.window,
            reflectionIntensity: floor.reflectionIntensity, enabled: c.enableStudioFloor },
        config: c
    };
}
// Stdout is JSON only. Diagnostics/errors are emitted to stderr.
if (require.main === module) {
    try {
        const input = JSON.parse((0, node_fs_1.readFileSync)(0, "utf8"));
        process.stdout.write(JSON.stringify(buildStudioPlan(input)));
    }
    catch (err) {
        process.stderr.write(String(err) + "\n");
        process.exitCode = 1;
    }
}
