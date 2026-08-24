import pytest

from user_phone import UserPhone


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("138 0013 8000", "13800138000"), ("138-0013-8000", "13800138000")],
)
def test_parse_normalizes_existing_formats(raw: str, expected: str) -> None:
    assert UserPhone().parse(raw) == expected


def test_parse_keeps_chinese_error_contract() -> None:
    with pytest.raises(ValueError, match="手机号格式无效"):
        UserPhone().parse("not-a-phone")
