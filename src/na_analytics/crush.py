"""Soy crush margin: (farelo + oleo) - soja."""

from . import data

SOJA_INDICATORS = {
    "soja": "soja-bolsa-de-chicago-cme-group",
    "farelo": "farelo-de-soja-chicago-cbot",
    "oleo": "oleo-de-soja-chicago-cbot",
}


def compute(
    date_from: str | None = None,
    date_to: str | None = None,
    contract: str | None = None,
) -> dict:
    table = data.load_commodity("soja")

    date_clauses = []
    if date_from:
        date_clauses.append(f"date >= '{date_from}'")
    if date_to:
        date_clauses.append(f"date <= '{date_to}'")
    if contract:
        date_clauses.append(f"contract_month LIKE '%{contract}%'")

    extra = (" AND " + " AND ".join(date_clauses)) if date_clauses else ""

    sql = f"""
        WITH s AS (
            SELECT date, value AS soja_price FROM "{table}"
            WHERE indicator = '{SOJA_INDICATORS["soja"]}' AND column_name IN ('fechamento','preco') {extra}
        ),
        f AS (
            SELECT date, value AS farelo_price FROM "{table}"
            WHERE indicator = '{SOJA_INDICATORS["farelo"]}' AND column_name IN ('fechamento','preco') {extra}
        ),
        o AS (
            SELECT date, value AS oleo_price FROM "{table}"
            WHERE indicator = '{SOJA_INDICATORS["oleo"]}' AND column_name IN ('fechamento','preco') {extra}
        )
        SELECT s.date, s.soja_price, f.farelo_price, o.oleo_price,
               (f.farelo_price + o.oleo_price - s.soja_price) AS crush_margin
        FROM s
        LEFT JOIN f ON s.date = f.date
        LEFT JOIN o ON s.date = o.date
        ORDER BY s.date DESC
        LIMIT 500
    """
    rows = data.query(sql)

    for row in rows:
        row["date"] = str(row["date"])
        if row["crush_margin"] is not None:
            row["crush_margin"] = round(row["crush_margin"], 4)

    return {"commodity": "soja", "data": rows}
