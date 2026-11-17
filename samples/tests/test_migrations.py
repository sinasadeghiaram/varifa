import sqlite3
import tempfile
import unittest
from pathlib import Path

from varifa_samples.migrations import MigrationError, apply_pending, discover


class MigrationRunnerTest(unittest.TestCase):
    """Runs against SQLite so the tests need no database server."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.conn = sqlite3.connect(":memory:")

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def write(self, name, sql):
        (self.dir / name).write_text(sql, encoding="utf-8")

    def apply(self):
        return apply_pending(self.conn, self.dir, placeholder="?")

    def tables(self):
        rows = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return {r[0] for r in rows}

    def test_applies_in_order_then_does_nothing(self):
        self.write("0002_add_suppliers.sql", "CREATE TABLE suppliers (id INTEGER PRIMARY KEY)")
        self.write("0001_add_customers.sql", "CREATE TABLE customers (id INTEGER PRIMARY KEY)")

        self.assertEqual(self.apply(), ["0001_add_customers.sql", "0002_add_suppliers.sql"])
        self.assertTrue({"customers", "suppliers"} <= self.tables())
        self.assertEqual(self.apply(), [])  # second start-up: nothing pending

    def test_new_migration_picked_up_on_next_start(self):
        self.write("0001_add_customers.sql", "CREATE TABLE customers (id INTEGER PRIMARY KEY)")
        self.apply()
        self.write(
            "0002_customer_archive.sql",
            "ALTER TABLE customers ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1",
        )
        self.assertEqual(self.apply(), ["0002_customer_archive.sql"])

    def test_editing_an_applied_migration_stops_start_up(self):
        self.write("0001_add_customers.sql", "CREATE TABLE customers (id INTEGER PRIMARY KEY)")
        self.apply()
        self.write("0001_add_customers.sql", "CREATE TABLE customers (id INTEGER, name TEXT)")
        with self.assertRaisesRegex(MigrationError, "changed after it was applied"):
            self.apply()

    def test_failed_migration_is_not_recorded_and_stops_later_ones(self):
        self.write("0001_broken.sql", "CREATE TABL oops")
        self.write("0002_add_customers.sql", "CREATE TABLE customers (id INTEGER PRIMARY KEY)")
        with self.assertRaisesRegex(MigrationError, "0001_broken.sql failed"):
            self.apply()
        recorded = self.conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
        self.assertEqual(recorded, 0)
        self.assertNotIn("customers", self.tables())

    def test_badly_named_or_duplicate_files_rejected(self):
        self.write("add_customers.sql", "SELECT 1")
        with self.assertRaisesRegex(MigrationError, "Badly named"):
            discover(self.dir)
        (self.dir / "add_customers.sql").unlink()

        self.write("0001_a.sql", "SELECT 1")
        self.write("0001_b.sql", "SELECT 1")
        with self.assertRaisesRegex(MigrationError, "Duplicate migration version 1"):
            discover(self.dir)


if __name__ == "__main__":
    unittest.main()
