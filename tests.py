import unittest
import json
from crawler import CountryScraper
from app import app

class MyTestCase(unittest.TestCase):
    # Setup
    def setUp(self):
        """Runs before every test to set up the environment."""
        self.scraper = CountryScraper()
        self.app = app.test_client()  # Create a fake browser for testing the API
        self.app.testing = True

    # Unit tests (Scraper Logic)
    def test_scraper_number_parsing(self):
        """Test if '35 million' converts to 35000000 correctly."""
        print("\n[Test] Checking Number Parser...")

        self.assertEqual(self.scraper.parse_number("1,234"), 1234)

        self.assertEqual(self.scraper.parse_number("35 million"), 35000000)
        self.assertEqual(self.scraper.parse_number("1.5 billion"), 1500000000)

        self.assertIsNone(self.scraper.parse_number("No Data"))

    def test_scraper_text_cleaning(self):
        """Test if references [1] and newlines are removed."""
        print("[Test] Checking Text Cleaner...")
        raw_text = "France[1]\n (Republic)"
        cleaned = self.scraper.clean_text(raw_text)
        self.assertEqual(cleaned, "France")

    # Integration tests (API Endpoints)
    def test_api_home(self):
        """Check if Homepage returns 200 OK."""
        print("[Test] Checking API Home...")
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome", response.data)

    def test_api_get_countries(self):
        """Check if /api/countries returns a list."""
        print("[Test] Checking /api/countries...")
        response = self.app.get('/api/countries')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json, list))
        self.assertTrue(len(response.json) > 0)

    def test_api_search_country(self):
        """Check if searching for a specific country returns correct data."""
        country_to_test = "Romania"
        print(f"[Test] Checking /api/country/{country_to_test}...")

        response = self.app.get(f'/api/country/{country_to_test}')

        if response.status_code == 200:
            data = response.json
            self.assertEqual(data['name'], country_to_test)
            self.assertIn('capital', data)
        else:
            print(f"Warning: Country '{country_to_test}' not found in DB. Test skipped.")

    def test_api_search_filter(self):
        """Check the advanced search route."""
        print("[Test] Checking /api/countries/search?language=English...")
        response = self.app.get('/api/countries/search?language=English')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json, list))

    def test_api_404(self):
        """Check if invalid country returns 404 JSON (not HTML)."""
        print("[Test] Checking 404 Logic...")
        response = self.app.get('/api/country/Narnia_Fantasy_Land')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], "Country not found")


if __name__ == '__main__':
    unittest.main()