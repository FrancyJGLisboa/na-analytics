"""Data layer: fetch CSVs from GitHub (public repo), cache locally, query via DuckDB."""

import datetime
import urllib.request
from pathlib import Path

import duckdb

GITHUB_RAW = "https://raw.githubusercontent.com/FrancyJGLisboa/noticiasagricolas_etl/main/data/csv"
CACHE_DIR = Path.home() / ".cache" / "na-analytics"
CACHE_TTL_SECONDS = 3600  # 1 hour

VALID_COMMODITIES = [
    "algodao", "amendoim", "arroz", "boi-gordo", "cacau", "cafe",
    "frango", "frutas", "laranja", "latex", "legumes", "leite",
    "mandioca", "mercado-financeiro", "milho", "ovos", "silvicultura",
    "soja", "sorgo", "sucroenergetico", "suinos", "trigo", "verduras",
]

_db = None


def _get_db() -> duckdb.DuckDBPyConnection:
    global _db
    if _db is None:
        _db = duckdb.connect(":memory:")
    return _db


def _cache_path(name: str) -> Path:
    return CACHE_DIR / f"{name}.csv"


def _cache_ts_path(name: str) -> Path:
    return CACHE_DIR / f"{name}.ts"


def _is_cached(name: str) -> bool:
    csv = _cache_path(name)
    ts = _cache_ts_path(name)
    if not csv.exists() or not ts.exists():
        return False
    try:
        cached_at = float(ts.read_text().strip())
        return (datetime.datetime.now().timestamp() - cached_at) < CACHE_TTL_SECONDS
    except (ValueError, OSError):
        return False


def _fetch_csv(name: str) -> Path:
    """Fetch CSV from GitHub raw URL, cache locally."""
    if _is_cached(name):
        return _cache_path(name)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    url = f"{GITHUB_RAW}/{name}.csv"

    max_retries = 3
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "na-analytics/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                content = resp.read()
            break  # success
        except urllib.error.HTTPError as e:
            if e.code == 404:
                from . import output
                output.error(
                    f"CSV not found: {name}.csv",
                    hint=f"Valid commodities: {', '.join(VALID_COMMODITIES)}",
                )
            if e.code in (429, 500, 502, 503) and attempt < max_retries:
                import time
                time.sleep(2 ** attempt)
                last_error = e
                continue
            from . import output
            output.error(f"GitHub fetch error: {e.code}", hint=str(e.reason))
        except urllib.error.URLError as e:
            if attempt < max_retries:
                import time
                time.sleep(2 ** attempt)
                last_error = e
                continue
            if _cache_path(name).exists():
                return _cache_path(name)
            from . import output
            output.error(
                f"Cannot reach GitHub after {max_retries + 1} attempts and no cached data",
                hint="Check internet connection.",
            )

    csv_path = _cache_path(name)
    csv_path.write_bytes(content)
    _cache_ts_path(name).write_text(str(datetime.datetime.now().timestamp()))
    return csv_path


def _table_loaded(name: str) -> bool:
    db = _get_db()
    try:
        db.execute(f'SELECT 1 FROM "{name}" LIMIT 1')
        return True
    except duckdb.CatalogException:
        return False


def load_commodity(commodity: str) -> str:
    """Ensure commodity CSV is loaded into DuckDB. Returns table name."""
    if _table_loaded(commodity):
        return commodity

    csv_path = _fetch_csv(commodity)
    db = _get_db()
    db.execute(f"""
        CREATE TABLE IF NOT EXISTS "{commodity}" AS
        SELECT * FROM read_csv_auto('{csv_path}', header=true, sample_size=-1)
    """)
    return commodity


def load_basis(commodity: str) -> str:
    """Load pre-built basis CSV if available."""
    name = f"basis-{commodity}"
    if _table_loaded(name):
        return name

    csv_path = _fetch_csv(name)
    db = _get_db()
    db.execute(f"""
        CREATE TABLE IF NOT EXISTS "{name}" AS
        SELECT * FROM read_csv_auto('{csv_path}', header=true, sample_size=-1)
    """)
    return name


def list_indicators(commodity: str) -> list[dict]:
    """List all indicators for a commodity."""
    table = load_commodity(commodity)
    rows = query(f"""
        SELECT DISTINCT indicator, indicator_name, price_basis, market_type
        FROM "{table}"
        ORDER BY price_basis, indicator_name
    """)
    return rows


def query(sql: str, params: list | None = None) -> list[dict]:
    db = _get_db()
    if params:
        result = db.execute(sql, params)
    else:
        result = db.execute(sql)
    columns = [desc[0] for desc in result.description]
    rows = result.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def validate_commodity(commodity: str) -> None:
    if commodity not in VALID_COMMODITIES:
        from . import output
        output.error(
            f"Invalid commodity: '{commodity}'",
            hint=f"Valid commodities: {', '.join(VALID_COMMODITIES)}",
        )
