CONVERSION = {
    "soja": {"bu_to_sc": 2.2046, "ton_to_bu_factor": 0.367454},
    "milho": {"bu_to_sc": 2.3621, "ton_to_bu_factor": 0.393678},
}


def compute(
    commodity: str,
    cost_brl_ha: float,
    productivity: float,
    fx: float,
    logistics_usd_ton: float = 0.0,
    basis: float = 0.0,
) -> dict:
    key = commodity.lower()
    if key not in CONVERSION:
        return {"error": f"Breakeven not supported for '{commodity}'. Use 'soja' or 'milho'."}

    conv = CONVERSION[key]

    cost_usd_ha = cost_brl_ha / fx
    cost_usd_sc = cost_usd_ha / productivity
    cost_cbu = (cost_usd_sc / conv["bu_to_sc"]) * 100
    logistics_cbu = logistics_usd_ton / conv["ton_to_bu_factor"]
    breakeven_cbot = cost_cbu + logistics_cbu - basis

    return {
        "commodity": key,
        "inputs": {
            "cost_brl_ha": cost_brl_ha,
            "productivity_sc_ha": productivity,
            "fx_brl_usd": fx,
            "logistics_usd_ton": logistics_usd_ton,
            "basis_fob_cbu": basis,
        },
        "results": {
            "cost_usd_ha": round(cost_usd_ha, 2),
            "cost_usd_sc": round(cost_usd_sc, 4),
            "cost_cbu": round(cost_cbu, 2),
            "logistics_cbu": round(logistics_cbu, 2),
            "breakeven_cbot_cbu": round(breakeven_cbot, 2),
        },
        "units": {
            "cbu": "cents/bushel",
            "usd_ha": "USD/hectare",
            "usd_sc": "USD/saca",
            "sc_ha": "sacas/hectare",
        },
    }
