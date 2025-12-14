
import requests
from bs4 import BeautifulSoup
import re
import json


class CountryScraper:
    def __init__(self):
        self.base_url = "https://en.wikipedia.org"
        self.headers = {'User-Agent': 'StatesOfTheWorldAgent/1.0 (student_project_fii)'}

        self.neighbors_map = {}

    def clean_text(self, text):
        if not text:
            return None
        # Remove references
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        # Fix: Replace newlines with space to handle "List\nUTC+1"
        text = text.replace('\n', ' ')
        # Fix: Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def parse_number(self, text):
        if not text: return None

        text_lower = text.lower()
        multiplier = 1
        if 'billion' in text_lower:
            multiplier = 1_000_000_000
        elif 'million' in text_lower:
            multiplier = 1_000_000
        elif 'trillion' in text_lower:
            multiplier = 1_000_000_000_000

        clean_str = self.clean_text(text)

        match = re.search(r'(\d+(\.\d+)?)', clean_str.replace(",", ""))

        if match:
            try:
                # Get the raw number (e.g., 3.5)
                val_float = float(match.group(1))
                # Apply multiplier (3.5 * 1,000,000)
                return int(val_float * multiplier)
            except ValueError:
                return None
        return None

    def parse_float(self, text):
        if not text: return None
        clean_str = self.clean_text(text)

        match = re.search(r'\d+(\.\d+)?', clean_str.replace(",", ""))
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
        return None

    def parse_languages(self, td):
        if not td: return None

        for sup in td.find_all('sup'):
            sup.decompose()

        text = td.get_text(separator='|')

        excluded_words = ['List', 'List:', '(de facto)', 'None', 'Languages', 'Official', 'locally', ';', '[hide]']

        langs = []
        for item in text.split('|'):

            clean_item = item.replace(';', '').replace(':', '').strip()


            if (len(clean_item) > 2 and
                    clean_item not in excluded_words and
                    "List" not in clean_item and
                    "locally" not in clean_item and
                    not clean_item[0].isdigit()):

                langs.append(clean_item)

        return ", ".join(list(set(langs)))

    def build_neighbors_map(self):
        """
        Scraping for 'List_of_countries_and_territories_by_number_of_land_borders'
        and construct a dictionary {Country_name: [List_of_neighbors]}.
        """

        url = "/wiki/List_of_countries_and_territories_by_number_of_land_borders"
        full_url = self.base_url + url
        print(f"Build neighbors map from: {full_url}")

        try:
            response = requests.get(full_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # The sortable table
            table = soup.find('table', {'class': 'wikitable'})
            if not table:
                print("Can't find the sortable table.")
                return

            rows = table.find_all('tr')
            print(f"Rows founded in the neighbors table: {len(rows)}")

            for tr in rows[1:]:  # Skip the header
                # Wikipedia stores the name of the country in table_header and sometimes in table_data
                cells = tr.find_all(['td', 'th'])

                # Need at least 2 colls (name and neighbors)
                if not cells or len(cells) < 4:
                    continue

                # Extract the name of the state (first cell)
                country_link = cells[0].find('a')
                if not country_link:
                    continue
                country_name = self.clean_text(country_link.get_text())

                # Extract the neighbors (last cell)
                neighbors_cell = cells[-1]

                neighbor_links = neighbors_cell.find_all('a')
                neighbors_list = []

                # ignored = ["citation needed", "note", "[", "]", "north", "south", "east", "west"]

                for link in neighbor_links:
                    n_name = link.get_text().strip()
                    n_href = link.get('href', '')

                    # Validations
                    if (n_name and
                            len(n_name) > 2 and
                            "/wiki/" in n_href and
                            not n_name.startswith('[')):
                            # and not any(x in n_name.lower() for x in ignored)):
                        neighbors_list.append(n_name)

                # Delete duplicates
                self.neighbors_map[country_name] = list(set(neighbors_list))

            print(f"Neighbors map successfully built: {len(self.neighbors_map)} countries.")
            # print(self.neighbors_map)

        except Exception as e:
            print(f"Error creating the neighbors map: {e}")

    def get_country_data(self, country_url):
        full_url = self.base_url + country_url
        print(f"Scraping: {full_url}")  # Debug print

        try:
            response = requests.get(full_url, headers=self.headers, timeout=10)
        except Exception as e:
            print(f"Connection error: {e}")
            return None

        if response.status_code != 200:
            print(f"Error status code {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        infobox = soup.find('table', {'class': 'infobox'})
        if not infobox:
            print("Infobox not found")
            return None

        data = {
            "name": "",
            "capital": None,
            "population": None,
            "area_in_km2": None,
            "density": None,
            "neighbors": [],
            "language": None,
            "timezone": None,
            "political_system": None
        }

        fn_org = infobox.find('div', {'class': 'fn org'})
        if fn_org:
            data['name'] = self.clean_text(fn_org.get_text())
        else:
            h1 = soup.find('h1')
            if h1:
                data['name'] = self.clean_text(h1.get_text())

        if not data['name']:
            print(f"SKIPPING: Couldn't idetinfy the name for {country_url}")
            return None

        if data['name'] in self.neighbors_map:
            data['neighbors'] = self.neighbors_map[data['name']]
        else:
            # Fuzzy search
            for k in self.neighbors_map:
                if k and (data['name'] in k or k in data['name']):
                    data['neighbors'] = self.neighbors_map[k]
                    break

        rows = infobox.find_all('tr')
        for tr in rows:
            th = tr.find('th')
            td = tr.find('td')
            if not th or not td: continue

            header_clean = re.sub(r'[^a-z]', '', th.get_text().lower())

            # --- CAPITAL ---
            if "capital" in header_clean:
                if td.find('a'):
                    data['capital'] = td.find('a').get_text()
                else:
                    data['capital'] = self.clean_text(td.get_text().split(';')[0])

            # --- POLITICAL SYSTEM ---
            if "government" in header_clean and "transitional" not in header_clean:
                if data['political_system'] is None:
                    links = td.find_all('a')
                    # Filter out references [1] and citations
                    valid_links = [
                        a.get_text() for a in links
                        if not a.get_text().startswith('[') and not a.get_text()[0].isdigit()
                    ]

                    if valid_links:
                        data['political_system'] = ", ".join(valid_links)
                    else:
                        text = self.clean_text(td.get_text())
                        # Double check: don't save if it looks like a date (starts with digit)
                        if text and not text[0].isdigit():
                            data['political_system'] = text

            # --- POPULATION ---
            if "population" in header_clean or "estimate" in header_clean or "census" in header_clean:
                if data['population'] is None:
                    data['population'] = self.parse_number(td.get_text())

            # --- DENSITY ---
            if "density" in header_clean:
                data['density'] = self.parse_float(td.get_text())

            # --- AREA ---
            is_area = "area" in header_clean
            is_total_km = "total" in header_clean and "km" in td.get_text().lower()

            if (is_area or is_total_km) and data['area_in_km2'] is None:
                data['area_in_km2'] = self.parse_number(td.get_text())

            # --- LANGUAGE ---
            if "officiallanguage" in header_clean or "officialandnational" in header_clean or "nationallanguage" in header_clean:
                data['language'] = self.parse_languages(td)

            # --- TIMEZONE ---
            if "timezone" in header_clean:
                raw_text = td.get_text()
                cleaned_tz = re.split(r'[\[\(]', raw_text)[0]

                data['timezone'] = self.clean_text(cleaned_tz)

            if data['density'] is None:
                if data['population'] is not None and data['area_in_km2'] is not None:
                    # Ensure we don't divide by zero
                    if data['area_in_km2'] > 0:
                        calculated_density = data['population'] / data['area_in_km2']
                        # Round to 1 decimal place (e.g., 54.4)
                        data['density'] = float(f"{calculated_density:.1f}")

            if data['area_in_km2'] is None:
                if data['population'] is not None and data['density'] is not None:
                    if data['density'] > 0:
                        val = data['population'] / data['density']
                        # Area is usually an integer, so we round it
                        data['area_in_km2'] = int(val)
        return data

    def get_all_country_links(self):
        """
        Acces the list of all states and return their urls.
        """
        list_url = "/wiki/List_of_sovereign_states"
        full_url = self.base_url + list_url
        print(f"Accessing the main list: {full_url}")

        try:
            response = requests.get(full_url, headers=self.headers, timeout=15)
        except Exception as e:
            print(f"Critical error: list of states: {e}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')

        # Finding all tables of type wikitables
        tables = soup.find_all('table', {'class': 'wikitable'})
        target_table = None

        for t in tables:
            headers = t.get_text()
            if "Common and formal names" in headers and "Membership within the UN" in headers:
                target_table = t
                break

        if not target_table:
            print("Critical Error: Can't identify the tables with the states")
            return []

        country_links = []

        rows = target_table.find_all('tr')

        for tr in rows:
            td = tr.find('td')
            if not td:
                continue

            links = td.find_all('a')
            for link in links:
                href = link.get('href')
                title = link.get('title')

                # Filtering
                if (href and
                        href.startswith("/wiki/") and
                        "File:" not in href and
                        "cite_note" not in href and
                        "Help:" not in href):
                    country_links.append(href)
                    break

        print(f"{len(country_links)} states found.")
        return country_links


if __name__ == "__main__":
    scraper = CountryScraper()

    print("Creating the neighbors map...")
    scraper.build_neighbors_map()

    print("\nGetting all countries links for wikipedia...")
    links = scraper.get_all_country_links()

    all_data = []

    print(f"\nScraping {len(links)} countries...")

    for i, link in enumerate(links):
        print(f"[{i + 1}/{len(links)}] {link}")

        c_data = scraper.get_country_data(link)
        if c_data and c_data['name']:
            all_data.append(c_data)

    with open('states_final.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

    print("Finished!")