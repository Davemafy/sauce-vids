import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

export const FLAVORS = ["clean-studio", "3d-launch", "hyper-cut"] as const;
export type Flavor = (typeof FLAVORS)[number];
export const RECORDINGS = {
  brimble: {
    id: "brimble",
    title: "Brimble · Connect an agent",
    subtitle: "Live product UI · two verified interactions",
    session: "studio/.tmp/brimble-reference-v16-ink",
    workflow: "tests/fixtures/brimble-cinematic-workflow.json",
    seconds: 4.2,
    hideSelector: 'img[src*="bee-cutout"]',
  },
  sauce: {
    id: "sauce",
    title: "Sauce · Workspace creation",
    subtitle: "Local test app · modal, form and confirmation",
    session: "studio/.tmp/studio-workspace-v3",
    workflow: "tests/fixtures/studio-workspace-workflow.json",
    seconds: 4.2,
    hideSelector: null,
  },
} as const;
export type RecordingId = keyof typeof RECORDINGS;
export type JobState = "queued" | "rendering" | "ready" | "failed";
export interface RenderJob {
  id: string;
  recording: RecordingId;
  preset: Flavor;
  foley: boolean;
  state: JobState;
  createdAt: number;
  updatedAt?: number;
  phase?: "queued" | "compositing" | "finishing" | "complete";
  framesRendered?: number;
  framesTotal?: number;
  message?: string;
  output?: string;
}
declare global {
  // Shared across Next.js route modules within a single Node worker.
  var __sauceStudioJobs: Map<string, RenderJob> | undefined;
  var __sauceStudioQueue: string[] | undefined;
  var __sauceStudioBusy: boolean | undefined;
}
const jobs = globalThis.__sauceStudioJobs ??= new Map<string, RenderJob>();
const queue = globalThis.__sauceStudioQueue ??= [];
const isFlavor = (x: unknown): x is Flavor =>
  typeof x === "string" && (FLAVORS as readonly string[]).includes(x);
const isRecording = (x: unknown): x is RecordingId =>
  typeof x === "string" && Object.prototype.hasOwnProperty.call(RECORDINGS, x);
const workspace = () => process.env.SAUCE_WORKSPACE_ROOT || path.resolve(process.cwd(), "../..");
const enabled = () => process.env.SAUCE_STUDIO_ENABLED === "1" && existsSync(
  path.join(workspace(), "scripts/produce_cinematic_demo.py")
);
const outputDir = (id: string) => path.join(workspace(), "studio/.tmp/studio-ui-jobs", id);
const success = (id: string) => {
  const dir = outputDir(id);
  return ["master-1080p60.mp4", "preview.mp4", "release.json"].every((f) => {
    const name = path.join(dir, f);
    return existsSync(name) && statSync(name).size > 100;
  });
};
export function parseCompositorProgress(output: string) {
  // The frame pass has a measurable ceiling; total job duration does not.
  const matches = [...output.matchAll(/REPLAY\s+(\d+)\s+of\s+(\d+)/g)];
  const latest = matches.at(-1);
  if (!latest) return null;
  const done = Number(latest[1]);
  const total = Number(latest[2]);
  if (!Number.isSafeInteger(done) || !Number.isSafeInteger(total) ||
      total <= 0 || done < 0 || done > total) return null;
  return { done, total };
}
export function studioAvailable() { return enabled(); }
export function makeJobId(recording: RecordingId, preset: Flavor, foley: boolean) {
  return `${recording}-${preset}-${foley ? "sound" : "silent"}`;
}
export function describeJob(job: RenderJob) {
  return {
    id: job.id, recording: job.recording, preset: job.preset,
    foley: job.foley, state: job.state,
    createdAt: job.createdAt, updatedAt: job.updatedAt,
    phase: job.phase, framesRendered: job.framesRendered,
    framesTotal: job.framesTotal, message: job.message,
    ...(job.state === "ready" ? {
      previewUrl: `${process.env.NEXT_PUBLIC_SAUCE_BASE_PATH || ""}/api/studio/jobs/${job.id}/media?type=preview`,
      masterUrl: `${process.env.NEXT_PUBLIC_SAUCE_BASE_PATH || ""}/api/studio/jobs/${job.id}/media?type=master`,
    } : {}),
  };
}
export function getJob(id: string) {
  if (!/^(brimble|sauce)-(clean-studio|3d-launch|hyper-cut)-(sound|silent)$/.test(id))
    return null;
  const recorded = jobs.get(id);
  if (recorded) return recorded;
  if (success(id)) {
    const [recording, ...rest] = id.split("-");
    const foley = id.endsWith("-sound");
    const preset = rest.slice(0, foley ? -1 : -1).join("-") as Flavor;
    const job: RenderJob = { id, recording: recording as RecordingId, preset, foley,
      state: "ready", createdAt: 0, output: outputDir(id) };
    jobs.set(id, job);
    return job;
  }
  return null;
}
function startNext() {
  if (globalThis.__sauceStudioBusy || queue.length === 0) return;
  const id = queue.shift()!;
  const job = jobs.get(id);
  if (!job || job.state !== "queued") return startNext();
  globalThis.__sauceStudioBusy = true;
  job.state = "rendering";
  job.phase = "compositing";
  job.updatedAt = Date.now();
  job.message = "Preparing the verified browser-frame composition";
  const rec = RECORDINGS[job.recording];
  const root = workspace();
  const dest = outputDir(id);
  mkdirSync(path.dirname(dest), { recursive: true, mode: 0o700 });
  const python = process.env.SAUCE_PYTHON_BIN ||
    path.join(root, "../.sauce-render-env/bin/python");
  const args = [
    path.join(root, "scripts/produce_cinematic_demo.py"),
    "--session", path.join(root, rec.session),
    "--workflow", path.join(root, rec.workflow),
    "--out", dest,
    "--seconds", String(rec.seconds),
    "--preset", job.preset,
    "--title", rec.title,
    "--description", "Recorded software transformed by the Sauce Motion Engine.",
    "--no-webgl-optics",
  ];
  if (rec.hideSelector) args.push("--presentation-hide-selector", rec.hideSelector);
  if (!job.foley) args.push("--mute-audio");
  const child = spawn(python, args, {
    cwd: root,
    stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
  });
  let diagnostics = "";
  let stdoutTail = "";
  child.stdout.on("data", (chunk: Buffer) => {
    // Only publish real frame counts emitted by the Sauce compositor.
    // Never send the raw renderer's stdout or private capture paths to users.
    stdoutTail = (stdoutTail + chunk.toString()).slice(-2048);
    const progress = parseCompositorProgress(stdoutTail);
    if (progress) {
      job.framesRendered = Math.max(job.framesRendered || 0, progress.done);
      job.framesTotal = progress.total;
      job.updatedAt = Date.now();
      job.message = "Compositing frame " + job.framesRendered + " of " + progress.total;
    }
  });
  child.stderr.on("data", (data: Buffer) => {
    diagnostics = (diagnostics + data.toString()).slice(-2000);
  });
  const renderStartedAt = Date.now();
  const outputCheck = setInterval(() => {
    if (job.state !== "rendering") return;
    const master = path.join(dest, "master-1080p60.mp4");
    if (existsSync(master) && statSync(master).mtimeMs >= renderStartedAt) {
      job.phase = "finishing";
      job.updatedAt = Date.now();
      job.message = "Master ready. Preparing the playable preview";
    }
  }, 3000);
  const timeout = setTimeout(() => child.kill("SIGKILL"), 240_000);
  let finished = false;
  const finish = (ok: boolean) => {
    if (finished) return;
    finished = true;
    clearTimeout(timeout);
    clearInterval(outputCheck);
    job.state = ok && success(id) ? "ready" : "failed";
    job.phase = job.state === "ready" ? "complete" : job.phase;
    job.updatedAt = Date.now();
    job.output = job.state === "ready" ? dest : undefined;
    // Do not leak filesystem paths, source URLs or stderr to browsers.
    job.message = job.state === "ready" ? "Render completed" : "Render failed. Review worker logs.";
    if (!ok) console.error("[Sauce studio render]", id, diagnostics.slice(-600));
    globalThis.__sauceStudioBusy = false;
    startNext();
  };
  child.once("error", () => finish(false));
  child.once("close", (code) => {
    if (job.state === "failed" || job.state === "ready") return;
    finish(code === 0);
  });
}
export function submitJob(recording: unknown, preset: unknown, foley: unknown) {
  if (!enabled()) throw new Error("unavailable");
  if (!isRecording(recording) || !isFlavor(preset) || typeof foley !== "boolean")
    throw new Error("invalid");
  const id = makeJobId(recording, preset, foley);
  if (success(id)) return getJob(id)!;
  const existing = jobs.get(id);
  if (existing && existing.state !== "failed") return existing;
  if (existing?.state === "failed") jobs.delete(id);
  // Hard bounded catalog: at most 2 recordings x 3 flavors x 2 Foley states.
  if (jobs.size >= 12) throw new Error("capacity");
  const job: RenderJob = {
    id, recording, preset, foley, state: "queued",
    createdAt: Date.now(), updatedAt: Date.now(), phase: "queued",
    message: "Waiting for the rendering worker",
  };
  jobs.set(id, job); queue.push(id); startNext();
  return job;
}
export function readMedia(id: string, type: "preview" | "master") {
  const job = getJob(id);
  if (!job || job.state !== "ready") return null;
  const filename = type === "preview" ? "preview.mp4" : "master-1080p60.mp4";
  // Only return fixed export filenames; raw HAR and session files never leave.
  return readFileSync(path.join(outputDir(id), filename));
}
