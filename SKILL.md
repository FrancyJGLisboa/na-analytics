---
name: na-analytics
description: >-
  Agricultural commodity analytics CLI for Brazilian markets — basis, PPE,
  futures curves, crush margins, seasonal patterns, breakeven, profitability.
  Fetches daily-updated data from GitHub. No local data setup required.
  Triggers on: basis analysis, export parity price, PPE soja milho, futures
  curve contango backwardation, crush margin, seasonal pattern, regional spread,
  fx adjusted pricing, breakeven CBOT, profitability matrix, agricultural
  commodity analytics, Brazilian grain market, noticiasagricolas, soybean price,
  corn price, cattle price.
license: MIT
---

# na-analytics

Agricultural commodity analytics CLI for Brazilian markets. Fetches daily-updated CSV data directly from [noticiasagricolas_etl](https://github.com/FrancyJGLisboa/noticiasagricolas_etl) on GitHub. All output is JSON to stdout; errors are JSON to stderr with exit code 1.

**No local data setup required.** Data is fetched on demand and cached for 1 hour.

## Important: Finding Indicator Slugs

Most commands require an `--indicator` slug. **Always run `list-indicators` first** to find the correct slug for a commodity:

```bash
na-analytics list-indicators --commodity soja
na-analytics list-indicators --commodity milho
na-analytics list-indicators --commodity boi-gordo
```

### Common indicator slugs

| Commodity | Slug | Description | Type |
|-----------|------|-------------|------|
| soja | `soja-mercado-fisico-sindicatos-e-cooperativas` | Physical spot prices by location | spot |
| soja | `soja-bolsa-de-chicago-cme-group` | CBOT soybean futures | futures |
| soja | `soja-b3-pregao-regular` | B3 soybean futures | futures |
| soja | `farelo-de-soja-chicago-cbot` | CBOT soybean meal | futures |
| soja | `oleo-de-soja-chicago-cbot` | CBOT soybean oil | futures |
| milho | `milho-mercado-fisico-26` | Physical corn prices by location | spot |
| milho | `milho-bolsa-de-chicago-cme-group` | CBOT corn futures | futures |
| milho | `milho-b3-pregao-regular` | B3 corn futures | futures |
| boi-gordo | `boi-gordo-mercado-fisico-scot-consultoria` | Cattle physical prices | spot |
| boi-gordo | `boi-gordo-b3-pregao-regular` | B3 cattle futures | futures |
| cafe | `cafe-bolsa-de-nova-york-ice-us` | ICE coffee futures | futures |
| cafe | `cafe-mercado-fisico` | Physical coffee prices | spot |

## Commands

### list-indicators
List all available indicator slugs for a commodity. **Run this first.**
```bash
na-analytics list-indicators --commodity soja
na-analytics list-indicators --commodity milho
```
Options: `--commodity` (required)

### basis
Basis = physical price - futures price. Uses pre-built basis data with PTAX FX adjustment.
```bash
na-analytics basis --commodity soja --location "Paranaguá"
na-analytics basis --commodity soja --location "Sorriso" --date-from 2024-01-01 --date-to 2024-06-30
na-analytics basis --commodity soja --all-locations
```
Options: `--commodity` (required), `--location` (partial match), `--date-from`, `--date-to`, `--all-locations`

Basis available for: soja, milho, boi-gordo, cafe, trigo, algodao

### futures-curve
Futures curve with contango/backwardation label.
```bash
na-analytics futures-curve --commodity soja --indicator soja-bolsa-de-chicago-cme-group
na-analytics futures-curve --commodity milho --indicator milho-b3-pregao-regular --date 2024-06-17
```
Options: `--commodity` (required), `--indicator` (required), `--date`

### crush-margin
Soy crush margin: (farelo + oleo) - soja.
```bash
na-analytics crush-margin
na-analytics crush-margin --date-from 2024-01-01 --date-to 2024-06-30
```
Options: `--date-from`, `--date-to`, `--contract`

### seasonal
Multi-year monthly averages vs current year.
```bash
na-analytics seasonal --commodity soja --indicator soja-mercado-fisico-sindicatos-e-cooperativas --location "Paranaguá"
na-analytics seasonal --commodity milho --indicator milho-mercado-fisico-26
```
Options: `--commodity` (required), `--indicator` (required), `--location`, `--measure`

### spread
Regional price spread statistics with by-state breakdown.
```bash
na-analytics spread --commodity soja --indicator soja-mercado-fisico-sindicatos-e-cooperativas
na-analytics spread --commodity milho --indicator milho-mercado-fisico-26 --date 2024-06-17
```
Options: `--commodity` (required), `--indicator` (required), `--date`

### fx-adjusted
BRL/USD conversion via PTAX exchange rate.
```bash
na-analytics fx-adjusted --commodity soja --indicator soja-mercado-fisico-sindicatos-e-cooperativas --target-currency USD
```
Options: `--commodity` (required), `--indicator` (required), `--target-currency`, `--date-from`, `--date-to`

### ppe
Export Parity Price: CBOT + Basis FOB → FOB → FCA → EXW in R$/sc.

When `--cbot`, `--basis-fob`, or `--fx` are omitted, values are **auto-resolved** from the latest pipeline data.
```bash
# All params explicit (from course examples):
na-analytics ppe --commodity soja --cbot 840 --basis-fob 85 --fx 5.80 --logistics 25.24 --fobbings 8
na-analytics ppe --commodity milho --cbot 340 --basis-fob 55 --fx 5.80 --logistics 25.24

# Auto-resolve CBOT and FX from latest pipeline data:
na-analytics ppe --commodity soja --basis-fob 85 --logistics 25.24
na-analytics ppe --commodity soja
```
Options: `--commodity` (required), `--cbot` (auto-resolved), `--basis-fob` (auto-resolved), `--fx` (auto-resolved), `--logistics`, `--fobbings`

ANEC conversion factors: Soja bu→ton = 36.7454, bu→saca = 2.2046 | Milho bu→ton = 39.3678, bu→saca = 2.3621

### basis-signal
Long/short basis strategy classification based on seasonal comparison.
```bash
na-analytics basis-signal --commodity soja --location "Paranaguá"
na-analytics basis-signal --commodity milho --location "Sorriso"
```
Options: `--commodity` (required), `--location` (required, partial match)

Signals: `long_basis` (basis wider than seasonal avg → sell physical), `short_basis` (basis narrower → sell futures)

### breakeven
Minimum CBOT price (¢/bu) to cover production costs.
```bash
na-analytics breakeven --commodity soja --cost-brl-ha 4500 --productivity 55 --fx 5.80 --logistics-usd-ton 25 --basis 85
```
Options: `--commodity` (required), `--cost-brl-ha` (required), `--productivity` (required), `--fx` (required), `--logistics-usd-ton`, `--basis`

### profitability
Productivity × price profit/loss matrix in R$/ha.
```bash
na-analytics profitability --cost-brl-ha 4500 --base-productivity 55 --base-price-brl-sc 120
na-analytics profitability --cost-brl-ha 4500 --base-productivity 55 --base-price-brl-sc 120 --prod-steps 7 --price-steps 7
```
Options: `--cost-brl-ha` (required), `--base-productivity` (required), `--base-price-brl-sc` (required), `--prod-steps`, `--price-steps`, `--prod-range-pct`, `--price-range-pct`

## Anti-Goals

- Does NOT provide trade recommendations — analytics only, the human decides
- Does NOT handle options pricing (puts/calls/Greeks)
- Does NOT simulate hedging with margin calls
- Does NOT compute cattle confinement P&L

## Error Handling

All errors output JSON to stderr: `{"error": "message", "hint": "suggested action"}` with exit code 1.

Common errors:
- Unknown indicator slug → run `list-indicators --commodity X` to find the right one
- Invalid commodity → error lists valid commodities
- No internet + no cache → check connection
