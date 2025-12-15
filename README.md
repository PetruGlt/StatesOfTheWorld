# 🌍 States of the World API

The Python Project "States of the World" is a comprehensive solution that scrapes, processes, and serves detailed information about countries worldwide. It features a custom web scraper, a normalized SQLite database, and a robust Flask-based REST API with interactive Swagger documentation.

## 🚀 Features

* **Web Scraper:** Custom-built crawler using `BeautifulSoup` to extract Population, Area, Density, Government type, Timezones, Languages, and Neighbors.
* **Data Cleaning:** Robust parsing logic to handle inconsistent data formats (e.g., converting "35 million" to integers, cleaning footnotes like `[1]`).
* **Relational Database:** Normalized SQLite architecture with tables for `countries`, `languages`, and `borders`.
* **REST API:** Fast Flask-based API supporting filtering, searching, and sorting.
* **Interactive Documentation:** Integrated **Swagger UI** for testing endpoints directly in the browser.
* **Performance:** Optimized with database indexes for sub-millisecond query responses.
* **Reliability:** Includes automated Unit Tests, Integration Tests, and Request Logging.

---

## 📂 Project Structure

```text
StatesOfTheWorld/
├── static/
│   └── swagger.json        # Open API specification for Swagger UI
├── venv/                   # Virtual Environment (excluded from git)
├── app.py                  # The Flask API Server (Main Entry Point)
├── crawler.py              # The Web Scraper (Phase 1)
├── database_manager.py     # Database creation & insertion logic (Phase 2) + Indexing (Phase 5)
├── tests.py                # Automated Test Suite (Phase 6)
├── validator.py            # Data Integrity Reporter (Phase 4)
├── requirements.txt        # Project dependencies
└── README.md               # Project Documentation