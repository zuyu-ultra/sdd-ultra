from pricing.discount import apply_discount
from pricing.report import describe_rule
from pricing.rules import Rule, load_rules, parse_rule


def test_parse_rule_reads_percent() -> None:
    assert parse_rule({"name": "vip", "percent": 20}) == Rule("vip", 20)


def test_parse_rule_marks_missing_percent_as_not_applicable() -> None:
    assert parse_rule({"name": "none"}) == Rule("none", None)


def test_apply_discount_reduces_price() -> None:
    assert apply_discount(10000, Rule("vip", 20)) == 8000


def test_apply_discount_passes_through_when_not_applicable() -> None:
    assert apply_discount(10000, Rule("none", None)) == 10000


def test_describe_rule_renders_percent() -> None:
    assert describe_rule(Rule("vip", 20)) == "vip：折扣 20%"


def test_load_rules_maps_all_entries() -> None:
    rules = load_rules([{"name": "vip", "percent": 20}, {"name": "none"}])
    assert [r.name for r in rules] == ["vip", "none"]
