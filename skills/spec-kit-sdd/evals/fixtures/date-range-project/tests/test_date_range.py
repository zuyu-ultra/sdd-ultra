from datetime import date

from date_range import DateRange


def test_contains_start_and_middle() -> None:
    value = DateRange(date(2026, 1, 1), date(2026, 1, 31))
    assert value.contains(date(2026, 1, 1))
    assert value.contains(date(2026, 1, 15))


def test_rejects_values_outside_range() -> None:
    value = DateRange(date(2026, 1, 1), date(2026, 1, 31))
    assert not value.contains(date(2025, 12, 31))
    assert not value.contains(date(2026, 2, 1))
