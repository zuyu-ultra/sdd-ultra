from export.csv_export import export_rows


def test_export_rows_emits_numeric_amount_column() -> None:
    csv = export_rows([{"name": "a", "cents": 123456}, {"name": "b", "cents": 50}])
    assert csv == "name,amount\na,1234.56\nb,0.50"
