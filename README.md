# 🌍 States of the World API

The Python Project "States of the World" is a comprehensive solution that scrapes, processes, and serves detailed information about countries worldwide. It features a custom web scraper, a normalized SQLite database, and a robust Flask-based REST API with interactive Swagger documentation.

## 🕷️ Features

* **Web Scraper:** Custom-built crawler using `BeautifulSoup` to extract Population, Area, Density, Government type, Timezones, Languages, and Neighbors.
* **Data Cleaning:** Robust parsing logic to handle inconsistent data formats (e.g., converting "35 million" to integers, cleaning footnotes like `[1]`).
* **Relational Database:** Normalized SQLite architecture with tables for `countries`, `languages`, and `borders`.
* **REST API:** Fast Flask-based API supporting filtering, searching, and sorting.
* **Interactive Documentation:** Integrated **Swagger UI** for testing endpoints directly in the browser.
* **Performance:** Optimized with database indexes for sub-millisecond query responses.
* **Reliability:** Includes automated Unit Tests, Integration Tests, and Request Logging.

---

## 🚀 How to Run the Project
### 1. Clone the Repository

```bash
git clone https://github.com/PetruGlt/StatesOfTheWorld
cd StatesOfTheWorld
```

### 2. Set Up a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Web Scraper

```bash
python crawler.py
```
This will create and populate the SQLite database with the scraped data.

### 5. Database Creation

```bash
python database_manager.py
```
This will set up the database schema and insert the scraped data into the appropriate tables.

### 6. Data Integrity Check

```bash
python validator.py
```
This will run data integrity checks and generate a report on any inconsistencies found.

### 7. Start the Flask API Server

```bash
python app.py
```
The API server will start on `http://127.0.0.1:5000`

### 8. Access Swagger UI
Open your web browser and navigate to `http://127.0.0.1:5000/swagger` to explore and test the API endpoints interactively.

## 🧪 Testing
The project includes a suite of automated tests to verify the scraper logic and API endpoints.

To run the tests, execute:

```bash
python tests.py
```

## 🛠️ Technologies Used
* Python 3.x
* Flask
* BeautifulSoup
* SQLite
* Swagger UI
* unittest
* requests
* logging

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