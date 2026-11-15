"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DEFAULT_STAGE = void 0;
exports.createStudioStage = createStudioStage;
exports.projectAnchor = projectAnchor;
/** Studio stage parameters and perspective anchor projection.
 * Film pixels are rendered by Sauce's existing OpenCV homography compositor.
 * This mathematical contract shares the same 1820px focal length and tilt cap.
 */
const types_1 = require("./types");
exports.DEFAULT_STAGE = {
    width: 1920, height: 1080,
    window: { x: 220, y: 124, width: 1480, height: 832 },
    focalLength: 1820, maxTiltDegrees: 2.5,
    reflectionIntensity: .25, roughness: .35,
    contactShadowBlur: 13, ambientShadowBlur: 45,
};
function createStudioStage(reflectionIntensity) {
    if (!(0, types_1.finite)(reflectionIntensity) || reflectionIntensity < 0 || reflectionIntensity > .5)
        throw new Error("floorReflectionIntensity must be between 0 and 0.5");
    return { ...exports.DEFAULT_STAGE, reflectionIntensity };
}
function projectAnchor(box, camera, stage = exports.DEFAULT_STAGE) {
    if (!(0, types_1.finite)(box.x) || !(0, types_1.finite)(box.y) || !(0, types_1.finite)(box.width) || !(0, types_1.finite)(box.height) || box.width < 0 || box.height < 0)
        throw new Error("Invalid anchor box");
    const anchorX = box.x + box.width / 2;
    const anchorY = box.y;
    const { window: win } = stage;
    const rawX = win.x + camera.offsetX + anchorX * camera.sourceScale;
    const rawY = win.y + camera.offsetY + anchorY * camera.sourceScale;
    const cx = win.x + win.width / 2, cy = win.y + win.height / 2;
    const ax = (0, types_1.clamp)(camera.rotateX, -stage.maxTiltDegrees, stage.maxTiltDegrees) * Math.PI / 180;
    const ay = (0, types_1.clamp)(camera.rotateY, -stage.maxTiltDegrees, stage.maxTiltDegrees) * Math.PI / 180;
    const X = rawX - cx, Y = rawY - cy;
    const X1 = X * Math.cos(ay), Z1 = -X * Math.sin(ay);
    const Y2 = Y * Math.cos(ax) - Z1 * Math.sin(ax);
    const Z2 = Y * Math.sin(ax) + Z1 * Math.cos(ax);
    const perspective = stage.focalLength / (stage.focalLength - Z2);
    return { x: cx + X1 * perspective, y: cy + Y2 * perspective };
}
