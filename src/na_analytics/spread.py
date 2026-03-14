"""Regional price spread statistics."""

from . import data


def get_regional_spread(
    commodity: str,
    indicator: str,
    date: str | None = None,
) -> dict:
    data.validate_commodity(commodity)
    table = data.load_commodity(commodity)

    date_clause = f"date = '{date}'" if date else f"date = (SELECT MAX(date) FROM \"{table}\" WHERE indicator = '{indicator}')"

    sql = f"""
        SELECT location, state, value AS price
        FROM "{table}"
        WHERE indicator = '{indicator}' AND {date_clause}
          AND measure = 'price' AND column_name IN ('preco', 'fechamento', 'valor')
          AND value IS NOT NULL
        ORDER BY value ASC
    """
    rows = data.query(sql)

    if not rows:
        return {"error": f"No data for {indicator}", "hint": "Check indicator slug and date."}

    prices = [r["price"] for r in rows]
    n = len(prices)
    mean = sum(prices) / n
    variance = sum((p - mean) ** 2 for p in prices) / n
    std = variance ** 0.5
    sorted_p = sorted(prices)

    summary = {
        "mean": round(mean, 2),
        "std": round(std, 2),
        "min": sorted_p[0],
        "max": sorted_p[-1],
        "iqr_25": sorted_p[n // 4] if n >= 4 else sorted_p[0],
        "iqr_75": sorted_p[3 * n // 4] if n >= 4 else sorted_p[-1],
        "count": n,
    }

    # By state
    by_state = {}
    for r in rows:
        st = r["state"] or "unknown"
        by_state.setdefault(st, []).append(r["price"])
    state_summary = [
        {"state": st, "mean": round(sum(v) / len(v), 2), "count": len(v)}
        for st, v in sorted(by_state.items())
    ]

    extremes = {
        "highest": {"location": rows[-1]["location"], "price": rows[-1]["price"]},
        "lowest": {"location": rows[0]["location"], "price": rows[0]["price"]},
    }

    return {
        "commodity": commodity,
        "indicator": indicator,
        "summary": summary,
        "by_state": state_summary,
        "extremes": extremes,
        "locations": rows,
    }
