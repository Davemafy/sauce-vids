import {test,expect} from "@playwright/test";
const prefix=process.env.NEXT_PUBLIC_SAUCE_BASE_PATH||"";
const id="e5a0b1c2d3e4f5a6b7c8d9e0";
const job={id,url:"https://paldey.com/",stage:"rendering",status:"queued",
 created_at:Date.now()/1000-8,frames_rendered:150,frames_total:480};
const auth=(page:any,allow=true)=>page.route("**/api/studio/url/auth",(route:any)=>route.fulfill({
 status:200,contentType:"application/json",body:JSON.stringify({authorized:allow,configured:true}),
}));
const submit=(page:any)=>page.route("**/api/studio/url/jobs",(route:any)=>route.fulfill({
 status:202,contentType:"application/json",body:JSON.stringify({jobId:id}),
}));

test("URL is primary and access code blocks public rendering",async({page})=>{
 await auth(page,false);
 await page.goto(prefix+"/studio");
 await expect(page.getByRole("heading",{name:/product deserves/i})).toBeVisible();
 await expect(page.getByRole("button",{name:/make film/i})).toBeDisabled();
 await expect(page.getByLabel("Private pilot access code")).toBeVisible();
 await expect(page.getByRole("link",{name:"Sample recordings"})).toBeVisible();
});

test("Frame counts are factual, and auth-gated products are not faked",async({page})=>{
 await auth(page);await submit(page);
 let needsAccess=false;
 await page.route("**/api/studio/url/jobs/"+id,route=>route.fulfill({
  status:200,contentType:"application/json",
  body:JSON.stringify({job:needsAccess?
   {...job,status:"needs_access",stage:"needs_access",reason:"Real product requires authentication."}:job}),
 }));
 await page.goto(prefix+"/studio");
 await page.getByLabel("Product website").fill("https://paldey.com/");
 await page.getByRole("button",{name:/make film/i}).click();
 const monitor=page.getByRole("region",{name:"Live URL film production status"});
 await expect(monitor.getByRole("progressbar",{name:"Verified frames rendered"})).toHaveAttribute("aria-valuenow","150",{timeout:6500});
 await expect(monitor.getByText("150 / 480 frames")).toBeVisible();
 needsAccess=true;
 await expect(page.getByRole("heading",{name:"This product needs more than a link."})).toBeVisible({timeout:6500});
 await expect(page.getByText(/requires authentication/i)).toBeVisible();
 await expect(page.locator("video")).toHaveCount(0);
});

test("Refresh reconnects to job, then review can be saved",async({page})=>{
 await auth(page);await submit(page);
 let ready=false;
 await page.route("**/api/studio/url/jobs/"+id,route=>route.fulfill({
  status:200,contentType:"application/json",
  body:JSON.stringify({job:ready?{...job,status:"needs_review",stage:"needs_review"}:job}),
 }));
 await page.route("**/api/studio/url/jobs/"+id+"/feedback",route=>route.fulfill({
  status:200,contentType:"application/json",body:JSON.stringify({saved:true}),
 }));
 await page.route("**/api/studio/url/jobs/"+id+"/media",route=>route.fulfill({
  status:404,contentType:"application/json",body:"{}",
 }));
 await page.goto(prefix+"/studio");
 await page.getByLabel("Product website").fill("https://paldey.com/");
 await page.getByRole("button",{name:/make film/i}).click();
 await expect(page.getByRole("region",{name:"Live URL film production status"})).toBeVisible();
 await page.reload();
 await expect(page.getByRole("region",{name:"Live URL film production status"})).toBeVisible();
 ready=true;
 await expect(page.getByRole("heading",{name:"Your first cut is ready."})).toBeVisible({timeout:6500});
 await expect(page.getByLabel("AI-directed Sauce video preview")).toBeVisible();
 await expect(page.getByRole("link",{name:/Download MP4/})).toHaveAttribute("download",/sauce-/);
 await expect(page.getByRole("link",{name:/Open review link/})).toHaveAttribute("href",new RegExp("job="+id));
 await page.getByRole("button",{name:"Rate 4 out of 5"}).click();
 await page.getByRole("button",{name:"Save review"}).click();
 await expect(page.getByRole("button",{name:/Review saved/})).toBeVisible();
});

test("URL film production fits mobile viewport",async({page})=>{
 await auth(page);await submit(page);
 await page.route("**/api/studio/url/jobs/"+id,route=>route.fulfill({
  status:200,contentType:"application/json",body:JSON.stringify({job}),
 }));
 await page.setViewportSize({width:390,height:844});
 await page.goto(prefix+"/studio");
 await page.getByLabel("Product website").fill("https://paldey.com/");
 await page.getByRole("button",{name:/make film/i}).click();
 await expect(page.getByRole("region",{name:"Live URL film production status"})).toBeVisible();
 const sizes=await page.evaluate(()=>[document.documentElement.scrollWidth,window.innerWidth]);
 expect(sizes[0]).toBeLessThanOrEqual(sizes[1]);
});


test("Shared job does not impersonate progress before pilot authorization",async({page})=>{
 await page.route("**/api/studio/url/auth",route=>route.fulfill({
  status:200,contentType:"application/json",body:JSON.stringify({authorized:false,configured:true}),
 }));
 await page.goto(prefix+"/studio?job="+id);
 await expect(page.getByLabel("Private pilot access code")).toBeVisible();
 await expect(page.getByRole("region",{name:"Live URL film production status"})).toHaveCount(0);
});
