"""对账报表。与 discount 独立地消费同一份规则数据。"""

from pricing.rules import Rule


def describe_rule(rule: Rule) -> str:
    if rule.percent is None:
        return f"{rule.name}：不适用"
    return f"{rule.name}：折扣 {rule.percent}%"
