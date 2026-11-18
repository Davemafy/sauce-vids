"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.planCameraRig = planCameraRig;
/** Deterministic spring camera rig. No wall-clock, randomness or DOM reads.
 * All values are computed sequentially once; any output frame is seekable.
 */
const types_1 = require("./types");
const timeWarp_1 = require("./timeWarp");
class Spring {
    mass;
    stiffness;
    damping;
    position;
    velocity = 0;
    constructor(initial, mass, stiffness, damping) {
        this.mass = mass;
        this.stiffness = stiffness;
        this.damping = damping;
        this.position = initial;
    }
    step(target, dt) {
        if (dt <= 0)
            return this.position;
        const omega = Math.sqrt(this.stiffness / this.mass);
        const zeta = this.damping / (2 * Math.sqrt(this.stiffness * this.mass));
        const y = this.position - target, v = this.velocity;
        let yn, vn;
        if (Math.abs(zeta - 1) < 1e-8) {
            const a = v + omega * y, d = Math.exp(-omega * dt);
            yn = (y + a * dt) * d;
            vn = (v - omega * a * dt) * d;
        }
        else if (zeta < 1) {
            const alpha = zeta * omega, wd = omega * Math.sqrt(1 - zeta * zeta);
            const co = Math.cos(wd * dt), si = Math.sin(wd * dt), d = Math.exp(-alpha * dt);
            yn = d * (y * co + (v + alpha * y) * si / wd);
            vn = d * (v * co - (alpha * v + omega * omega * y) * si / wd);
        }
        else {
            const root = Math.sqrt(zeta * zeta - 1), r1 = -omega * (zeta - root), r2 = -omega * (zeta + root);
            const c1 = (v - r2 * y) / (r1 - r2), c2 = y - c1;
            yn = c1 * Math.exp(r1 * dt) + c2 * Math.exp(r2 * dt);
            vn = r1 * c1 * Math.exp(r1 * dt) + r2 * c2 * Math.exp(r2 * dt);
        }
        this.position = target + yn;
        this.velocity = vn;
        return this.position;
    }
}
function rounded(v, places) {
    const n = Number(v.toFixed(places));
    return Object.is(n, -0) ? 0 : n;
}
function safeBox(box) {
    return !!box && [box.x, box.y, box.width, box.height].every(types_1.finite)
        && box.width >= 2 && box.height >= 2;
}
function sampleCursor(events, startMs) {
    return events.filter(e => (e.type === "pointermove" || e.eventType === "pointermove")
        && (0, types_1.finite)(e.t) && (0, types_1.finite)(e.x) && (0, types_1.finite)(e.y))
        .map(e => ({ t: e.t - startMs, x: e.x, y: e.y }))
        .sort((a, b) => a.t - b.t);
}
function velocityAt(t, samples, hint) {
    let j = hint;
    while (j + 1 < samples.length && samples[j + 1].t <= t)
        j++;
    if (j < 1)
        return { x: 0, y: 0, index: j };
    const a = samples[j - 1], b = samples[j];
    const dt = (b.t - a.t) / 1000;
    if (dt <= 0 || t - b.t > 160 || dt > 0.45)
        return { x: 0, y: 0, index: j };
    return { x: (0, types_1.clamp)((b.x - a.x) / dt, -2000, 2000),
        y: (0, types_1.clamp)((b.y - a.y) / dt, -2000, 2000), index: j };
}
function planCameraRig(frameMap, heroMoments, events, preset, startMs, viewport = { width: 1280, height: 720 }, cutFrames = new Set()) {
    if (!(0, types_1.finite)(startMs) || viewport.width <= 0 || viewport.height <= 0)
        throw new Error("Invalid camera source viewport");
    const p = preset.camera, dt = 1 / preset.export.fps;
    const newSpring = (x) => new Spring(x, p.spring.mass, p.spring.stiffness, p.spring.damping);
    const centerX = viewport.width / 2, centerY = viewport.height / 2;
    const scale = newSpring(1), cx = newSpring(centerX), cy = newSpring(centerY);
    const rx = newSpring(0), ry = newSpring(0);
    const heroes = [...heroMoments].sort((a, b) => a.sourceMs - b.sourceMs);
    const cursors = sampleCursor(events, startMs);
    const gaze = (0, timeWarp_1.visualGazeTargets)(events, startMs, frameMap.length ? frameMap[frameMap.length - 1].sourceMs : 0);
    const out = [];
    let heroIndex = -1, cursorIndex = 0, gazeIndex = -1;
    for (let i = 0; i < frameMap.length; i++) {
        const sourceMs = frameMap[i].sourceMs;
        while (heroIndex + 1 < heroes.length && heroes[heroIndex + 1].sourceMs <= sourceMs)
            heroIndex++;
        const hero = heroIndex >= 0 ? heroes[heroIndex] : null;
        while (gazeIndex + 1 < gaze.length && gaze[gazeIndex + 1].sourceMs <= sourceMs)
            gazeIndex++;
        const candidate = gazeIndex >= 0 ? gaze[gazeIndex] : null;
        const attention = candidate && sourceMs - candidate.sourceMs < 1500 &&
            candidate.score >= .4 ? candidate : null;
        const modalClosed = hero?.kind === "modal" && events.some(e => {
            const k = (e.eventType || e.type).toLowerCase().replaceAll("_", "-");
            return ["modal-close", "modal-closed", "dialog-hidden", "dialog-closed"].includes(k)
                && e.t - startMs > hero.sourceMs && e.t - startMs <= sourceMs;
        });
        // An open dialog owns the camera even when a nested click becomes the
        // newest hero. The 2400ms foreground timer is not a camera cut signal.
        // Release only on an observed dialog-close event.
        const modalOwner = preset.id === "3d-launch" ? [...heroes].reverse().find(h => h.kind === "modal" && safeBox(h.box) && h.sourceMs <= sourceMs &&
            !events.some(e => {
                const k = (e.eventType || e.type).toLowerCase().replaceAll("_", "-");
                return ["dialog-hidden", "dialog-closed", "modal-close", "modal-closed"].includes(k)
                    && e.t - startMs > h.sourceMs && e.t - startMs <= sourceMs;
            })) : undefined;
        // Verified product outcomes deserve a reading shot. An ordinary click is
        // merely a trigger; a real feature commit can sustain the composition.
        // These are limits on how long an observed event owns the camera, not
        // invented freezes or fabricated source states.
        const ownershipMs = hero?.kind === "modal" ? 2400 :
            hero?.kind === "feature" ? 2600 : 1800;
        const active = hero && !modalClosed && sourceMs - hero.sourceMs <
            ownershipMs && safeBox(hero.box) ? hero : null;
        const nestedInModal = !!(modalOwner && hero && safeBox(hero.box) &&
            hero.box.x + hero.box.width / 2 >= modalOwner.box.x &&
            hero.box.x + hero.box.width / 2 <= modalOwner.box.x + modalOwner.box.width &&
            hero.box.y + hero.box.height / 2 >= modalOwner.box.y &&
            hero.box.y + hero.box.height / 2 <= modalOwner.box.y + modalOwner.box.height);
        // Only a genuine modal or an action inside it inherits modal framing.
        // A feature commit without a spatial target keeps its own camera beat.
        const modalCameraLocked = !!(modalOwner && (hero?.kind === "modal" || nestedInModal));
        // A click that mounts an observed modal within 300ms is a trigger, not a
        // camera destination. Hold the previous composition through the brief
        // latency, then spring directly to the *actual* modal rectangle when it
        // is mounted. Prevents the Connect Agent tooltip -> dialog double pan.
        const upcomingModal = (active?.kind === "click" && preset.id === "3d-launch")
            ? heroes.find(h => h.kind === "modal" && safeBox(h.box)
                && h.sourceMs > sourceMs && h.sourceMs - active.sourceMs <= 300
                && h.sourceMs >= active.sourceMs)
            : undefined;
        const cameraHero = upcomingModal ? null :
            (modalCameraLocked ? modalOwner : active);
        const box = cameraHero?.box || null;
        let desiredScale = 1, desiredX = centerX, desiredY = centerY, desiredRX = 0, desiredRY = 0;
        if (box) {
            const maxSafe = Math.min(p.scaleRange[1], (viewport.width - 96) / box.width, (viewport.height - 90) / box.height);
            desiredScale = (0, types_1.clamp)((cameraHero.kind === "modal" ? 1.31 : 1.19), p.scaleRange[0], Math.max(p.scaleRange[0], maxSafe));
            desiredX = (0, types_1.clamp)(box.x + box.width / 2, 0, viewport.width);
            desiredY = (0, types_1.clamp)(box.y + box.height / 2, 0, viewport.height);
        }
        if (p.mode === "perspective" && preset.id !== "3d-launch" &&
            !box && attention && !upcomingModal) {
            // Hyper-Cut may use ambient attention. 3D Launch is a deliberate film:
            // its camera stays wide and still until a recorded action or verified
            // visual result owns a shot. Gaze alone is not a product state change.
            desiredScale = (0, types_1.clamp)(1 + attention.score * .065, 1, p.scaleRange[1]);
            desiredX = (0, types_1.clamp)(attention.x, viewport.width * .22, viewport.width * .78);
            desiredY = (0, types_1.clamp)(attention.y, viewport.height * .22, viewport.height * .78);
        }
        if (p.mode === "perspective") {
            const v = velocityAt(sourceMs, cursors, cursorIndex);
            cursorIndex = v.index;
            // Pointer travel provides inertia, but never manufactures a pre-click
            // zoom. The camera can tilt slightly during approach.
            desiredRX = (0, types_1.clamp)(-p.maxTiltDeg * Math.tanh(v.y / 1550), -p.maxTiltDeg, p.maxTiltDeg);
            desiredRY = (0, types_1.clamp)(p.maxTiltDeg * Math.tanh(v.x / 1550), -p.maxTiltDeg, p.maxTiltDeg);
            if (hero?.kind === "feature" && sourceMs - hero.sourceMs < 2100) {
                // Micro-pivot explicitly tied to the recorded commit event.
                desiredRY = (0, types_1.clamp)(desiredRY + 1.65, -p.maxTiltDeg, p.maxTiltDeg);
                desiredRX = (0, types_1.clamp)(desiredRX - .65, -p.maxTiltDeg, p.maxTiltDeg);
            }
            if (box) {
                desiredRX += (0, types_1.clamp)((desiredY - centerY) / viewport.height * .6, -.35, .35);
                desiredRY += (0, types_1.clamp)((desiredX - centerX) / viewport.width * .6, -.35, .35);
            }
            desiredRX = (0, types_1.clamp)(desiredRX, -p.maxTiltDeg, p.maxTiltDeg);
            desiredRY = (0, types_1.clamp)(desiredRY, -p.maxTiltDeg, p.maxTiltDeg);
        }
        if (preset.id === "3d-launch" && p.mode === "perspective" &&
            (modalCameraLocked || hero?.kind !== "feature")) {
            // One deliberate modal angle across its real child clicks; unrelated
            // feature commits keep their verified independent micro-pivot.
            // The approved 180/24/1 spring and 1200px projection are unchanged.
            desiredRX = modalCameraLocked ? .30 : 0;
            desiredRY = modalCameraLocked ? -.40 : 0;
        }
        if (preset.id === "3d-launch" && p.mode === "perspective" &&
            p.orbit.enabled && modalCameraLocked) {
            // The exact second-order Spring dynamics already exist above. Drive
            // their angular targets along a slow, bounded orbit using the fixed
            // output clock; the modal remains center-locked and source-true.
            // 2200ms avoids a perceptible oscillation within the 3.28s proof.
            const phase = 2 * Math.PI * i * dt * 1000 / p.orbit.periodMs;
            desiredRX = (0, types_1.clamp)(desiredRX +
                p.orbit.amplitudeXDeg * Math.sin(phase), -p.maxTiltDeg, p.maxTiltDeg);
            desiredRY = (0, types_1.clamp)(desiredRY +
                p.orbit.amplitudeYDeg * (Math.cos(phase) - 1), -p.maxTiltDeg, p.maxTiltDeg);
        }
        if (cutFrames.has(i)) {
            // Explicit editorial hard cut to the next verified action's composition.
            // Do not mutate the 180/24/1 physical spring parameters.
            for (const [spring, target] of [
                [scale, desiredScale], [cx, desiredX], [cy, desiredY],
                ...((p.orbit.enabled && modalCameraLocked) ? [] :
                    [[rx, desiredRX], [ry, desiredRY]])
            ]) {
                spring.position = target;
                spring.velocity = 0;
            }
            if (p.orbit.enabled && modalCameraLocked && i > 0) {
                rx.step(desiredRX, dt);
                ry.step(desiredRY, dt);
            }
        }
        else if (i > 0) {
            scale.step(desiredScale, dt);
            cx.step(desiredX, dt);
            cy.step(desiredY, dt);
            rx.step(desiredRX, dt);
            ry.step(desiredRY, dt);
        }
        out.push({
            scale: +(0, types_1.clamp)(scale.position, p.scaleRange[0], p.scaleRange[1]).toFixed(6),
            focusX: +(0, types_1.clamp)(cx.position, 0, viewport.width).toFixed(5),
            focusY: +(0, types_1.clamp)(cy.position, 0, viewport.height).toFixed(5),
            rotateXDeg: rounded((0, types_1.clamp)(rx.position, -p.maxTiltDeg, p.maxTiltDeg), 6),
            rotateYDeg: rounded((0, types_1.clamp)(ry.position, -p.maxTiltDeg, p.maxTiltDeg), 6),
            perspectivePx: p.perspectivePx,
            spotlightActive: !!box && p.spotlight.enabled && scale.position > 1.025,
            spotlightBox: box ? { ...box } : null,
            spotlightBlurPx: p.spotlight.blurPx,
            spotlightDimOpacity: p.spotlight.dimOpacity
        });
    }
    return out;
}
