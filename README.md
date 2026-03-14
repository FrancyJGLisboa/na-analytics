# na-analytics — Agricultural Commodity Analytics CLI

> Brazilian commodity market analytics powered by daily-updated data. No setup, no database, no API keys.

`na-analytics` is a CLI tool that gives AI agents and humans instant access to Brazilian agricultural commodity analytics — basis, export parity pricing (PPE), futures curves, crush margins, seasonal patterns, breakeven calculations, and profitability matrices.

**Data source:** daily-updated CSVs from [noticiasagricolas_etl](https://github.com/FrancyJGLisboa/noticiasagricolas_etl) — 23 commodities, 158 indicators, 214+ locations, 6+ years of history (2020–present). Updated every business day.

## Install

```bash
git clone https://github.com/FrancyJGLisboa/na-analytics
cd na-analytics
uv pip install -e .
```

Dependencies: `click`, `duckdb`. That's it.

## How It Works

1. You run a command (e.g., `na-analytics spread --commodity soja --indicator ...`)
2. The tool fetches the relevant CSV from GitHub (cached locally for 1 hour)
3. Loads it into an in-memory DuckDB database
4. Runs SQL analytics and returns JSON to stdout

No local data to manage. No database to set up. No API keys.

## Examples

### Find available indicators

Always start here — indicator slugs are needed for most commands:

```bash
$ na-analytics list-indicators --commodity milho
```

```json
{
  "commodity": "milho",
  "indicators": [
    {"indicator": "milho-b3-prego-regular", "indicator_name": "Milho - B3 (Pregão Regular)", "price_basis": "futures", "market_type": "b3"},
    {"indicator": "milho-bolsa-de-chicago-cme-group", "indicator_name": "Milho - Bolsa de Chicago", "price_basis": "futures", "market_type": "cme"},
    {"indicator": "indicador-cepea-esalq-milho", "indicator_name": "Indicador do Milho Esalq/B3", "price_basis": "spot", "market_type": "indicator"},
    {"indicator": "milho-mercado-fisico-sindicatos-e-cooperativas", "indicator_name": "Milho - Mercado Físico", "price_basis": "spot", "market_type": "physical"},
    {"indicator": "milho-mercado-fisico-ms", "indicator_name": "Milho - Mercado Físico - MS", "price_basis": "spot", "market_type": "physical"},
    {"indicator": "milho-disponivel-imea", "indicator_name": "Milho Disponível - IMEA", "price_basis": "spot", "market_type": "physical"}
  ]
}
```

### Regional price spread — where is soy cheapest today?

```bash
$ na-analytics spread --commodity soja --indicator soja-mercado-fisico-sindicatos-e-cooperativas
```

```json
{
  "summary": {"mean": 115.27, "std": 8.42, "min": 99.0, "max": 130.0, "count": 30},
  "by_state": [
    {"state": "MT", "mean": 105.14, "count": 7},
    {"state": "MS", "mean": 110.67, "count": 3},
    {"state": "GO", "mean": 111.50, "count": 2},
    {"state": "PR", "mean": 118.50, "count": 4},
    {"state": "RS", "mean": 119.00, "count": 2},
    {"state": "SP", "mean": 124.00, "count": 2}
  ],
  "extremes": {
    "lowest":  {"location": "Campo Novo do Parecis/MT (Ceres)", "price": 99.0},
    "highest": {"location": "Porto Santos/SP (Dellagro)", "price": 130.0}
  }
}
```

R$99/sc in Mato Grosso interior vs R$130/sc at Santos port — a R$31 logistics spread.

### Export Parity Price (PPE) — what's soy worth at the farm gate?

With explicit inputs:

```bash
$ na-analytics ppe --commodity soja --cbot 1050 --basis-fob 85 --fx 5.75 --logistics 25.24
```

```json
{
  "results": {
    "flat_price_cbu": 1135.0,
    "fob_usd_ton": 417.06,
    "fca_usd_ton": 409.06,
    "exw_usd_ton": 391.82,
    "exw_usd_sc": 23.51,
    "exw_brl_sc": 135.18
  }
}
```

CBOT at 1050¢/bu + 85¢ basis → R$135.18/sc at the farm gate (EXW).

Or let the tool auto-resolve CBOT, basis, and FX from the latest pipeline data:

```bash
$ na-analytics ppe --commodity soja
```

```json
{
  "results": {
    "flat_price_cbu": 1192.03,
    "fob_usd_ton": 438.02,
    "exw_brl_sc": 140.70
  },
  "resolved_from_pipeline": {
    "cbot": 1218.25,
    "cbot_source_date": "2026-03-13",
    "fx": 5.3535,
    "fx_source_date": "2026-03-13",
    "basis_fob": -26.22,
    "basis_source_date": "2026-03-13"
  }
}
```

### Basis across all locations — where is the best basis?

```bash
$ na-analytics basis --commodity soja --all-locations
```

```json
{
  "locations": [
    {"location": "Campo Novo do Parecis/MT", "state": "MT", "avg_basis_brl": -42.07, "avg_basis_pct": -29.82},
    {"location": "Tangará da Serra/MT",      "state": "MT", "avg_basis_brl": -40.07, "avg_basis_pct": -28.40},
    {"location": "Sorriso/MT",               "state": "MT", "avg_basis_brl": -38.87, "avg_basis_pct": -27.55},
    {"location": "Alto Garças/MT",            "state": "MT", "avg_basis_brl": -34.07, "avg_basis_pct": -24.15},
    {"location": "Primavera do Leste/MT",     "state": "MT", "avg_basis_brl": -32.67, "avg_basis_pct": -23.15}
  ]
}
```

Sorted worst-to-best — MT interior has the widest (most negative) basis, as expected.

### Long/short basis signal — should I sell physical or futures?

```bash
$ na-analytics basis-signal --commodity soja --location "Paranaguá"
```

```json
{
  "signal": "long_basis",
  "explanation": "Basis wider than seasonal average — consider selling physical, futures will converge.",
  "current_basis": -9.86,
  "seasonal_average": 0.88,
  "current_month": 3,
  "data_date": "2026-03-13"
}
```

Current basis (-9.86) is well below the March seasonal average (+0.88) → long basis signal.

### Breakeven — what CBOT price covers my costs?

```bash
$ na-analytics breakeven --commodity soja --cost-brl-ha 4500 --productivity 55 --fx 5.75 --logistics-usd-ton 25 --basis 85
```

```json
{
  "results": {
    "cost_usd_ha": 782.61,
    "cost_usd_sc": 14.23,
    "cost_cbu": 645.43,
    "logistics_cbu": 68.04,
    "breakeven_cbot_cbu": 628.47
  }
}
```

With costs at R$4,500/ha and 55 sc/ha productivity, CBOT needs to be above 628¢/bu to break even.

### Profitability matrix — what if productivity or price changes?

```bash
$ na-analytics profitability --cost-brl-ha 4500 --base-productivity 55 --base-price-brl-sc 130 --prod-steps 3 --price-steps 3
```

| Productivity (sc/ha) | R$104/sc | R$130/sc | R$156/sc |
|---------------------|----------|----------|----------|
| **44** | R$76/ha | R$1,220/ha | R$2,364/ha |
| **55** | R$1,220/ha | R$2,650/ha | R$4,080/ha |
| **66** | R$2,364/ha | R$4,080/ha | R$5,796/ha |

At 55 sc/ha and R$130/sc → R$2,650/ha profit. But if productivity drops to 44 and price drops to R$104 → barely R$76/ha.

## All Commands

| Command | Description |
|---------|-------------|
| `list-indicators` | List available indicator slugs for a commodity |
| `basis` | Basis = physical - futures (with PTAX FX) |
| `basis-signal` | Long/short basis strategy classification |
| `futures-curve` | Futures curve with contango/backwardation |
| `crush-margin` | Soy crush margin (farelo + oleo - soja) |
| `seasonal` | Multi-year monthly averages vs current year |
| `spread` | Regional price spread by state/location |
| `fx-adjusted` | BRL/USD conversion via PTAX |
| `ppe` | Export Parity Price (CBOT → FOB → EXW in R$/sc) |
| `breakeven` | Minimum CBOT price to cover production costs |
| `profitability` | Productivity x price profit/loss matrix |

## Common Indicator Slugs

| Commodity | Slug | Description |
|-----------|------|-------------|
| soja | `soja-mercado-fisico-sindicatos-e-cooperativas` | Physical spot prices |
| soja | `soja-bolsa-de-chicago-cme-group` | CBOT futures |
| soja | `soja-b3-pregao-regular` | B3 futures |
| soja | `farelo-de-soja-chicago-cbot` | CBOT soy meal |
| soja | `oleo-de-soja-chicago-cbot` | CBOT soy oil |
| milho | `milho-mercado-fisico-sindicatos-e-cooperativas` | Physical corn prices |
| milho | `milho-bolsa-de-chicago-cme-group` | CBOT corn futures |
| milho | `milho-b3-prego-regular` | B3 corn futures |
| boi-gordo | `boi-gordo-mercado-fisico-scot-consultoria` | Cattle physical prices |
| boi-gordo | `boi-gordo-b3-pregao-regular` | B3 cattle futures |
| cafe | `cafe-mercado-fisico` | Coffee physical prices |
| cafe | `cafe-bolsa-de-nova-york-ice-us` | ICE coffee futures |

Run `na-analytics list-indicators --commodity X` for the full list.

## Data

All data comes from [noticiasagricolas_etl](https://github.com/FrancyJGLisboa/noticiasagricolas_etl):

- **23 commodities** — soja, milho, cafe, boi-gordo, trigo, algodao, sucroenergetico, arroz, and more
- **158 indicators** — CBOT, B3, CME, CEPEA/ESALQ, cooperatives, Scot Consultoria
- **214+ locations** across Brazil — MT, MS, PR, SP, GO, BA, RS, MG, SC, DF
- **6+ years of history** — daily data from 2020-01-02 to present
- **Updated every business day** — GitHub Actions at 22:00 UTC (19:00 BRT)
- **Pre-built basis** — for soja, milho, cafe, boi-gordo, trigo, algodao

Data is fetched on demand from GitHub and cached locally for 1 hour at `~/.cache/na-analytics/`.

## License

MIT
