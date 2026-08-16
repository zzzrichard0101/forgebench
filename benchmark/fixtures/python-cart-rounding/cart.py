"""Tiny invoice calculation fixture used by the public ForgeBench example."""

from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")


def line_total(quantity: int, unit_price: Decimal) -> Decimal:
    return (Decimal(quantity) * unit_price).quantize(CENT, rounding=ROUND_HALF_UP)


def invoice_total(items: list[tuple[int, Decimal]]) -> Decimal:
    """Return the amount charged for an invoice.

    BUG: the UI displays rounded line totals, but this implementation sums the
    unrounded values and rounds only once at the end.
    """

    raw_total = sum((Decimal(quantity) * price for quantity, price in items), Decimal("0"))
    return raw_total.quantize(CENT, rounding=ROUND_HALF_UP)

