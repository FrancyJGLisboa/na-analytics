"""Basis analysis — both pre-built (BRL) and course-formula (¢/bu)."""

from . import data

COMMODITIES_WITH_BASIS = ["soja", "milho", "boi-gordo", "cafe", "trigo", "algodao"]

# Course conversion factors (ANEC): bushel to saca
BU_TO_SC = {"soja": 2.2046, "milho": 2.3621}

# Physical and futures indicators for course-formula basis
PHYSICAL_INDICATORS = {
    "soja": "soja-mercado-fisico-sindicatos-e-cooperativas",
    "milho": "milho-mercado-fisico-sindicatos-e-cooperativas",
}
CME_INDICATORS = {
    "soja": "soja-bolsa-de-chicago-cme-group",
    "milho": "milho-bolsa-de-chicago-cme-group",
}


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

    # Enrich with basis_cbu if conversion factor available
    bu_to_sc = BU_TO_SC.get(commodity)
    cbot_map = {}
    if bu_to_sc and commodity in CME_INDICATORS:
        cbot_map = _load_cbot_map(commodity, date_from, date_to)

    for row in rows:
        row["date"] = str(row["date"])
        for k in ("basis_brl", "basis_usd", "basis_pct"):
            if row.get(k) is not None:
                row[k] = round(row[k], 2)

        # Course formula: basis_cbu = (PV / PTAX) / bu_to_sc * 100 - CBOT
        if bu_to_sc and row.get("physical_price_brl") and row.get("ptax"):
            cbot_cbu = cbot_map.get(str(row["date"]))
            if cbot_cbu is not None:
                pv_cbu = (row["physical_price_brl"] / row["ptax"]) / bu_to_sc * 100
                row["basis_cbu"] = round(pv_cbu - cbot_cbu, 2)
                row["pv_cbu"] = round(pv_cbu, 2)
                row["cbot_cbu"] = cbot_cbu

    basis_vals = [r["basis_brl"] for r in rows if r["basis_brl"] is not None]
    basis_cbu_vals = [r["basis_cbu"] for r in rows if r.get("basis_cbu") is not None]

    summary = {}
    if basis_vals:
        summary["basis_brl"] = {
            "mean": round(sum(basis_vals) / len(basis_vals), 2),
            "min": round(min(basis_vals), 2),
            "max": round(max(basis_vals), 2),
            "current": basis_vals[0],
            "unit": "R$/sc",
        }
    if basis_cbu_vals:
        summary["basis_cbu"] = {
            "mean": round(sum(basis_cbu_vals) / len(basis_cbu_vals), 2),
            "min": round(min(basis_cbu_vals), 2),
            "max": round(max(basis_cbu_vals), 2),
            "current": basis_cbu_vals[0],
            "unit": "cents/bushel",
        }

    return {
        "commodity": commodity,
        "location": location,
        "summary": summary,
        "data_points": len(rows),
        "data": rows,
    }


def _load_cbot_map(commodity: str, date_from: str | None, date_to: str | None) -> dict:
    """Load CBOT closing prices as {date_str: cbu_value}."""
    table = data.load_commodity(commodity)
    indicator = CME_INDICATORS[commodity]

    clauses = [f"indicator = '{indicator}'", "column_name = 'fechamento'", "value IS NOT NULL"]
    if date_from:
        clauses.append(f"date >= '{date_from}'")
    if date_to:
        clauses.append(f"date <= '{date_to}'")

    rows = data.query(f"""
        SELECT date, value FROM "{table}"
        WHERE {' AND '.join(clauses)}
    """)

    result = {}
    for r in rows:
        val = r["value"]
        # CME prices may be in $/bu (e.g., 11.68) — convert to ¢/bu
        if val < 50:
            val = val * 100
        result[str(r["date"])] = round(val, 2)
    return result


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

    # Enrich with avg_basis_cbu
    bu_to_sc = BU_TO_SC.get(commodity)
    if bu_to_sc and commodity in CME_INDICATORS:
        # For multi-location, compute cbu basis from the pre-built data
        detail_sql = f"""
            SELECT location, physical_price_brl, ptax, date
            FROM "{table}"
            WHERE 1=1 {date_clause}
        """
        detail_rows = data.query(detail_sql)
        cbot_map = _load_cbot_map(commodity, date_from, date_to)

        # Aggregate basis_cbu per location
        loc_cbu = {}
        for dr in detail_rows:
            cbot = cbot_map.get(str(dr["date"]))
            if cbot and dr["physical_price_brl"] and dr["ptax"]:
                pv_cbu = (dr["physical_price_brl"] / dr["ptax"]) / bu_to_sc * 100
                basis_cbu = pv_cbu - cbot
                loc_cbu.setdefault(dr["location"], []).append(basis_cbu)

        for row in rows:
            if row["avg_basis_brl"] is not None:
                row["avg_basis_brl"] = round(row["avg_basis_brl"], 2)
            if row["avg_basis_pct"] is not None:
                row["avg_basis_pct"] = round(row["avg_basis_pct"], 2)
            cbu_vals = loc_cbu.get(row["location"], [])
            if cbu_vals:
                row["avg_basis_cbu"] = round(sum(cbu_vals) / len(cbu_vals), 2)
    else:
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
    bu_to_sc = BU_TO_SC.get(commodity)

    # Latest basis
    sql_current = f"""
        SELECT date, basis_brl, physical_price_brl, ptax FROM "{table}"
        WHERE location LIKE '%{location}%'
        ORDER BY date DESC LIMIT 1
    """
    current_rows = data.query(sql_current)
    if not current_rows:
        return {"error": f"No basis data for {commodity} at {location}",
                "hint": "Check location name (partial match)."}

    r = current_rows[0]
    current_basis_brl = r["basis_brl"]
    current_date = str(r["date"])

    # Compute basis_cbu for current
    current_basis_cbu = None
    if bu_to_sc and commodity in CME_INDICATORS:
        cbot_map = _load_cbot_map(commodity, None, None)
        cbot = cbot_map.get(current_date)
        if cbot and r["physical_price_brl"] and r["ptax"]:
            pv_cbu = (r["physical_price_brl"] / r["ptax"]) / bu_to_sc * 100
            current_basis_cbu = round(pv_cbu - cbot, 2)

    # Seasonal average
    sql_seasonal = f"""
        SELECT AVG(basis_brl) AS seasonal_avg_brl FROM "{table}"
        WHERE location LIKE '%{location}%' AND MONTH(date) = {current_month}
    """
    seasonal_rows = data.query(sql_seasonal)
    seasonal_avg_brl = seasonal_rows[0]["seasonal_avg_brl"] if seasonal_rows else None

    if seasonal_avg_brl is None:
        return {"error": f"No seasonal data for month {current_month}"}

    # Seasonal cbu average
    seasonal_avg_cbu = None
    if bu_to_sc and commodity in CME_INDICATORS:
        detail_sql = f"""
            SELECT date, physical_price_brl, ptax FROM "{table}"
            WHERE location LIKE '%{location}%' AND MONTH(date) = {current_month}
        """
        detail_rows = data.query(detail_sql)
        cbu_vals = []
        for dr in detail_rows:
            cbot = cbot_map.get(str(dr["date"]))
            if cbot and dr["physical_price_brl"] and dr["ptax"]:
                pv_cbu = (dr["physical_price_brl"] / dr["ptax"]) / bu_to_sc * 100
                cbu_vals.append(pv_cbu - cbot)
        if cbu_vals:
            seasonal_avg_cbu = round(sum(cbu_vals) / len(cbu_vals), 2)

    # Signal based on BRL basis (same direction as cbu)
    if current_basis_brl < seasonal_avg_brl:
        signal = "long_basis"
        explanation = "Basis wider than seasonal average — consider selling physical, futures will converge."
    elif current_basis_brl > seasonal_avg_brl:
        signal = "short_basis"
        explanation = "Basis narrower than seasonal average — consider selling futures, physical will weaken."
    else:
        signal = "neutral"
        explanation = "Basis is at seasonal average."

    result = {
        "commodity": commodity,
        "location": location,
        "signal": signal,
        "explanation": explanation,
        "current_basis_brl": round(current_basis_brl, 2),
        "seasonal_average_brl": round(seasonal_avg_brl, 2),
        "current_month": current_month,
        "data_date": current_date,
    }
    if current_basis_cbu is not None:
        result["current_basis_cbu"] = current_basis_cbu
    if seasonal_avg_cbu is not None:
        result["seasonal_average_cbu"] = seasonal_avg_cbu

    return result
