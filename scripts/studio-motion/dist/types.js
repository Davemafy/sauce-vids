"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DEFAULT_STUDIO_CONFIG = void 0;
exports.finite = finite;
exports.clamp = clamp;
exports.DEFAULT_STUDIO_CONFIG = {
    enableTimeWarp: false,
    maxWarpSpeed: 4,
    enableStudioFloor: false,
    floorReflectionIntensity: 0.25,
    enableCallouts: false,
    calloutCooldownMs: 2500,
    maxCalloutLifetimeMs: 1800,
};
function finite(v) { return typeof v === "number" && Number.isFinite(v); }
function clamp(v, a, b) { return Math.min(b, Math.max(a, v)); }
