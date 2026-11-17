import unittest
from datetime import date, timedelta

from varifa_samples.jalali import JalaliDate, is_leap, month_length


class KnownDates(unittest.TestCase):
    CASES = [
        (date(2023, 3, 21), JalaliDate(1402, 1, 1)),
        (date(2024, 3, 20), JalaliDate(1403, 1, 1)),
        (date(2025, 3, 20), JalaliDate(1403, 12, 30)),  # last day of a leap year
        (date(2025, 3, 21), JalaliDate(1404, 1, 1)),
        (date(2026, 3, 21), JalaliDate(1405, 1, 1)),
        (date(2026, 8, 11), JalaliDate(1405, 5, 20)),
        (date(2026, 9, 22), JalaliDate(1405, 6, 31)),
        (date(2026, 9, 23), JalaliDate(1405, 7, 1)),
    ]

    def test_gregorian_to_jalali(self):
        for g, j in self.CASES:
            with self.subTest(g=g):
                self.assertEqual(JalaliDate.from_gregorian(g), j)

    def test_jalali_to_gregorian(self):
        for g, j in self.CASES:
            with self.subTest(j=j):
                self.assertEqual(j.to_gregorian(), g)


class Calendar(unittest.TestCase):
    def test_leap_years(self):
        self.assertTrue(is_leap(1399))
        self.assertTrue(is_leap(1403))
        self.assertFalse(is_leap(1402))
        self.assertFalse(is_leap(1404))

    def test_month_lengths(self):
        self.assertEqual(month_length(1405, 1), 31)
        self.assertEqual(month_length(1405, 7), 30)
        self.assertEqual(month_length(1403, 12), 30)
        self.assertEqual(month_length(1404, 12), 29)

    def test_invalid_dates_rejected(self):
        with self.assertRaises(ValueError):
            JalaliDate(1404, 12, 30)  # 1404 is not a leap year
        with self.assertRaises(ValueError):
            JalaliDate(1405, 13, 1)

    def test_round_trip_every_day_for_fifty_years(self):
        d, end = date(2000, 1, 1), date(2050, 12, 31)
        previous = None
        while d <= end:
            j = JalaliDate.from_gregorian(d)
            self.assertEqual(j.to_gregorian(), d)
            if previous is not None:
                self.assertLess(previous, j)  # strictly increasing, no gaps reused
            previous = j
            d += timedelta(days=1)


class Formatting(unittest.TestCase):
    def test_formats(self):
        j = JalaliDate(1405, 5, 20)
        self.assertEqual(j.isoformat(), "1405/05/20")
        self.assertEqual(j.persian(), "۱۴۰۵/۰۵/۲۰")
        self.assertEqual(j.persian(long=True), "۲۰ مرداد ۱۴۰۵")


if __name__ == "__main__":
    unittest.main()
