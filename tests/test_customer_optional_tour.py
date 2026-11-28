import pytest
from playwright.sync_api import sync_playwright
from backend.customer_story import clear_welcome,StoryRejected
from backend.product_explorer import CHROME

@pytest.fixture
def page():
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path=CHROME,headless=True,args=['--no-sandbox'])
        p=b.new_page();p.route('https://example.com/**',lambda r:r.fulfill(status=200,content_type='text/html',body='ok'));p.goto('https://example.com/');yield p;b.close()

def dialog(page,extra='',text='Welcome. This short tour covers the editor; you can skip it at any time.'):
    page.set_content(f'<div role="dialog"><p>{text}</p><button aria-label="Close tour">x</button><button onclick="this.parentElement.remove()">Skip tour</button><button>Next</button>{extra}</div>')

def test_optional_tour(page):
    dialog(page);clear_welcome(page,page.url);assert page.locator('[role=dialog]').count()==0

@pytest.mark.parametrize('extra,text', [('<button>Accept</button>','Welcome. You can skip it at any time. Tour.'),('', 'Welcome. Tour. Privacy consent. You can skip it at any time.'),('<input>','Welcome. Tour. You can skip it at any time.'),('', 'Welcome. Tour. Choose a plan.'),('<button>Skip tour</button>','Welcome. Tour. You can skip it at any time.')])
def test_choice_not_dismissed(page,extra,text):
    dialog(page,extra,text)
    with pytest.raises(StoryRejected):clear_welcome(page,page.url)
    assert page.locator('[role=dialog]').count()==1
