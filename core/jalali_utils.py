"""
Self-contained Gregorian <-> Jalali (Persian/Shamsi) calendar conversion.

Implemented independently of any third-party library or the OS/browser locale
database, per project requirement: the system owns its own calendar logic so
official holidays and occasions can be layered on top of it later.

Algorithm: the well-established astronomical Jalali calendar algorithm
(as used by the widely-referenced "jalaali-js" implementation), which is
accurate for Jalali years roughly in the range 1 to 3177.
"""

_BREAKS = [
    -61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
    1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178,
]

PERSIAN_MONTH_NAMES = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]

PERSIAN_WEEKDAY_NAMES = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]


def _div(a, b):
    # Truncating division toward zero (like JS's ~~(a/b)), NOT Python's
    # floor-toward-negative-infinity `//`. This distinction matters because
    # several intermediate values in this algorithm (e.g. gm - 8) are
    # negative, and floor-division there silently produces wrong results.
    q = a / b
    return int(q) if q >= 0 else -int(-q)


def _mod(a, b):
    return a - _div(a, b) * b


def _jal_cal(jy):
    bl = len(_BREAKS)
    gy = jy + 621
    leap_j = -14
    jp = _BREAKS[0]
    if jy < jp or jy >= _BREAKS[bl - 1]:
        raise ValueError(f"Invalid Jalali year {jy}")

    jm = jp
    jump = 0
    for i in range(1, bl):
        jm = _BREAKS[i]
        jump = jm - jp
        if jy < jm:
            break
        leap_j = leap_j + _div(jump, 33) * 8 + _div(_mod(jump, 33), 4)
        jp = jm

    n = jy - jp
    leap_j = leap_j + _div(n, 33) * 8 + _div(_mod(n, 33) + 3, 4)
    if _mod(jump, 33) == 4 and jump - n == 4:
        leap_j += 1

    leap_g = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g

    if jump - n < 6:
        n = n - jump + _div(jump, 33) * 33
    leap = _mod(_mod(n + 1, 33) - 1, 4)
    if leap == -1:
        leap = 4

    return {"leap": leap, "gy": gy, "march": march}


def _g2d(gy, gm, gd):
    d = (
        _div((gy + _div(gm - 8, 6) + 100100) * 1461, 4)
        + _div(153 * _mod(gm + 9, 12) + 2, 5)
        + gd
        - 34840408
    )
    d = d - _div(_div(gy + 100100 + _div(gm - 8, 6), 100) * 3, 4) + 752
    return d


def _d2g(jdn):
    j = 4 * jdn + 139361631
    j = j + _div(_div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908
    i = _div(_mod(j, 1461), 4) * 5 + 308
    gd = _div(_mod(i, 153), 5) + 1
    gm = _mod(_div(i, 153), 12) + 1
    gy = _div(j, 1461) - 100100 + _div(8 - gm, 6)
    return gy, gm, gd


def _j2d(jy, jm, jd):
    r = _jal_cal(jy)
    return _g2d(r["gy"], 3, r["march"]) + (jm - 1) * 31 - _div(jm, 7) * (jm - 7) + jd - 1


def _d2j(jdn):
    gy, _, _ = _d2g(jdn)
    jy = gy - 621
    r = _jal_cal(jy)
    jdn1f = _g2d(r["gy"], 3, r["march"])
    k = jdn - jdn1f
    if k >= 0:
        if k <= 185:
            jm = 1 + _div(k, 31)
            jd = _mod(k, 31) + 1
            return jy, jm, jd
        k -= 186
    else:
        jy -= 1
        k += 179
        if r["leap"] == 1:
            k += 1
    jm = 7 + _div(k, 30)
    jd = _mod(k, 30) + 1
    return jy, jm, jd


def gregorian_to_jalali(gy, gm, gd):
    """Returns (jy, jm, jd) for a given Gregorian date."""
    return _d2j(_g2d(gy, gm, gd))


def jalali_to_gregorian(jy, jm, jd):
    """Returns (gy, gm, gd) for a given Jalali date."""
    return _d2g(_j2d(jy, jm, jd))


def date_to_jalali(date_obj):
    """Converts a datetime.date to (jy, jm, jd)."""
    return gregorian_to_jalali(date_obj.year, date_obj.month, date_obj.day)


def jalali_to_date(jy, jm, jd):
    """Converts (jy, jm, jd) to a datetime.date."""
    from datetime import date
    gy, gm, gd = jalali_to_gregorian(jy, jm, jd)
    return date(gy, gm, gd)


def is_jalali_leap_year(jy):
    return _jal_cal(jy)["leap"] == 0


FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def to_fa_digits(value):
    """Converts any string/number containing ASCII digits to Persian digits."""
    return "".join(FA_DIGITS[int(ch)] if ch.isdigit() else ch for ch in str(value))


def format_jalali(date_obj, with_weekday=False):
    """Formats a datetime.date as a Persian-digit Jalali string: ۱۴۰۵/۰۵/۰۶"""
    jy, jm, jd = date_to_jalali(date_obj)
    formatted = to_fa_digits(f"{jy:04d}/{jm:02d}/{jd:02d}")
    if with_weekday:
        weekday = PERSIAN_WEEKDAY_NAMES[(date_obj.weekday() + 2) % 7]  # Python Mon=0 -> Sat=0
        return f"{weekday} {formatted}"
    return formatted
