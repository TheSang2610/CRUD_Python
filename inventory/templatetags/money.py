from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def vnd(value):
    """150000 -> '150.000 ₫' (ban goc in ra '150000đ')."""
    try:
        number = Decimal(value or 0)
    except (InvalidOperation, TypeError, ValueError):
        return value
    return f"{number:,.0f}".replace(",", ".") + " ₫"
