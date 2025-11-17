#!/usr/bin/env python3
"""
Universe MCP - Use Cases Scraper
Scrapes all use cases from PulseMCP.com
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
USECASES_URL = f"{BASE_URL}/use-cases"
DELAY_BETWEEN_REQUESTS = 1.5
MAX_RETRIES = 4
RETRY_DELAYS = [2, 4, 8, 16]

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "use-cases"
CHECKPOINT_FILE = PROJECT_ROOT / "scripts" / "scrapers" / ".checkpoint_usecases.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}


class UseCaseScraper:
    """Scraper for MCP use cases from PulseMCP"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.usecases_scraped = 0
        self.checkpoint_data = self.load_checkpoint()

    def load_checkpoint(self) -> Dict:
        """Load checkpoint data if exists"""
        if CHECKPOINT_FILE.exists():
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        return {
            'last_page': 0,
            'usecases_scraped': 0,
            'last_run': None
        }

    def save_checkpoint(self, page: int):
        """Save checkpoint data"""
        self.checkpoint_data.update({
            'last_page': page,
            'usecases_scraped': self.usecases_scraped,
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

    def extract_usecase_data(self, card) -> Optional[Dict]:
        """Extract data from a use case card element"""
        try:
            href = card.get('href', '')
            if not href or not href.startswith('/use-cases/'):
                return None

            usecase_id = href.split('/use-cases/')[-1]
            url = urljoin(BASE_URL, href)

            # Extract title
            title_elem = card.find('h3')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"

            # Extract description
            text_content = card.get_text('\n', strip=True)
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]

            description = None
            for line in lines:
                if len(line) > 30 and line != title:
                    description = line
                    break

            usecase_data = {
                'id': usecase_id,
                'title': title,
                'description': description,
                'url': url,
                'servers_used': [],
                'clients_used': [],
                'categories': [],
                'scraped_at': datetime.now().isoformat()
            }

            return usecase_data

        except Exception as e:
            print(f"  ❌ Error parsing use case card: {e}")
            return None

    def save_usecase(self, usecase_data: Dict):
        """Save use case data to JSON file"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        file_path = DATA_DIR / f"{usecase_data['id']}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(usecase_data, f, indent=2, ensure_ascii=False)

    def scrape_page(self, page: int) -> List[Dict]:
        """Scrape a single page of use cases"""
        url = f"{USECASES_URL}?page={page}" if page > 1 else USECASES_URL
        print(f"\n📄 Scraping page {page}: {url}")

        soup = self.fetch_page(url)
        if not soup:
            return []

        usecase_cards = soup.find_all('a', href=re.compile(r'^/use-cases/[^/]+$'))

        usecases = []
        for card in usecase_cards:
            usecase_data = self.extract_usecase_data(card)
            if usecase_data:
                usecases.append(usecase_data)
                self.save_usecase(usecase_data)
                self.usecases_scraped += 1

        print(f"  ✅ Found {len(usecases)} use cases on page {page}")
        return usecases

    def get_total_pages(self) -> int:
        """Get total number of pages"""
        print("🔍 Fetching first page to determine total pages...")
        soup = self.fetch_page(USECASES_URL)
        if not soup:
            return 1

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
        print("🌌 UNIVERSE MCP - Use Case Scraper")
        print("=" * 80)

        total_pages = self.get_total_pages()
        if end_page is None:
            end_page = total_pages

        if resume and self.checkpoint_data['last_page'] > 0:
            start_page = self.checkpoint_data['last_page'] + 1
            self.usecases_scraped = self.checkpoint_data['usecases_scraped']
            print(f"\n🔄 Resuming from checkpoint (page {self.checkpoint_data['last_page']})")

        print(f"\n🎯 Scraping pages {start_page} to {end_page}\n")

        for page in tqdm(range(start_page, end_page + 1), desc="Pages"):
            self.scrape_page(page)
            self.save_checkpoint(page)
            if page < end_page:
                time.sleep(DELAY_BETWEEN_REQUESTS)

        print("\n" + "=" * 80)
        print(f"✅ Scraping completed! Total use cases: {self.usecases_scraped}")
        print(f"📁 Data saved to: {DATA_DIR}")
        print("=" * 80)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scrape MCP use cases from PulseMCP')
    parser.add_argument('--start', type=int, default=1, help='Start page')
    parser.add_argument('--end', type=int, default=None, help='End page')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--test', action='store_true', help='Test mode: scrape only first page')

    args = parser.parse_args()

    scraper = UseCaseScraper()
    if args.test:
        print("🧪 TEST MODE: Scraping only first page")
        scraper.run(start_page=1, end_page=1, resume=False)
    else:
        scraper.run(start_page=args.start, end_page=args.end, resume=args.resume)


if __name__ == '__main__':
    main()
