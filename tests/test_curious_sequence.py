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
