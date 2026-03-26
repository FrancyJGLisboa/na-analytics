import json
import sys
from datetime import date, datetime
from decimal import Decimal


def _default(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def success(data: dict) -> None:
    print(json.dumps(data, default=_default, ensure_ascii=False))


def error(message: str, hint: str | None = None, errors: list | None = None, exit_code: int = 1) -> None:
    payload = {"error": message, "error_type": "validation" if errors else "runtime"}
    if hint:
        payload["hint"] = hint
    if errors:
        payload["details"] = errors
    print(json.dumps(payload, default=_default, ensure_ascii=False), file=sys.stderr)
    sys.exit(exit_code)
