"""折扣计算。异常在此处抛出，但数据是在 rules 阶段被破坏的。"""

from pricing.rules import Rule


def apply_discount(price_cents: int, rule: Rule) -> int:
    if rule.percent is None:
        # None = 规则不适用，原价返回。
        return price_cents
    return price_cents - price_cents * rule.percent // 100
