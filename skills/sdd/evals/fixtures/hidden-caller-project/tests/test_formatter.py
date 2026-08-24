from invoice.formatter import format_amount


def test_format_amount_renders_two_decimals() -> None:
    assert format_amount(123456) == "¥1234.56"
    assert format_amount(50) == "¥0.50"
