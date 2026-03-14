"""Multi-year seasonal averages vs current year."""

from . import data


def get_seasonal(
    commodity: str,
    indicator: str,
    location: str | None = None,
    measure: str = "price",
) -> dict:
    data.validate_commodity(commodity)
    table = data.load_commodity(commodity)

    loc_clause = f"AND location LIKE '%{location}%'" if location else ""

    sql = f"""
        SELECT MONTH(date) AS month,
               AVG(value) AS avg_value,
               STDDEV(value) AS std_value,
               COUNT(*) AS data_points
        FROM "{table}"
        WHERE indicator = '{indicator}' AND measure = '{measure}'
          AND column_name IN ('preco', 'fechamento', 'valor')
          {loc_clause}
        GROUP BY MONTH(date)
        ORDER BY month
    """
    avg_rows = data.query(sql)

    # Current year
    import datetime
    year = datetime.date.today().year
    sql_current = f"""
        SELECT MONTH(date) AS month, AVG(value) AS current_value
        FROM "{table}"
        WHERE indicator = '{indicator}' AND measure = '{measure}'
          AND YEAR(date) = {year}
          AND column_name IN ('preco', 'fechamento', 'valor')
          {loc_clause}
        GROUP BY MONTH(date)
        ORDER BY month
    """
    current_rows = data.query(sql_current)
    current_map = {r["month"]: r["current_value"] for r in current_rows}

    months = []
    for row in avg_rows:
        m = row["month"]
        months.append({
            "month": m,
            "average_value": round(row["avg_value"], 2) if row["avg_value"] else None,
            "std": round(row["std_value"], 2) if row["std_value"] else None,
            "current_year_value": round(current_map[m], 2) if m in current_map and current_map[m] else None,
            "data_points": row["data_points"],
        })

    return {
        "commodity": commodity,
        "indicator": indicator,
        "location": location,
        "current_year": year,
        "months": months,
    }
