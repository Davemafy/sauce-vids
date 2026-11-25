from unittest.mock import Mock
from backend.curious_sequence import choose,exact,safe_label,dismiss_picker
import pytest

def test_model_cannot_invent_labels_or_selectors():
    rows=[{'label':'Observed appearance','locator':'loc'}]
    assert choose('{"id":"c0"}',rows)=='Observed appearance'
    for response in ('{"id":"c1"}','{"id":"#arbitrary"}','{"id":null}','[]'):
        assert choose(response,rows) is None
    with pytest.raises(ValueError):exact(rows,'invented')
    with pytest.raises(ValueError):exact(rows+rows,'Observed appearance')

def test_exclude_sensitive_controls():
    for label in ('Delete','Submit','Payment settings','API key','Connect account','Log in',''):
        assert not safe_label(label)
    assert safe_label('Cyberpunk')

def test_open_picker_is_dismissed_only_if_needed():
    p=Mock();s=Mock();s.is_visible.return_value=True
    dismiss_picker(p,s)
    p.keyboard.press.assert_called_once_with('Escape')
    s.wait_for.assert_called_once_with(state='hidden',timeout=3500)
    p.reset_mock();s.is_visible.return_value=False
    dismiss_picker(p,s)
    p.keyboard.press.assert_not_called()

def test_largest_independently_changed_panel_is_framed(monkeypatch):
    from backend.curious_sequence import choose_result_panel,sequence_viewport
    sidebar={'result_area_fraction':.24,'changed_result_fraction':.79}
    product={'result_area_fraction':.57,'changed_result_fraction':.16}
    unchanged={'result_area_fraction':.8,'changed_result_fraction':.01}
    assert choose_result_panel([sidebar,product,unchanged])==product
    assert choose_result_panel([unchanged])=={}
    monkeypatch.setenv('SAUCE_CAPTURE_QUALITY','high')
    assert sequence_viewport()==({'width':1920,'height':1080},2)

def test_option_search_bounded_and_observed_only():
    from backend.curious_sequence import option_hypotheses
    rows=[{'label':str(i)} for i in range(6)]
    assert option_hypotheses('{"ids":["fake","c2","c2","c1","c0","c4",null]}',rows)==['2','1','0']
    assert option_hypotheses('{"ids":"c0"}',rows)==[]

def test_option_comparison_cannot_select_failed_probe(tmp_path,monkeypatch):
    import backend.curious_sequence as s
    def probe(url,picker,option,path,existing=None):
        if option=='bad':raise ValueError('no payoff')
        return {'result_area_fraction':.5}
    monkeypatch.setattr(s,'option_probe',probe)
    monkeypatch.setattr(s,'_media',lambda *a:{})
    conv=Mock();conv.ask.return_value='{"id":"p0","reason":"invented"}'
    receipt={}
    assert s.compare_options('https://example.com','picker',['bad','good'],tmp_path,conv,receipt) is None
    assert receipt['option_probes'][0]['status']=='rejected'
    conv.ask.return_value='{"id":"p1","reason":"real"}'
    assert s.compare_options('https://example.com','picker',['bad','good'],tmp_path,conv,{})==('good',{'result_area_fraction':.5})

def test_comparative_capture_requires_same_substantial_payoff():
    from backend.curious_sequence import require_replay_payoff
    expected={'changed_result_fraction':.9492,'change_above_baseline':.6098}
    require_replay_payoff({'changed_result_fraction':.85,'change_above_baseline':.55},expected)
    with pytest.raises(ValueError,match='does not reproduce'):
        require_replay_payoff({'changed_result_fraction':.1329,'change_above_baseline':.0778},expected)

def test_applied_label_requires_real_option(monkeypatch):
    import backend.curious_sequence as s
    monkeypatch.setattr(s,'discover',lambda p:[{'label':'Claymorphism'}])
    s.assert_applied_option(None,'Claymorphism')
    with pytest.raises(ValueError,match='does not match'):
        s.assert_applied_option(None,'Bubblegum')

@pytest.mark.parametrize("comparative",[False,True])
def test_both_sequence_paths_receive_one_council_challenge(tmp_path,monkeypatch,comparative):
    from contextlib import contextmanager
    import backend.curious_sequence as s
    page=Mock()
    @contextmanager
    def browser(url):yield page
    picker=[{'label':'Appearance','locator':Mock()}]
    options=[{'label':'A','locator':Mock()},{'label':'B','locator':Mock()}]
    conv=Mock();conv.calls=0
    conv.ask.side_effect=['{"id":"c0"}','{"ids":[]}' if comparative else '{"id":null}']
    council=Mock(return_value='\nTEXT-ONLY challenge fixture')
    monkeypatch.setattr(s,'Conversation',lambda path:conv)
    monkeypatch.setattr(s,'browser',browser)
    monkeypatch.setattr(s,'discover',lambda p,scope=None:picker if scope is None else options)
    monkeypatch.setattr(s,'open_picker',lambda *a:Mock())
    monkeypatch.setattr(s,'shot',lambda p:b'fixture')
    monkeypatch.setattr(s,'panels',lambda p:[])
    monkeypatch.setattr(s,'_media',lambda *a:{})
    monkeypatch.setattr(s,'advise',council)
    compare=Mock(return_value=None)
    monkeypatch.setattr(s,'compare_options',compare)
    monkeypatch.setenv('SAUCE_CURIOUS_OPTION_SEARCH','1' if comparative else '0')
    result,_=s.investigate_sequence('https://example.com',{'title':'Demo'},tmp_path)
    assert result is None
    council.assert_called_once_with([{'id':'c0','label':'A'},{'id':'c1','label':'B'}],tmp_path,phase='picker')
    assert 'TEXT-ONLY challenge fixture' in conv.ask.call_args.args[0]
    assert conv.ask.call_count==2
    assert compare.call_count==int(comparative)

def test_option_search_accepts_observed_gemini_array():
    from backend.curious_sequence import option_hypotheses
    items=[{'label':str(i)} for i in range(24)]
    raw='[{"id":"c19","reason":"baseline"},{"id":"c22","reason":"structure"},{"id":"c8","reason":"texture"}]'
    assert option_hypotheses(raw,items)==['19','22','8']
    assert option_hypotheses('[{"id":"fake"},{"id":"c2"},{"id":"c2"},{"id":"c3"},{"id":"c4"},{"id":"c5"}]',items)==['2','3','4']
    assert option_hypotheses('[{"id":"c1"},"c2"]',items)==[]
    assert option_hypotheses('prose c1',items)==[]

def test_analytic_date_range_is_opt_in_and_bounded(monkeypatch):
    from backend.curious_sequence import analytic_name,analytic_option
    monkeypatch.delenv('SAUCE_CURIOUS_ANALYTICS',raising=False)
    assert not analytic_name('Date range')
    monkeypatch.setenv('SAUCE_CURIOUS_ANALYTICS','1')
    assert analytic_name('Date range')
    assert not analytic_name('Account') and not analytic_name('Chart interval')
    for label in ('Today','Yesterday','Last 7 days','Last 24 hours'):
        assert analytic_option('Date range',label)
    for label in ('Custom range','Submit','Last 0 days','Last 9999 days','Last 7 days and export'):
        assert not analytic_option('Date range',label)

def test_analytic_preset_requires_applied_visible_label(monkeypatch):
    import backend.curious_sequence as s
    monkeypatch.setenv('SAUCE_CURIOUS_ANALYTICS','1')
    loc=Mock();loc.inner_text.return_value='Last 7 days'
    monkeypatch.setattr(s,'analytic_triggers',lambda p:[{'label':'Date range','locator':loc}])
    s.assert_applied_option(None,'Last 7 days','Date range')
    with pytest.raises(ValueError,match='does not match'):
        s.assert_applied_option(None,'Last 24 hours','Date range')

def test_option_hypotheses_normalizes_only_unique_observed_names():
    from backend.curious_sequence import option_hypotheses
    rows=[{'label':'Today'},{'label':'Last 24 hours'},{'label':'Last 7 days'}]
    raw='{"ids":["Last 30 days","Last 24 hours","Today"]}'
    assert option_hypotheses(raw,rows)==['Last 24 hours','Today']
    assert option_hypotheses('{"ids":["Today","c0","today","Last 7 days"]}',rows)==['Today','Last 7 days']
    assert option_hypotheses('{"ids":["Today"]}',rows+[{'label':'Today'}])==[]

@pytest.mark.parametrize("obstructed",[False,True])
def test_native_sequence_click_checks_real_target_before_dispatch(monkeypatch,obstructed):
    import time
    import backend.curious_sequence as s
    page=Mock()
    loc=Mock()
    loc.bounding_box.return_value={'x':10,'y':20,'width':40,'height':30}
    loc.evaluate.return_value=None if obstructed else {'x':30,'y':35}
    scope=Mock()
    def open_picker(p,u,label,click):
        click(loc)
        return scope
    monkeypatch.setattr(s,'open_picker',open_picker)
    monkeypatch.setattr(s,'option_items',lambda *args:[{'label':'Preview','locator':loc}])
    monkeypatch.setattr(s,'dismiss_picker',Mock())
    monkeypatch.setattr(s,'observed_result',lambda *a,**kw:(b'after',{'result_rect':{'x':0,'y':0,'width':200,'height':100}},2.0))
    args=(page,'https://example.com/demo',{'picker':'Appearance','option':'Preview'},time.monotonic(),Mock())
    kwargs={'baseline':(b'before',b'steady',[]),'compact':True,'snapshot':Mock()}
    if obstructed:
        with pytest.raises(ValueError,match='obstructed'):
            s.capture_sequence(*args,**kwargs)
        page.mouse.down.assert_not_called()
    else:
        events,_=s.capture_sequence(*args,**kwargs)
        assert page.mouse.down.call_count==2
        assert page.mouse.up.call_count==2
        assert events[0]['t']>=0
    loc.click.assert_not_called()
