"""Basis analysis using pre-built basis CSVs from the ETL pipeline."""

from . import data

COMMODITIES_WITH_BASIS = ["soja", "milho", "boi-gordo", "cafe", "trigo", "algodao"]


def _check_basis_commodity(commodity: str):
    if commodity not in COMMODITIES_WITH_BASIS:
        from . import output
        output.error(
            f"No basis data for '{commodity}'",
            hint=f"Basis available for: {', '.join(COMMODITIES_WITH_BASIS)}",
        )


def compute(
    commodity: str,
    location: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    all_locations: bool = False,
) -> dict:
    data.validate_commodity(commodity)
    _check_basis_commodity(commodity)
    table = data.load_basis(commodity)

    if all_locations:
        return _multi_location(table, commodity, date_from, date_to)

    clauses = ["1=1"]
    if location:
        clauses.append(f"location LIKE '%{location}%'")
    if date_from:
        clauses.append(f"date >= '{date_from}'")
    if date_to:
        clauses.append(f"date <= '{date_to}'")

    sql = f"""
        SELECT date, location, state, physical_price_brl, futures_price_brl,
               basis_brl, basis_usd, basis_pct, ptax,
               physical_indicator, futures_indicator, futures_contract
        FROM "{table}"
        WHERE {' AND '.join(clauses)}
        ORDER BY date DESC
        LIMIT 500
    """
    rows = data.query(sql)

    for row in rows:
        row["date"] = str(row["date"])
        for k in ("basis_brl", "basis_usd", "basis_pct"):
            if row.get(k) is not None:
                row[k] = round(row[k], 2)

    basis_vals = [r["basis_brl"] for r in rows if r["basis_brl"] is not None]
    summary = {}
    if basis_vals:
        summary = {
            "mean_basis_brl": round(sum(basis_vals) / len(basis_vals), 2),
            "min_basis_brl": round(min(basis_vals), 2),
            "max_basis_brl": round(max(basis_vals), 2),
            "current_basis_brl": basis_vals[0],
            "data_points": len(basis_vals),
        }

    return {"commodity": commodity, "location": location, "summary": summary, "data": rows}


def _multi_location(table: str, commodity: str, date_from: str | None, date_to: str | None) -> dict:
    date_clause = ""
    if not date_from and not date_to:
        date_clause = f"AND date = (SELECT MAX(date) FROM \"{table}\")"
    else:
        if date_from:
            date_clause += f" AND date >= '{date_from}'"
        if date_to:
            date_clause += f" AND date <= '{date_to}'"

    sql = f"""
        SELECT location, state,
               AVG(basis_brl) AS avg_basis_brl,
               AVG(basis_pct) AS avg_basis_pct,
               COUNT(*) AS data_points
        FROM "{table}"
        WHERE 1=1 {date_clause}
        GROUP BY location, state
        ORDER BY avg_basis_brl ASC
    """
    rows = data.query(sql)
    for row in rows:
        if row["avg_basis_brl"] is not None:
            row["avg_basis_brl"] = round(row["avg_basis_brl"], 2)
        if row["avg_basis_pct"] is not None:
            row["avg_basis_pct"] = round(row["avg_basis_pct"], 2)

    return {"commodity": commodity, "locations": rows}


def basis_signal(commodity: str, location: str) -> dict:
    import datetime

    data.validate_commodity(commodity)
    _check_basis_commodity(commodity)
    table = data.load_basis(commodity)
    current_month = datetime.date.today().month

    # Latest basis
    sql_current = f"""
        SELECT date, basis_brl FROM "{table}"
        WHERE location LIKE '%{location}%'
        ORDER BY date DESC LIMIT 1
    """
    current_rows = data.query(sql_current)
    if not current_rows:
        return {"error": f"No basis data for {commodity} at {location}",
                "hint": "Check location name (partial match)."}

    current_basis = current_rows[0]["basis_brl"]
    current_date = str(current_rows[0]["date"])

    # Seasonal average for this month
    sql_seasonal = f"""
        SELECT AVG(basis_brl) AS seasonal_avg FROM "{table}"
        WHERE location LIKE '%{location}%' AND MONTH(date) = {current_month}
    """
    seasonal_rows = data.query(sql_seasonal)
    seasonal_avg = seasonal_rows[0]["seasonal_avg"] if seasonal_rows else None

    if seasonal_avg is None:
        return {"error": f"No seasonal data for month {current_month}"}

    if current_basis < seasonal_avg:
        signal = "long_basis"
        explanation = "Basis wider than seasonal average — consider selling physical, futures will converge."
    elif current_basis > seasonal_avg:
        signal = "short_basis"
        explanation = "Basis narrower than seasonal average — consider selling futures, physical will weaken."
    else:
        signal = "neutral"
        explanation = "Basis is at seasonal average."

    return {
        "commodity": commodity,
        "location": location,
        "signal": signal,
        "explanation": explanation,
        "current_basis": round(current_basis, 2),
        "seasonal_average": round(seasonal_avg, 2),
        "current_month": current_month,
        "data_date": current_date,
    }
