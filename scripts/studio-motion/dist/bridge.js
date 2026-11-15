"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.buildStudioPlan = buildStudioPlan;
/** Main renderer bridge: input JSON from Python stdin -> deterministic plan JSON. */
const node_fs_1 = require("node:fs");
const types_1 = require("./types");
const timeWarp_1 = require("./timeWarp");
const KineticCallouts_1 = require("./KineticCallouts");
const StudioStage_1 = require("./StudioStage");
function buildStudioPlan(input) {
    const c = { ...types_1.DEFAULT_STUDIO_CONFIG, ...input.config };
    if (!Number.isInteger(c.calloutCooldownMs) || c.calloutCooldownMs < 0)
        throw new Error("Invalid calloutCooldownMs");
    const floor = (0, StudioStage_1.createStudioStage)(c.floorReflectionIntensity);
    const time = (0, timeWarp_1.buildTimeWarp)(input.events, input.startMs, input.durationMs, input.fps, c.maxWarpSpeed, c.enableTimeWarp);
    const callouts = (0, KineticCallouts_1.buildCallouts)(input.events, input.startMs, time.sourceToOutput, { cooldownMs: c.calloutCooldownMs, lifetimeMs: c.maxCalloutLifetimeMs, enable: c.enableCallouts });
    return { schema: "sauce-studio-motion-v1", fps: input.fps, sourceDurationMs: input.durationMs,
        outputDurationMs: time.outputDurationMs, frameMap: time.frameMap,
        actionWindows: time.actionWindows, deadZones: time.deadZones, callouts,
        stage: { width: floor.width, height: floor.height, window: floor.window,
            reflectionIntensity: floor.reflectionIntensity, enabled: c.enableStudioFloor }, config: c };
}
// Real Node stdout stays JSON-only; any diagnostic is written to stderr.
if (require.main === module) {
    try {
        const src = (0, node_fs_1.readFileSync)(0, "utf8");
        const input = JSON.parse(src);
        if (!Array.isArray(input.events) || !(0, types_1.finite)(input.fps))
            throw new Error("Malformed bridge trace");
        process.stdout.write(JSON.stringify(buildStudioPlan(input)));
    }
    catch (err) {
        process.stderr.write(String(err) + "\n");
        process.exitCode = 1;
    }
}
