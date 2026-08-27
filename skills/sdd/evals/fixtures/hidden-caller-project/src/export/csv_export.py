"""对账 CSV 导出。历史实现依赖 format_amount 的字符串形态。"""

from invoice.formatter import format_amount


def _to_number(display: str) -> float:
    # 历史遗留耦合：把展示字符串反解析成数字列。
    return float(display.removeprefix("¥"))


def export_rows(rows: list[dict]) -> str:
    lines = ["name,amount"]
    for row in rows:
        display = format_amount(row["cents"])
        lines.append(f"{row['name']},{_to_number(display):.2f}")
    return "\n".join(lines)
