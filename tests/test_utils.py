from app.agent.state import new_turn_input
from app.utils import text_of, truncate


def test_text_of_handles_str_and_blocks():
    assert text_of("hi") == "hi"
    assert text_of([{"type": "text", "text": "a"}, {"type": "tool_use"}, "b"]) == "ab"


def test_truncate():
    assert truncate("abcdef", 4) == "abc…"
    assert truncate("abc", 4) == "abc"


def test_new_turn_input_resets_working_state():
    s = new_turn_input("hello")
    assert s["plan"] == [] and s["revision_count"] == 0 and s["messages"][0].content == "hello"
