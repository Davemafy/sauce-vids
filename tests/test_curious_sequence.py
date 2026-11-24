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
