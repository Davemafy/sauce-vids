"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.buildCallouts = buildCallouts;
/** Conservative evidence-driven callouts. No fabricated action outcomes. */
const types_1 = require("./types");
const DANGER = /password|secret|token|api.?key|credit.?card|otp|verification code/i;
function compact(raw) {
    const text = raw.replace(/[\r\n\t]+/g, " ").replace(/\s+/g, " ").trim()
        .replace(/^\s*(click|tap|press)\s+/i, "").replace(/\b(your|the|a|an)\b/gi, "")
        .replace(/\s+/g, " ").trim().replace(/\s*\.{3,}.*$/, "");
    if (!text || text.length > 58 || DANGER.test(text))
        return "";
    return text.split(" ").slice(0, 4).map(word => /^[A-Z]{2,}$/.test(word) ? word : (word[0]?.toUpperCase() || "") + word.slice(1)).join(" ").replace(/[.,:;!]+$/, "");
}
function nameOf(e) {
    const direct = e.ariaLabel || e.innerText;
    if (direct?.trim())
        return compact(direct);
    const s = e.selector || "";
    // Pre-v20 traces only have Playwright selectors; use only explicit text().
    const m = /:has-text\((['"])(.*?)\1\)|:text-is\((['"])(.*?)\3\)/.exec(s);
    return compact(m?.[2] || m?.[4] || "");
}
function isPrimary(e) {
    const k = (e.eventType || e.type).toLowerCase().replaceAll("_", "-");
    if (["submit", "modal-open", "dialog-visible"].includes(k))
        return true;
    if (!["click", "pointerdown"].includes(k))
        return false;
    const tag = (e.tag || "").toLowerCase(), role = (e.role || "").toLowerCase(), selector = e.selector || "";
    return tag === "button" || role === "button" || /^button(?:[:.\[]|$)/i.test(selector)
        || /\[role=["']?button/.test(selector);
}
function buildCallouts(events, startMs, sourceToOutput, options) {
    if (!options.enable)
        return [];
    if (!(0, types_1.finite)(options.cooldownMs) || options.cooldownMs < 0 || !(0, types_1.finite)(options.lifetimeMs) || options.lifetimeMs <= 0)
        throw new Error("Invalid callout timing");
    const hold = Math.min(1800, options.lifetimeMs);
    const approved = events.filter(e => (0, types_1.finite)(e.t) && e.box && isPrimary(e))
        .sort((a, b) => a.t - b.t);
    const out = [];
    let last = -Infinity;
    for (const e of approved) {
        const label = nameOf(e);
        if (!label || !e.box)
            continue;
        const t = Math.max(0, e.t - startMs), mapped = sourceToOutput(t);
        if (mapped - last < options.cooldownMs)
            continue;
        const b = e.box;
        if (![b.x, b.y, b.width, b.height].every(types_1.finite) || b.width < 2 || b.height < 2)
            continue;
        // Reject full-screen backdrop; dialogs need a real title to trigger.
        if (b.width > 1100 || b.height > 650)
            continue;
        out.push({ text: label, kind: e.eventType || e.type,
            sourceStartMs: +t.toFixed(3), outputStartMs: +mapped.toFixed(3),
            outputEndMs: +(mapped + hold).toFixed(3), box: { x: b.x, y: b.y, width: b.width, height: b.height } });
        last = mapped;
    }
    return out;
}
