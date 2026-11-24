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
