"""Input validation and output sanity checks — the harness layer."""


def validate_ppe_inputs(commodity, cbot, basis_fob, fx, logistics, fobbings):
    """Validate PPE inputs before computation. Returns list of errors or empty list."""
    errors = []
    if commodity not in ("soja", "milho"):
        errors.append({"field": "commodity", "error": f"PPE supports 'soja' or 'milho', got '{commodity}'"})
    if cbot is not None:
        if cbot < 0:
            errors.append({"field": "cbot", "error": f"CBOT price cannot be negative ({cbot})"})
        if cbot > 3000:
            errors.append({"field": "cbot", "error": f"CBOT price {cbot} cbu seems too high (max ~3000 for soja)"})
    if basis_fob is not None and abs(basis_fob) > 500:
        errors.append({"field": "basis_fob", "error": f"Basis FOB {basis_fob} cbu seems extreme (typical: -200 to +200)"})
    if fx is not None:
        if fx <= 0:
            errors.append({"field": "fx", "error": f"Exchange rate must be positive ({fx})"})
        if fx > 20:
            errors.append({"field": "fx", "error": f"Exchange rate {fx} BRL/USD seems too high"})
    if logistics < 0:
        errors.append({"field": "logistics", "error": f"Logistics cost cannot be negative ({logistics})"})
    if fobbings < 0:
        errors.append({"field": "fobbings", "error": f"Fobbings cost cannot be negative ({fobbings})"})
    return errors


def validate_breakeven_inputs(commodity, cost_brl_ha, productivity, fx, logistics, basis):
    """Validate breakeven inputs."""
    errors = []
    if commodity not in ("soja", "milho"):
        errors.append({"field": "commodity", "error": f"Breakeven supports 'soja' or 'milho', got '{commodity}'"})
    if cost_brl_ha <= 0:
        errors.append({"field": "cost_brl_ha", "error": f"Production cost must be positive ({cost_brl_ha})"})
    if productivity <= 0:
        errors.append({"field": "productivity", "error": f"Productivity must be positive ({productivity})"})
    if fx <= 0:
        errors.append({"field": "fx", "error": f"Exchange rate must be positive ({fx})"})
    if logistics < 0:
        errors.append({"field": "logistics_usd_ton", "error": f"Logistics cannot be negative ({logistics})"})
    return errors


def validate_profitability_inputs(cost_brl_ha, base_productivity, base_price):
    """Validate profitability matrix inputs."""
    errors = []
    if cost_brl_ha <= 0:
        errors.append({"field": "cost_brl_ha", "error": f"Cost must be positive ({cost_brl_ha})"})
    if base_productivity <= 0:
        errors.append({"field": "base_productivity", "error": f"Productivity must be positive ({base_productivity})"})
    if base_price <= 0:
        errors.append({"field": "base_price_brl_sc", "error": f"Price must be positive ({base_price})"})
    return errors


def check_ppe_sanity(result):
    """Check PPE output for sanity. Attaches warnings."""
    warnings = []
    r = result.get("results", {})
    if r.get("exw_brl_sc") is not None:
        if r["exw_brl_sc"] < 0:
            warnings.append({"field": "exw_brl_sc", "warning": "Negative EXW price — check inputs", "value": r["exw_brl_sc"]})
        if r["exw_brl_sc"] > 500:
            warnings.append({"field": "exw_brl_sc", "warning": "EXW above R$500/sc — unusually high", "value": r["exw_brl_sc"]})
    if r.get("fob_usd_ton") is not None and r["fob_usd_ton"] < 0:
        warnings.append({"field": "fob_usd_ton", "warning": "Negative FOB price", "value": r["fob_usd_ton"]})
    if warnings:
        result["_warnings"] = warnings
    return result


def check_breakeven_sanity(result):
    """Check breakeven output for sanity."""
    warnings = []
    r = result.get("results", {})
    be = r.get("breakeven_cbot_cbu")
    if be is not None:
        if be < 0:
            warnings.append({"field": "breakeven_cbot_cbu", "warning": "Negative breakeven — costs may be wrong", "value": be})
        if be > 2500:
            warnings.append({"field": "breakeven_cbot_cbu", "warning": "Breakeven above 2500 cbu — unusually high", "value": be})
    if warnings:
        result["_warnings"] = warnings
    return result
