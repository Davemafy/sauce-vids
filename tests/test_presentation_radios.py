from playwright.sync_api import sync_playwright
from backend.product_explorer import CHROME
from backend.presentation_radios import catalog,handle,applied,result_region

def test_named_public_presentation_radio_controls_only():
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
        try:
            page=browser.new_page(viewport={"width":1920,"height":1080})
            page.set_content("""<main>Product preview</main>
            <aside style="position:fixed;left:1544px;top:64px;width:360px;height:800px;background:white">
            <style>label {display:block;width:150px;height:35px}</style>
            <p id="a">Appearance</p><div role="group" aria-labelledby="a">
            <label><input type="radio" name="appearance" value="light" checked>Light</label>
            <label><input type="radio" name="appearance" value="dark">Dark</label></div>
            <p id="r">Radius</p><div role="group" aria-labelledby="r">
            <label><input type="radio" name="radius" value="small" checked>Small</label>
            <label><input type="radio" name="radius" value="large">Large</label></div>
            <form><div role="group" aria-labelledby="r"><label><input type="radio" name="other" value="full">Full</label></div></form>
            <div role="group" aria-labelledby="r" data-sensitive><label><input type="radio" name="sensitive" value="none">None</label></div>
            <p id="p">Payment</p><div role="group" aria-labelledby="p"><label><input type="radio" name="payment" value="card">Card</label></div>
            </aside>""")
            rows=catalog(page)
            assert {(r["group"],r["label"]) for r in rows}=={("Appearance","dark"),("Radius","large")}
            assert result_region(page)=={"x":0,"y":64,"width":1536,"height":1016}
            a=next(r for r in rows if r["label"]=="dark")
            loc=handle(page,a)
            assert loc is not None
            loc.click()
            assert applied(page,a)
            assert handle(page,a) is None
            assert handle(page,{"group":"Payment","label":"card"}) is None
            page.evaluate("""()=>{const r=document.createElement('div');r.style='position:fixed;inset:0;z-index:10000;background:black';document.body.append(r)}""")
            assert not catalog(page)
            assert result_region(page) is None
        finally:browser.close()
