from typing import Any, Dict, Mapping


def sanitize_headers(headers: Mapping[str, str] | Any) -> Dict[str, str]:
    """Removes sensitive headers like Authorization."""
    if hasattr(headers, "items"):
        return {k: v for k, v in headers.items() if k.lower() != "authorization"}
    return dict(headers)
