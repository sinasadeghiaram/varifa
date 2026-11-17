"""Jalali (Persian / Solar Hijri) calendar helpers.

Every date a Varifa user sees — invoices, payroll periods, reports — is shown
in the Jalali calendar, while PostgreSQL stores plain Gregorian dates. This
module converts between the two and formats dates for a right-to-left UI.

Leap years follow the 33-year "breaks" arithmetic used by the Iranian
calendar authority, which is exact for the years 1-3177 SH.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

# Years at which the 33-year leap cycle shifts (Borkowski / jalaali-js).
_BREAKS = (
    -61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
    1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178,
)

MONTH_NAMES = (
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
)

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _div(a: int, b: int) -> int:
    """Integer division truncated toward zero (like C / JavaScript)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def _mod(a: int, b: int) -> int:
    return a - _div(a, b) * b


def _year_info(jy: int) -> tuple[int, int, int]:
    """Return (leap, gregorian_year, march_day) for Jalali year ``jy``.

    ``leap == 0`` means ``jy`` is a leap year. ``march_day`` is the day of
    March (in ``gregorian_year``) on which 1 Farvardin of ``jy`` falls.
    """
    if not _BREAKS[0] < jy < _BREAKS[-1]:
        raise ValueError(f"Jalali year out of supported range: {jy}")

    gy = jy + 621
    leap_j = -14
    jp = _BREAKS[0]
    jump = 0
    for jm in _BREAKS[1:]:
        jump = jm - jp
        if jy < jm:
            break
        leap_j += _div(jump, 33) * 8 + _div(_mod(jump, 33), 4)
        jp = jm

    n = jy - jp
    leap_j += _div(n, 33) * 8 + _div(_mod(n, 33) + 3, 4)
    if _mod(jump, 33) == 4 and jump - n == 4:
        leap_j += 1

    leap_g = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march_day = 20 + leap_j - leap_g

    if jump - n < 6:
        n = n - jump + _div(jump + 4, 33) * 33
    leap = _mod(_mod(n + 1, 33) - 1, 4)
    if leap == -1:
        leap = 4
    return leap, gy, march_day


def is_leap(jy: int) -> bool:
    return _year_info(jy)[0] == 0


def month_length(jy: int, jm: int) -> int:
    if not 1 <= jm <= 12:
        raise ValueError(f"Month must be 1-12, got {jm}")
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    return 30 if is_leap(jy) else 29


@dataclass(frozen=True, order=True)
class JalaliDate:
    year: int
    month: int
    day: int

    def __post_init__(self) -> None:
        if not 1 <= self.day <= month_length(self.year, self.month):
            raise ValueError(f"Invalid Jalali date: {self.year}/{self.month}/{self.day}")

    @classmethod
    def from_gregorian(cls, d: date) -> "JalaliDate":
        jy = d.year - 621
        leap, gy, march_day = _year_info(jy)
        k = (d - date(gy, 3, march_day)).days
        if k >= 0:
            if k <= 185:  # first six months have 31 days
                return cls(jy, 1 + k // 31, k % 31 + 1)
            k -= 186
        else:  # still in the previous Jalali year
            jy -= 1
            k += 179
            if leap == 1:  # previous year was a leap year
                k += 1
        return cls(jy, 7 + k // 30, k % 30 + 1)

    def to_gregorian(self) -> date:
        _, gy, march_day = _year_info(self.year)
        day_of_year = (self.month - 1) * 31 - (self.month // 7) * (self.month - 7) + self.day - 1
        return date(gy, 3, march_day) + timedelta(days=day_of_year)

    @classmethod
    def today(cls) -> "JalaliDate":
        return cls.from_gregorian(date.today())

    def isoformat(self) -> str:
        """``1405/05/20`` — the format used in invoices and reports."""
        return f"{self.year:04d}/{self.month:02d}/{self.day:02d}"

    def persian(self, long: bool = False) -> str:
        """Persian digits; ``long=True`` gives ``۲۰ مرداد ۱۴۰۵``."""
        if long:
            text = f"{self.day} {MONTH_NAMES[self.month - 1]} {self.year}"
        else:
            text = self.isoformat()
        return text.translate(_PERSIAN_DIGITS)
