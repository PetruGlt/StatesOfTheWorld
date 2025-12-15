import sqlite3


class DataValidator:
    def __init__(self, db_name='states.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def run_all_checks(self):

        self.check_integrity()
        self.report_general_stats()

    def check_integrity(self):
        """Checks for missing critical data (NULLs)."""
        print("\n[1] Integrity check (Searching for null data)...")

        self.cursor.execute("SELECT name FROM countries WHERE population IS NULL OR area_km2 IS NULL")
        bad_rows = self.cursor.fetchall()

        if not bad_rows:
            print("Passed: All countries have Population and Area data.")
        else:
            print(f"Fail: Found {len(bad_rows)} countries with missing data:")
            for row in bad_rows:
                print(f"   - {row[0]}")

    def report_general_stats(self):
        """Calculates totals and averages."""
        print("\n[2] General stats")

        self.cursor.execute("SELECT COUNT(*), SUM(population), AVG(density) FROM countries")
        count, total_pop, avg_density = self.cursor.fetchone()

        print(f"   - Total Countries Scraped: {count}")
        print(f"   - Total World Population (in DB): {total_pop:,.0f}")
        print(f"   - Average Global Density: {avg_density:.2f} people/km^2")

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    validator = DataValidator()
    validator.run_all_checks()
    validator.close()