import { expect, test } from "@playwright/test";

const prefix = process.env.NEXT_PUBLIC_SAUCE_BASE_PATH || "";

test("Studio preset picker, verified source and Foley toggle work on desktop", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(`${prefix}/studio`);
  await expect(page.getByRole("heading", { name: /make a recording worth watching/i })).toBeVisible();
  await expect(page.getByRole("combobox", { name: /verified source/i })).toHaveValue("brimble");
  await expect(page.getByRole("group", { name: "Motion preset" }).getByRole("button", { name: /3d launch/i })).toHaveAttribute("aria-pressed", "true");
  const cta = page.getByRole("button", { name: "Create film" });
  await expect(cta).toBeVisible();
  const box = await cta.boundingBox();
  expect(box?.y! + box?.height!).toBeLessThanOrEqual(720);

  await page.getByRole("button", { name: /hyper-cut/i }).click();
  await expect(page.getByText("Your Hyper-Cut film appears here.")).toBeVisible();
  await page.getByRole("switch", { name: /foley sound/i }).uncheck();
  await expect(page.getByRole("switch", { name: /foley sound/i })).not.toBeChecked();
  await page.getByRole("combobox", { name: /verified source/i }).selectOption("sauce");
  await expect(page.getByRole("combobox", { name: /verified source/i })).toHaveValue("sauce");
  const sizes = await page.evaluate(() => [document.documentElement.scrollWidth, innerWidth]);
  expect(sizes[0]).toBeLessThanOrEqual(sizes[1]);
});

test("Studio preview works on mobile without horizontal clipping", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${prefix}/studio`);
  await expect(page.getByRole("button", { name: /clean studio/i })).toBeVisible();
  await expect(page.getByRole("button", { name: "Create film" })).toBeVisible();
  await expect(page.getByRole("switch", { name: /foley sound/i })).toBeChecked();
  const sizes = await page.evaluate(() => [document.documentElement.scrollWidth, innerWidth]);
  expect(sizes[0]).toBeLessThanOrEqual(sizes[1]);
});

test("Studio API denies cross-site render submissions", async ({ request }) => {
  const response = await request.post(`${prefix}/api/studio/jobs`, {
    data: { recording: "brimble", preset: "3d-launch", foley: true },
    headers: { Origin: "https://unauthorized.example" },
  });
  expect(response.status()).toBe(403);
});

test("Landing page AFTER card plays a real 3D Launch MP4", async ({ page }) => {
  await page.goto(prefix || "/");
  const film = page.getByRole("heading", { name: /difference is in the details/i });
  await expect(film).toBeVisible();
  const player = page.getByLabel("AFTER: A demo with Sauce — verified 3D Launch film");
  await expect(player).toBeVisible();
  await expect(player).toHaveAttribute("src", /sauce-motion-phase2\/master-1080p60\.mp4/);
  await expect(page.getByRole("link", { name: /open sauce studio/i })).toHaveAttribute("href", /\/studio$/);
});
