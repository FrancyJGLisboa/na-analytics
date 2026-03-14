import click

from . import output


@click.group()
def cli():
    """Agricultural commodity analytics for Brazilian markets."""
    pass


@cli.command("list-indicators")
@click.option("--commodity", required=True, help="Commodity slug (e.g. soja, milho)")
def list_indicators(commodity):
    """List available indicator slugs for a commodity."""
    try:
        from . import data
        data.validate_commodity(commodity)
        rows = data.list_indicators(commodity)
        output.success({"commodity": commodity, "indicators": rows})
    except SystemExit:
        raise
    except Exception as e:
        output.error(str(e))


@cli.command()
@click.option("--commodity", required=True, help="Commodity slug (e.g. soja, milho)")
@click.option("--location", default=None, help="Location name (partial match)")
@click.option("--date-from", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--date-to", default=None, help="End date (YYYY-MM-DD)")
@click.option("--all-locations", is_flag=True, default=False, help="Compare all locations")
def basis(commodity, location, date_from, date_to, all_locations):
    """Basis analysis: physical price minus futures price."""
    try:
        from .basis import compute
        result = compute(commodity=commodity, location=location,
                        date_from=date_from, date_to=date_to, all_locations=all_locations)
        if "error" in result:
            output.error(result["error"], result.get("hint"))
        output.success(result)
    except SystemExit:
        raise
    except Exception as e:
        output.error(str(e))


@cli.command("futures-curve")
@click.option("--commodity", required=True, help="Commodity slug")
@click.option("--indicator", required=True, help="Futures indicator slug")
@click.option("--date", default=None, help="Date (YYYY-MM-DD), default: latest")
def futures_curve(commodity, indicator, date):
    """Futures curve with contango/backwardation classification."""
    try:
        from .futures import get_curve
        result = get_curve(commodity=commodity, indicator=indicator, date=date)
        if "error" in result:
            output.error(result["error"], result.get("hint"))
        output.success(result)
    except SystemExit:
        raise
    except Exception as e:
        output.error(str(e))


@cli.command("crush-margin")
@click.option("--date-from", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--date-to", default=None, help="End date (YYYY-MM-DD)")
@click.option("--contract", default=None, help="Contract month filter")
def crush_margin(date_from, date_to, contract):
    """Soy crush margin: farelo + oleo - soja."""
    try:
        from .crush import compute
        result = compute(date_from=date_from, date_to=date_to, contract=contract)
        if "error" in result:
            output.error(result["error"], result.get("hint"))
        output.success(result)
    except SystemExit:
        raise
    except Exception as e:
        output.error(str(e))


@cli.command()
@click.option("--commodity", required=True, help="Commodity slug")
@click.option("--indicator", required=True, help="Indicator slug")
@click.option("--location", default=None, help="Location name (partial match)")
@click.option("--measure", default="price", help="Measure type (default: price)")
def seasonal(commodity, indicator, location, measure):
    """Multi-year seasonal averages vs current year."""
    try:
        from .seasonal import get_seasonal
        result = get_seasonal(commodity=commodity, indicator=indicator,
                             location=location, measure=measure)
        if "error" in result:
            output.error(result["error"], result.get("hint"))
        output.success(result)
    except SystemExit:
        raise
    except Exception as e:
        output.error(str(e))


@cli.command()
@click.option("--commodity", required=True, help="Commodity slug")
@click.option("--indicator", required=True, help="Indicator slug")
@click.option("--date", default=None, help="Date (YYYY-MM-DD), default: latest")
def spread(commodity, indicator, date):
    """Regional price spread statistics."""
    try:
        from .spread import get_regional_spread
        result = get_regional_spread(commodity=commodity, indicator=indicator, date=date)
        if "error" in result:
            output.error(result["error"], result.get("hint"))
        output.success(result)
    except SystemExit:
        raise
    except Exception as e:
        output.error(str(e))


@cli.command("fx-adjusted")
@click.option("--commodity", required=True, help="Commodity slug")
@click.option("--indicator", required=True, help="Indicator slug")
@click.option("--target-currency", default="USD", help="Target currency: USD or BRL")
@click.option("--date-from", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--date-to", default=None, help="End date (YYYY-MM-DD)")
def fx_adjusted(commodity, indicator, target_currency, date_from, date_to):
    """FX-adjusted pricing via PTAX."""
    try:
        from .fx import get_fx_adjusted
        result = get_fx_adjusted(commodity=commodity, indicator=indicator,
                                target_currency=target_currency,
                                date_from=date_from, date_to=date_to)
        if "error" in result:
            output.error(result["error"], result.get("hint"))
        output.success(result)
    except SystemExit:
        raise
    except Exception as e:
        output.error(str(e))


@cli.command()
@click.option("--commodity", required=True, help="soja or milho")
@click.option("--cbot", default=None, type=float, help="CBOT price in cents/bushel (auto-resolved if omitted)")
@click.option("--basis-fob", default=None, type=float, help="Basis FOB in cents/bushel (auto-resolved if omitted)")
@click.option("--fx", default=None, type=float, help="Exchange rate BRL/USD (auto-resolved if omitted)")
@click.option("--logistics", default=0.0, type=float, help="Logistics cost in USD/ton")
@click.option("--fobbings", default=8.0, type=float, help="Fobbings cost in USD/ton (default: 8)")
def ppe(commodity, cbot, basis_fob, fx, logistics, fobbings):
    """Export Parity Price (PPE): CBOT+Basis to EXW in R$/sc.

    When --cbot, --basis-fob, or --fx are omitted, values are auto-resolved
    from the latest pipeline data (requires GitHub access).
    """
    try:
        auto_resolve = cbot is None or basis_fob is None or fx is None
        from .ppe import compute
        result = compute(commodity=commodity, cbot=cbot, basis_fob=basis_fob,
                        fx=fx, logistics_usd_ton=logistics, fobbings=fobbings,
                        auto_resolve=auto_resolve)
        if "error" in result:
            output.error(result["error"], result.get("hint"))
        output.success(result)
    except SystemExit:
        raise
    except Exception as e:
        output.error(str(e))


@cli.command("basis-signal")
@click.option("--commodity", required=True, help="Commodity slug")
@click.option("--location", required=True, help="Location name (partial match)")
def basis_signal_cmd(commodity, location):
    """Long/short basis strategy signal."""
    try:
        from .basis import basis_signal
        result = basis_signal(commodity=commodity, location=location)
        if "error" in result:
            output.error(result["error"], result.get("hint"))
        output.success(result)
    except SystemExit:
        raise
    except Exception as e:
        output.error(str(e))


@cli.command()
@click.option("--commodity", required=True, help="soja or milho")
@click.option("--cost-brl-ha", required=True, type=float, help="Production cost in BRL/ha")
@click.option("--productivity", required=True, type=float, help="Productivity in sc/ha")
@click.option("--fx", required=True, type=float, help="Exchange rate BRL/USD")
@click.option("--logistics-usd-ton", default=0.0, type=float, help="Logistics in USD/ton")
@click.option("--basis", default=0.0, type=float, help="Basis FOB in cents/bushel")
def breakeven(commodity, cost_brl_ha, productivity, fx, logistics_usd_ton, basis):
    """Breakeven CBOT price to cover production costs."""
    try:
        from .breakeven import compute
        result = compute(commodity=commodity, cost_brl_ha=cost_brl_ha,
                        productivity=productivity, fx=fx,
                        logistics_usd_ton=logistics_usd_ton, basis=basis)
        if "error" in result:
            output.error(result["error"])
        output.success(result)
    except SystemExit:
        raise
    except Exception as e:
        output.error(str(e))


@cli.command()
@click.option("--cost-brl-ha", required=True, type=float, help="Production cost in BRL/ha")
@click.option("--base-productivity", required=True, type=float, help="Base productivity in sc/ha")
@click.option("--base-price-brl-sc", required=True, type=float, help="Base price in BRL/sc")
@click.option("--prod-steps", default=5, type=int, help="Number of productivity steps")
@click.option("--price-steps", default=5, type=int, help="Number of price steps")
@click.option("--prod-range-pct", default=20.0, type=float, help="Productivity range +/- percent")
@click.option("--price-range-pct", default=20.0, type=float, help="Price range +/- percent")
def profitability(cost_brl_ha, base_productivity, base_price_brl_sc,
                  prod_steps, price_steps, prod_range_pct, price_range_pct):
    """Profitability matrix: productivity x price grid."""
    try:
        from .profitability import compute
        result = compute(cost_brl_ha=cost_brl_ha, base_productivity=base_productivity,
                        base_price_brl_sc=base_price_brl_sc, prod_steps=prod_steps,
                        price_steps=price_steps, prod_range_pct=prod_range_pct,
                        price_range_pct=price_range_pct)
        if "error" in result:
            output.error(result["error"])
        output.success(result)
    except SystemExit:
        raise
    except Exception as e:
        output.error(str(e))


if __name__ == "__main__":
    cli()
