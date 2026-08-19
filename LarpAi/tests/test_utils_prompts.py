import pytest
from research_agent.app.utils import normalize_whitespace, truncate, slugify, format_confidence, format_currency
from research_agent.app.prompts import PLANNER_SYSTEM_PROMPT, REPORT_FULL_TEMPLATE


def test_utils_normalize_whitespace():
    assert normalize_whitespace("  hello   world  ") == "hello world"
    assert normalize_whitespace("") == ""


def test_utils_truncate():
    text = "hello world this is a long string"
    assert truncate(text, max_chars=10) == "hello w..."
    assert truncate(text, max_chars=100) == text
    assert truncate("short", max_chars=10) == "short"


def test_utils_slugify():
    assert slugify("Hello World") == "hello-world"
    assert slugify("Research AI! v2.0") == "research-ai-v20"


def test_utils_format_confidence():
    assert format_confidence(0.856) == "85.6%"
    assert format_confidence(1.0) == "100.0%"
    assert format_confidence(0.0) == "0.0%"


def test_utils_format_currency():
    assert format_currency(10.50) == "$10.50"
    assert format_currency(0.25, "EUR") == "\u20ac0.25"


def test_prompts_planner_system_prompt():
    assert "ResearchTask" in PLANNER_SYSTEM_PROMPT
    assert "task_ids" in PLANNER_SYSTEM_PROMPT


def test_prompts_report_template():
    assert "{title}" in REPORT_FULL_TEMPLATE
    assert "{query}" in REPORT_FULL_TEMPLATE
    assert "{confidence}" in REPORT_FULL_TEMPLATE
    assert "{findings}" in REPORT_FULL_TEMPLATE
