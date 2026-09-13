# -*- coding: utf-8 -*-
"""Regression tests for Lesson Bank Grade filters (no browser required)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "lesson_bank.html"

FORBIDDEN = (
    "create-from-fork",
    "share.streamlit.io",
    "location.href=",
    "window.top.location",
)


def load_html() -> str:
    assert HTML_PATH.exists(), f"missing {HTML_PATH}"
    return HTML_PATH.read_text(encoding="utf-8")


def extract_cards(html: str) -> list[dict]:
    """Parse card data-grade / data-subj / data-search attributes in order."""
    cards = []
    # Match each card opening tag
    for m in re.finditer(
        r'<div class="card"\s+([^>]*?)onclick="openModal\((\d+)\)">',
        html,
        flags=re.DOTALL,
    ):
        attrs = m.group(1)
        grade = re.search(r'data-grade="([^"]*)"', attrs)
        subj = re.search(r'data-subj="([^"]*)"', attrs)
        search = re.search(r'data-search="([^"]*)"', attrs)
        cards.append(
            {
                "index": int(m.group(2)),
                "grade": grade.group(1) if grade else "",
                "subj": subj.group(1) if subj else "",
                "search": search.group(1) if search else "",
            }
        )
    return cards


def extract_all_json(html: str):
    """Extract and parse const ALL = ... JSON array."""
    marker = "const ALL = "
    i = html.find(marker)
    assert i >= 0, "const ALL = not found"
    i = i + len(marker)
    # JSON starts with [
    assert html[i] == "[", "ALL does not start with ["
    # Walk to matching ]; before next function/let
    depth = 0
    in_str = False
    esc = False
    quote = ""
    j = i
    while j < len(html):
        ch = html[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True
                quote = ch
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    raw = html[i : j + 1]
                    return json.loads(raw)
        j += 1
    raise AssertionError("failed to parse const ALL JSON")


def filter_cards(cards, grades="all", subjects="all", search=""):
    """Pure-Python mirror of lesson_bank.html filterCards() logic."""
    gf = str(grades)
    sf = str(subjects)
    q = (search or "").lower()
    out = []
    for c in cards:
        gm = gf == "all" or str(c["grade"]) == gf
        sm = sf == "all" or str(c["subj"]) == sf
        qm = (not q) or q in (c.get("search") or "").lower()
        if gm and sm and qm:
            out.append(c)
    return out


def test_grade_filter_buttons_have_type_and_data():
    html = load_html()
    for g in ("all", "1", "2", "3", "4", "5"):
        # active class only on "all" by default; match either
        pat = rf'<button type="button" class="filter-btn[^"]*" data-grade="{g}"'
        assert re.search(pat, html), f"missing type=button grade filter for {g}"


def test_no_streamlit_fork_or_nav_strings():
    html = load_html()
    for bad in FORBIDDEN:
        assert bad not in html, f"forbidden string present: {bad}"


def test_filter_grade_5_only():
    cards = extract_cards(load_html())
    assert len(cards) > 0
    g5 = filter_cards(cards, grades="5")
    assert g5, "expected Grade 5 cards"
    assert all(str(c["grade"]) == "5" for c in g5)
    # count matches DOM enumeration
    assert len(g5) == sum(1 for c in cards if str(c["grade"]) == "5")


def test_each_grade_1_to_5_has_cards():
    cards = extract_cards(load_html())
    for g in range(1, 6):
        filtered = filter_cards(cards, grades=str(g))
        assert len(filtered) > 0, f"grade {g} returned 0 cards"


def test_all_json_grades_match_card_order():
    html = load_html()
    cards = extract_cards(html)
    topics = extract_all_json(html)
    assert len(topics) == len(cards), (
        f"ALL len {len(topics)} != cards {len(cards)}"
    )
    for i, (topic, card) in enumerate(zip(topics, cards)):
        assert str(topic.get("grade")) == str(card["grade"]), (
            f"mismatch at {i}: topic grade={topic.get('grade')} "
            f"card data-grade={card['grade']} title={topic.get('title')}"
        )


def main():
    tests = [
        test_grade_filter_buttons_have_type_and_data,
        test_no_streamlit_fork_or_nav_strings,
        test_filter_grade_5_only,
        test_each_grade_1_to_5_has_cards,
        test_all_json_grades_match_card_order,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    if failed:
        print(f"{failed} failed")
        sys.exit(1)
    print(f"OK {len(tests)} passed")
    sys.exit(0)




def test_no_duplicate_openmodal():
    html = (ROOT / "lesson_bank.html").read_text(encoding="utf-8")
    compact = "".join(html.split())
    assert "function openModal(i){function openModal(i){" not in compact
    assert html.count("function openModal(") == 1
    assert "onclick=\"setFilter(" in html or "onclick='setFilter(" in html or 'onclick="setFilter(' in html

if __name__ == "__main__":
    main()
