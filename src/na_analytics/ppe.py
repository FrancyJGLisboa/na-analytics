"""Export Parity Price (PPE) with auto-resolve from pipeline data."""

CONVERSION = {
    "soja": {"bu_to_ton": 36.7454, "bu_to_sc": 2.2046, "sc_to_ton": 0.06},
    "milho": {"bu_to_ton": 39.3678, "bu_to_sc": 2.3621, "sc_to_ton": 0.06},
}

CME_INDICATORS = {
    "soja": "soja-bolsa-de-chicago-cme-group",
    "milho": "milho-bolsa-de-chicago-cme-group",
}

DEFAULT_FOBBINGS = 8.0


def resolve_from_pipeline(commodity: str) -> dict:
    """Fetch latest CBOT, FX, and basis from live pipeline data.
    Returns dict with resolved values and source dates."""
    from . import data

    resolved = {}

    # Resolve CBOT from CME futures
    key = commodity.lower()
    cme_ind = CME_INDICATORS.get(key)
    if cme_ind:
        table = data.load_commodity(key)
        rows = data.query(f"""
            SELECT date, value FROM "{table}"
            WHERE indicator = '{cme_ind}' AND column_name = 'fechamento'
              AND value IS NOT NULL
            ORDER BY date DESC LIMIT 1
        """)
        if rows:
            # CME prices are in USD/bu — convert to cents/bu
            price = rows[0]["value"]
            # If price < 50, it's likely in $/bu (e.g., 11.46) → multiply by 100
            if price < 50:
                price = price * 100
            resolved["cbot"] = round(price, 2)
            resolved["cbot_source_date"] = str(rows[0]["date"])
            resolved["cbot_indicator"] = cme_ind

    # Resolve FX (PTAX) from mercado-financeiro
    fx_table = data.load_commodity("mercado-financeiro")
    fx_rows = data.query(f"""
        SELECT date, value FROM "{fx_table}"
        WHERE indicator LIKE '%dolar%' AND measure = 'price'
          AND column_name IN ('preco', 'fechamento', 'valor', 'venda')
          AND value IS NOT NULL
        ORDER BY date DESC LIMIT 1
    """)
    if fx_rows:
        fx_val = fx_rows[0]["value"]
        # B3 dólar futures are in points (5353.5 = R$5.3535)
        if fx_val > 100:
            fx_val = fx_val / 1000
        resolved["fx"] = round(fx_val, 4)
        resolved["fx_source_date"] = str(fx_rows[0]["date"])

    # Resolve basis from pre-built basis CSV
    try:
        basis_table = data.load_basis(key)
        basis_rows = data.query(f"""
            SELECT date, AVG(basis_brl) AS avg_basis
            FROM "{basis_table}"
            WHERE date = (SELECT MAX(date) FROM "{basis_table}")
            GROUP BY date
        """)
        if basis_rows and basis_rows[0]["avg_basis"] is not None:
            resolved["basis_fob"] = round(basis_rows[0]["avg_basis"], 2)
            resolved["basis_source_date"] = str(basis_rows[0]["date"])
    except SystemExit:
        pass  # No basis CSV for this commodity — not fatal

    return resolved


def compute(
    commodity: str,
    cbot: float | None = None,
    basis_fob: float | None = None,
    fx: float | None = None,
    logistics_usd_ton: float = 0.0,
    fobbings: float = DEFAULT_FOBBINGS,
    auto_resolve: bool = False,
) -> dict:
    key = commodity.lower()
    if key not in CONVERSION:
        return {"error": f"PPE not supported for '{commodity}'. Use 'soja' or 'milho'."}

    resolved = {}
    if auto_resolve and (cbot is None or basis_fob is None or fx is None):
        resolved = resolve_from_pipeline(key)

    # Apply resolved values where user didn't supply
    if cbot is None:
        cbot = resolved.get("cbot")
    if basis_fob is None:
        basis_fob = resolved.get("basis_fob")
    if fx is None:
        fx = resolved.get("fx")

    # Check what's still missing
    missing = []
    if cbot is None:
        missing.append("cbot")
    if basis_fob is None:
        missing.append("basis-fob")
    if fx is None:
        missing.append("fx")
    if missing:
        return {
            "error": f"Could not resolve: {', '.join(missing)}",
            "hint": f"Provide --{' --'.join(missing)} explicitly, or ensure pipeline data is available.",
        }

    conv = CONVERSION[key]

    flat_price_cbu = cbot + basis_fob
    fob_usd_ton = flat_price_cbu / 100 * conv["bu_to_ton"]
    fca_usd_ton = fob_usd_ton - fobbings
    exw_usd_ton = fob_usd_ton - logistics_usd_ton

    exw_usd_sc = exw_usd_ton * conv["sc_to_ton"]
    exw_brl_sc = exw_usd_sc * fx
    fca_usd_sc = fca_usd_ton * conv["sc_to_ton"]
    fca_brl_sc = fca_usd_sc * fx
    fob_usd_sc = fob_usd_ton * conv["sc_to_ton"]
    fob_brl_sc = fob_usd_sc * fx

    result = {
        "commodity": key,
        "inputs": {
            "cbot_cbu": cbot,
            "basis_fob_cbu": basis_fob,
            "fx_brl_usd": fx,
            "logistics_usd_ton": logistics_usd_ton,
            "fobbings_usd_ton": fobbings,
        },
        "conversion_factors": conv,
        "results": {
            "flat_price_cbu": round(flat_price_cbu, 2),
            "fob_usd_ton": round(fob_usd_ton, 4),
            "fca_usd_ton": round(fca_usd_ton, 4),
            "exw_usd_ton": round(exw_usd_ton, 4),
            "fob_usd_sc": round(fob_usd_sc, 4),
            "fob_brl_sc": round(fob_brl_sc, 2),
            "fca_usd_sc": round(fca_usd_sc, 4),
            "fca_brl_sc": round(fca_brl_sc, 2),
            "exw_usd_sc": round(exw_usd_sc, 4),
            "exw_brl_sc": round(exw_brl_sc, 2),
        },
        "units": {
            "cbu": "cents/bushel",
            "usd_ton": "USD/ton",
            "usd_sc": "USD/saca",
            "brl_sc": "BRL/saca",
        },
    }

    if resolved:
        result["resolved_from_pipeline"] = resolved

    return result
