# Code samples

Two small, self-contained modules written for this repository in the style of the Varifa codebase. They are not extracted from the private source, contain no licensing or security logic, and need nothing beyond the Python standard library.

| Module | What it shows |
|---|---|
| [`varifa_samples/jalali.py`](varifa_samples/jalali.py) | Jalali (Persian) ↔ Gregorian date conversion and RTL-friendly formatting. Every date in Varifa is shown in the Jalali calendar while PostgreSQL stores Gregorian dates. |
| [`varifa_samples/migrations.py`](varifa_samples/migrations.py) | The migration-first start-up pattern: ordered SQL files applied on every launch, one transaction each, with a checksum guard that stops start-up if an already-applied migration was edited. |

## Run the tests

Python 3.10 or newer, no packages to install:

```bash
cd samples
python -m unittest discover -s tests -v
```

The Jalali tests include a day-by-day round trip over fifty years. The migration tests run against an in-memory SQLite database, so no PostgreSQL server is needed; in the app itself the same runner is used with PostgreSQL.

## Example

```python
from datetime import date
from varifa_samples.jalali import JalaliDate

d = JalaliDate.from_gregorian(date(2026, 8, 11))
print(d.isoformat())          # 1405/05/20
print(d.persian(long=True))   # ۲۰ مرداد ۱۴۰۵
print(d.to_gregorian())       # 2026-08-11
```
