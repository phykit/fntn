"""US exchange business-day calendar for the kill tests of 15 October 2026 (PREREG A section 3).

The holiday list is an operator-side reconstruction of the CME calendar: New Year's Day, Martin
Luther King Day (from 1998), Presidents' Day, Good Friday, Memorial Day, Juneteenth (from 2022),
Independence Day, Labor Day, Thanksgiving, Christmas. Saturday holidays observed on the Friday
(except New Year's Day), Sunday holidays on the Monday. The reason the reconstruction is written
out rather than imported: nothing here may depend on a package whose calendar changes under it,
and the independent implementation must be able to reproduce it from the text.
"""
import datetime as dt
from functools import lru_cache


def easter(y):
    a = y % 19
    b, c = divmod(y, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return dt.date(y, month, day)


def nth_weekday(y, m, weekday, n):
    d = dt.date(y, m, 1)
    d += dt.timedelta(days=(weekday - d.weekday()) % 7)
    return d + dt.timedelta(days=7 * (n - 1))


def last_weekday_of(y, m, weekday):
    d = (dt.date(y, m, 1) + dt.timedelta(days=32)).replace(day=1) - dt.timedelta(days=1)
    while d.weekday() != weekday:
        d -= dt.timedelta(days=1)
    return d


def observed(d, newyear=False):
    if d.weekday() == 5:
        return None if newyear else d - dt.timedelta(days=1)
    if d.weekday() == 6:
        return d + dt.timedelta(days=1)
    return d


@lru_cache(maxsize=None)
def holidays(y):
    out = set()
    for d in (observed(dt.date(y, 1, 1), newyear=True), observed(dt.date(y, 7, 4)), observed(dt.date(y, 12, 25))):
        if d is not None:
            out.add(d)
    if y >= 1998:
        out.add(nth_weekday(y, 1, 0, 3))
    out.add(nth_weekday(y, 2, 0, 3))
    out.add(easter(y) - dt.timedelta(days=2))
    out.add(last_weekday_of(y, 5, 0))
    if y >= 2022:
        d = observed(dt.date(y, 6, 19))
        if d is not None:
            out.add(d)
    out.add(nth_weekday(y, 9, 0, 1))
    out.add(nth_weekday(y, 11, 3, 4))
    return out


def is_business_day(d):
    return d.weekday() < 5 and d not in holidays(d.year) and d not in holidays(d.year - 1) and d not in holidays(d.year + 1)


def expiry_for_delivery(asset, y, m):
    """NG: third business day counting back from the last day of the preceding month inclusive.
    HO, RB: the last business day of the preceding month."""
    d = dt.date(y, m, 1) - dt.timedelta(days=1)
    need = 3 if asset == "ng" else 1
    n = 0
    while True:
        if is_business_day(d):
            n += 1
            if n == need:
                return d
        d -= dt.timedelta(days=1)


def months_between(d0, d1):
    y, m = d0.year, d0.month
    out = []
    while (y, m) <= (d1.year, d1.month):
        out.append((y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out
