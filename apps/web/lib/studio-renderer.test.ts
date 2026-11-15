import { describe, expect, it } from "vitest";
import { FLAVORS, RECORDINGS, getJob, makeJobId, studioAvailable, submitJob } from "./studio-renderer";

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
