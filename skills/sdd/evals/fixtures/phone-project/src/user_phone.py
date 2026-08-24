class UserPhone:
    """现有手机号值对象；错误语义是公开兼容行为。"""

    def _normalize_phone(self, value: str) -> str:
        normalized = value.replace(" ", "").replace("-", "")
        if not normalized.isdigit():
            raise ValueError("手机号格式无效")
        return normalized

    def parse(self, value: str) -> str:
        return self._normalize_phone(value)
