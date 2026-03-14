"""FX-adjusted pricing via PTAX."""

from . import data


def get_fx_adjusted(
    commodity: str,
    indicator: str,
    target_currency: str = "USD",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    data.validate_commodity(commodity)
    table = data.load_commodity(commodity)

    # Load FX data (PTAX from mercado-financeiro)
    fx_table = data.load_commodity("mercado-financeiro")

    date_clauses = []
    if date_from:
        date_clauses.append(f"p.date >= '{date_from}'")
    if date_to:
        date_clauses.append(f"p.date <= '{date_to}'")
    extra = (" AND " + " AND ".join(date_clauses)) if date_clauses else ""

    sql = f"""
        WITH prices AS (
            SELECT date, value AS original_price, currency AS original_currency
            FROM "{table}"
            WHERE indicator = '{indicator}' AND measure = 'price'
              AND column_name IN ('preco', 'fechamento', 'valor')
        ),
        ptax AS (
            SELECT date, value AS ptax_rate
            FROM "{fx_table}"
            WHERE indicator LIKE '%dolar%' AND measure = 'price'
              AND column_name IN ('preco', 'fechamento', 'valor', 'venda')
        )
        SELECT p.date, p.original_price, p.original_currency,
               fx.ptax_rate,
               CASE
                 WHEN p.original_currency = 'BRL' AND '{target_currency}' = 'USD'
                   THEN p.original_price / fx.ptax_rate
                 WHEN p.original_currency = 'USD' AND '{target_currency}' = 'BRL'
                   THEN p.original_price * fx.ptax_rate
                 ELSE p.original_price
               END AS converted_price,
               '{target_currency}' AS target_currency
        FROM prices p
        LEFT JOIN ptax fx ON p.date = fx.date
        WHERE fx.ptax_rate IS NOT NULL {extra}
        ORDER BY p.date DESC
        LIMIT 500
    """
    rows = data.query(sql)

    for row in rows:
        row["date"] = str(row["date"])
        if row["converted_price"] is not None:
            row["converted_price"] = round(row["converted_price"], 4)

    return {
        "commodity": commodity,
        "indicator": indicator,
        "target_currency": target_currency,
        "data": rows,
    }
