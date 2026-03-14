"""Futures curve with contango/backwardation detection."""

from . import data


def get_curve(commodity: str, indicator: str, date: str | None = None) -> dict:
    data.validate_commodity(commodity)
    table = data.load_commodity(commodity)

    date_clause = f"date = '{date}'" if date else f"date = (SELECT MAX(date) FROM \"{table}\" WHERE indicator = '{indicator}')"

    sql = f"""
        SELECT date, contract_month, column_name, value, unit
        FROM "{table}"
        WHERE indicator = '{indicator}' AND {date_clause}
          AND column_name IN ('fechamento', 'preco', 'ultimo')
        ORDER BY contract_month ASC
    """
    rows = data.query(sql)

    if not rows:
        return {"error": f"No futures data for {indicator}", "hint": "Check indicator slug."}

    contracts = []
    for row in rows:
        contracts.append({
            "contract_month": row["contract_month"],
            "price": row["value"],
            "unit": row["unit"],
            "date": str(row["date"]),
        })

    curve_shape = "flat"
    prices = [c["price"] for c in contracts if c["price"] is not None]
    if len(prices) >= 2:
        if prices[-1] > prices[0]:
            curve_shape = "contango"
        elif prices[-1] < prices[0]:
            curve_shape = "backwardation"

    return {
        "commodity": commodity,
        "indicator": indicator,
        "curve_shape": curve_shape,
        "contracts": contracts,
    }
