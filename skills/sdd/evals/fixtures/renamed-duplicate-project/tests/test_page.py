from docs.page import Page


def test_page_keeps_title() -> None:
    assert Page("Getting Started").title == "Getting Started"
