import { describe, expect, it } from "vitest";
import { FLAVORS, RECORDINGS, getJob, makeJobId, parseCompositorProgress, studioAvailable, submitJob } from "./studio-renderer";

describe("bounded Studio render catalog", () => {
  it("offers exactly three supported flavors and two verified recording IDs", () => {
    expect(FLAVORS).toEqual(["clean-studio", "3d-launch", "hyper-cut"]);
    expect(Object.keys(RECORDINGS)).toEqual(["brimble", "sauce"]);
    expect(RECORDINGS.sauce.workflow).toContain("studio-workspace-workflow.json");
  });
  it("produces deterministic safe job names from fixed catalog IDs", () => {
    expect(makeJobId("brimble", "3d-launch", true)).toBe("brimble-3d-launch-sound");
    expect(makeJobId("sauce", "clean-studio", false)).toBe("sauce-clean-studio-silent");
    expect(getJob("../../../../private")).toBeNull();
    expect(getJob("brimble-3d-launch-sound/../../secrets")).toBeNull();
  });
  it("uses actual frame counts, not fabricated job percentages", () => {
    expect(parseCompositorProgress("REPLAY 60 of 252 elapsed 28.2")).toEqual({done:60,total:252});
    expect(parseCompositorProgress("REPLAY 0 of 252\nREPLAY 120 of 252")).toEqual({done:120,total:252});
    expect(parseCompositorProgress("starting renderer")).toBeNull();
    expect(parseCompositorProgress("REPLAY 300 of 252")).toBeNull();
    expect(parseCompositorProgress("REPLAY 60 of 0")).toBeNull();
  });
  it("fails closed when the rendering worker is unconfigured", () => {
    const previous = process.env.SAUCE_STUDIO_ENABLED;
    delete process.env.SAUCE_STUDIO_ENABLED;
    try {
      expect(studioAvailable()).toBe(false);
      expect(() => submitJob("brimble", "3d-launch", true)).toThrow("unavailable");
    } finally {
      if(previous !== undefined) process.env.SAUCE_STUDIO_ENABLED = previous;
    }
  });
});
