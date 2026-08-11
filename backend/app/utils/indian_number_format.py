"""
ChargeMesh — Indian Number Formatting Utilities
Formats numbers in Indian numbering system (lakhs, crores).
"""


def format_inr(amount: float, symbol: str = "₹") -> str:
    """Format amount in Indian Rupees with proper grouping (lakhs, crores)."""
    if amount >= 1_00_00_000:  # 1 crore
        return f"{symbol}{amount / 1_00_00_000:.2f}Cr"
    elif amount >= 1_00_000:  # 1 lakh
        return f"{symbol}{amount / 1_00_000:.2f}L"
    else:
        # Indian grouping: 1,00,000 format
        return f"{symbol}{_indian_grouping(amount)}"


def _indian_grouping(amount: float) -> str:
    """Apply Indian number grouping (thousands, then lakhs)."""
    parts = f"{amount:.2f}".split(".")
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else "00"

    # Last 3 digits, then groups of 2
    if len(integer_part) <= 3:
        return f"{integer_part}.{decimal_part}"

    last3 = integer_part[-3:]
    remaining = integer_part[:-3]
    groups = []
    while remaining:
        groups.append(remaining[-2:])
        remaining = remaining[:-2]
    groups.reverse()
    return ",".join(groups) + "," + last3 + "." + decimal_part


def format_kwh(kwh: float) -> str:
    """Format kWh with appropriate units."""
    if kwh >= 1000:
        return f"{kwh / 1000:.2f} MWh"
    return f"{kwh:.2f} kWh"


def format_km(km: float) -> str:
    """Format kilometers."""
    if km >= 1000:
        return f"{km / 1000:.1f}k km"
    return f"{km:.1f} km"
