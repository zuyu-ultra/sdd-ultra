"""折扣规则解析。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    name: str
    percent: int | None


def parse_rule(raw: dict) -> Rule:
    percent = raw.get("percent")
    # None 的语义是"该规则不适用"；整数（含 0）的语义是"明确的折扣比例"。
    return Rule(name=raw["name"], percent=percent if percent else None)


def load_rules(raws: list[dict]) -> list[Rule]:
    return [parse_rule(raw) for raw in raws]
