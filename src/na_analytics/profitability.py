def compute(
    cost_brl_ha: float,
    base_productivity: float,
    base_price_brl_sc: float,
    prod_steps: int = 5,
    price_steps: int = 5,
    prod_range_pct: float = 20.0,
    price_range_pct: float = 20.0,
) -> dict:
    prod_values = _build_range(base_productivity, prod_steps, prod_range_pct)
    price_values = _build_range(base_price_brl_sc, price_steps, price_range_pct)

    matrix = []
    for prod in prod_values:
        row = []
        for price in price_values:
            cost_per_sc = cost_brl_ha / prod
            profit_brl_ha = (price - cost_per_sc) * prod
            row.append({
                "productivity_sc_ha": round(prod, 2),
                "price_brl_sc": round(price, 2),
                "cost_per_sc_brl": round(cost_per_sc, 2),
                "profit_brl_ha": round(profit_brl_ha, 2),
            })
        matrix.append(row)

    return {
        "inputs": {
            "cost_brl_ha": cost_brl_ha,
            "base_productivity_sc_ha": base_productivity,
            "base_price_brl_sc": base_price_brl_sc,
        },
        "productivity_values": [round(p, 2) for p in prod_values],
        "price_values": [round(p, 2) for p in price_values],
        "matrix": matrix,
        "units": {
            "productivity": "sc/ha",
            "price": "BRL/sc",
            "profit": "BRL/ha",
        },
    }


def _build_range(base: float, steps: int, range_pct: float) -> list[float]:
    if steps <= 1:
        return [base]
    low = base * (1 - range_pct / 100)
    high = base * (1 + range_pct / 100)
    step = (high - low) / (steps - 1)
    return [low + i * step for i in range(steps)]
