#!/usr/bin/env python3
"""
Universe MCP - Client Scraper
Scrapes all MCP clients from PulseMCP.com
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin
from tqdm import tqdm

# Configuration
BASE_URL = "https://www.pulsemcp.com"
CLIENTS_URL = f"{BASE_URL}/clients"
DELAY_BETWEEN_REQUESTS = 1.5
MAX_RETRIES = 4
RETRY_DELAYS = [2, 4, 8, 16]

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "clients"
CHECKPOINT_FILE = PROJECT_ROOT / "scripts" / "scrapers" / ".checkpoint_clients.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}


class ClientScraper:
    """Scraper for MCP clients from PulseMCP"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.clients_scraped = 0
        self.checkpoint_data = self.load_checkpoint()

    def load_checkpoint(self) -> Dict:
        """Load checkpoint data if exists"""
        if CHECKPOINT_FILE.exists():
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        return {
            'last_page': 0,
            'clients_scraped': 0,
            'last_run': None
        }

    def save_checkpoint(self, page: int):
        """Save checkpoint data"""
        self.checkpoint_data.update({
            'last_page': page,
            'clients_scraped': self.clients_scraped,
            'last_run': datetime.now().isoformat()
        })
        CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(self.checkpoint_data, f, indent=2)

    def fetch_page(self, url: str, retry_count: int = 0) -> Optional[BeautifulSoup]:
        """Fetch a page with retry logic"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except requests.RequestException as e:
            if retry_count < MAX_RETRIES:
                delay = RETRY_DELAYS[retry_count]
                print(f"  ⚠️  Error: {e}")
                print(f"  🔄 Retrying in {delay}s... (attempt {retry_count + 1}/{MAX_RETRIES})")
                time.sleep(delay)
                return self.fetch_page(url, retry_count + 1)
            else:
                print(f"  ❌ Failed after {MAX_RETRIES} retries: {e}")
                return None

    def extract_client_data(self, card) -> Optional[Dict]:
        """Extract data from a client card element"""
        try:
            href = card.get('href', '')
            if not href or not href.startswith('/clients/'):
                return None

            client_id = href.split('/clients/')[-1]
            url = urljoin(BASE_URL, href)

            # Extract name
            name_elem = card.find('h3')
            name = name_elem.get_text(strip=True) if name_elem else "Unknown"

            # Extract text content
            text_content = card.get_text('\n', strip=True)
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]

            # Extract provider
            provider = None
            if len(lines) > 1:
                for i, line in enumerate(lines):
                    if name in line and i + 1 < len(lines):
                        potential_provider = lines[i + 1]
                        if len(potential_provider) < 100:
                            provider = potential_provider
                            break

            # Extract description
            description = None
            for line in lines:
                if len(line) > 30 and line != name and line != provider:
                    description = line
                    break

            client_data = {
                'id': client_id,
                'name': name,
                'provider': provider,
                'description': description,
                'url': url,
                'source_url': None,
                'platforms': [],
                'categories': [],
                'scraped_at': datetime.now().isoformat()
            }

            return client_data

        except Exception as e:
            print(f"  ❌ Error parsing client card: {e}")
            return None

    def save_client(self, client_data: Dict):
        """Save client data to JSON file"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        file_path = DATA_DIR / f"{client_data['id']}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(client_data, f, indent=2, ensure_ascii=False)

    def scrape_page(self, page: int) -> List[Dict]:
        """Scrape a single page of clients"""
        url = f"{CLIENTS_URL}?page={page}" if page > 1 else CLIENTS_URL
        print(f"\n📄 Scraping page {page}: {url}")

        soup = self.fetch_page(url)
        if not soup:
            return []

        client_cards = soup.find_all('a', href=re.compile(r'^/clients/[^/]+$'))

        clients = []
        for card in client_cards:
            client_data = self.extract_client_data(card)
            if client_data:
                clients.append(client_data)
                self.save_client(client_data)
                self.clients_scraped += 1

        print(f"  ✅ Found {len(clients)} clients on page {page}")
        return clients

    def get_total_pages(self) -> int:
        """Get total number of pages"""
        print("🔍 Fetching first page to determine total pages...")
        soup = self.fetch_page(CLIENTS_URL)
        if not soup:
            return 1

        # Look for pagination
        page_links = soup.find_all('a', href=re.compile(r'\?page=\d+'))
        if page_links:
            page_numbers = []
            for link in page_links:
                match = re.search(r'page=(\d+)', link.get('href', ''))
                if match:
                    page_numbers.append(int(match.group(1)))
            if page_numbers:
                total_pages = max(page_numbers)
                print(f"  📄 Found {total_pages} total pages")
                return total_pages

        print("  📄 Only 1 page found or could not determine pagination")
        return 1

    def run(self, start_page: int = 1, end_page: Optional[int] = None, resume: bool = False):
        """Run the scraper"""
        print("=" * 80)
        print("🌌 UNIVERSE MCP - Client Scraper")
        print("=" * 80)

        total_pages = self.get_total_pages()
        if end_page is None:
            end_page = total_pages

        if resume and self.checkpoint_data['last_page'] > 0:
            start_page = self.checkpoint_data['last_page'] + 1
            self.clients_scraped = self.checkpoint_data['clients_scraped']
            print(f"\n🔄 Resuming from checkpoint (page {self.checkpoint_data['last_page']})")

        print(f"\n🎯 Scraping pages {start_page} to {end_page}\n")

        for page in tqdm(range(start_page, end_page + 1), desc="Pages"):
            self.scrape_page(page)
            self.save_checkpoint(page)
            if page < end_page:
                time.sleep(DELAY_BETWEEN_REQUESTS)

        print("\n" + "=" * 80)
        print(f"✅ Scraping completed! Total clients: {self.clients_scraped}")
        print(f"📁 Data saved to: {DATA_DIR}")
        print("=" * 80)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scrape MCP clients from PulseMCP')
    parser.add_argument('--start', type=int, default=1, help='Start page')
    parser.add_argument('--end', type=int, default=None, help='End page')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--test', action='store_true', help='Test mode: scrape only first page')

    args = parser.parse_args()

    scraper = ClientScraper()
    if args.test:
        print("🧪 TEST MODE: Scraping only first page")
        scraper.run(start_page=1, end_page=1, resume=False)
    else:
        scraper.run(start_page=args.start, end_page=args.end, resume=args.resume)


if __name__ == '__main__':
    main()
