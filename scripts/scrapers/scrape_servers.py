#!/usr/bin/env python3
"""
Universe MCP - Server Scraper
Scrapes all MCP servers from PulseMCP.com
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import sys
from tqdm import tqdm

# Configuration
BASE_URL = "https://www.pulsemcp.com"
SERVERS_URL = f"{BASE_URL}/servers"
DELAY_BETWEEN_REQUESTS = 1.5  # seconds
MAX_RETRIES = 4
RETRY_DELAYS = [2, 4, 8, 16]  # exponential backoff

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "servers"
CHECKPOINT_FILE = PROJECT_ROOT / "scripts" / "scrapers" / ".checkpoint_servers.json"

# User agent to avoid blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


class ServerScraper:
    """Scraper for MCP servers from PulseMCP"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.servers_scraped = 0
        self.checkpoint_data = self.load_checkpoint()

    def load_checkpoint(self) -> Dict:
        """Load checkpoint data if exists"""
        if CHECKPOINT_FILE.exists():
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        return {
            'last_page': 0,
            'servers_scraped': 0,
            'last_run': None
        }

    def save_checkpoint(self, page: int):
        """Save checkpoint data"""
        self.checkpoint_data.update({
            'last_page': page,
            'servers_scraped': self.servers_scraped,
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
                print(f"  ⚠️  Error fetching {url}: {e}")
                print(f"  🔄 Retrying in {delay}s... (attempt {retry_count + 1}/{MAX_RETRIES})")
                time.sleep(delay)
                return self.fetch_page(url, retry_count + 1)
            else:
                print(f"  ❌ Failed to fetch {url} after {MAX_RETRIES} retries: {e}")
                return None

    def extract_server_data(self, card) -> Optional[Dict]:
        """Extract data from a server card element"""
        try:
            # Get the link and slug
            href = card.get('href', '')
            if not href or not href.startswith('/servers/'):
                return None

            server_id = href.split('/servers/')[-1]
            url = urljoin(BASE_URL, href)

            # Extract name (h3 tag)
            name_elem = card.find('h3')
            name = name_elem.get_text(strip=True) if name_elem else "Unknown"

            # Extract all text content
            text_content = card.get_text('\n', strip=True)
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]

            # Try to parse provider (usually second line after name)
            provider = None
            if len(lines) > 1:
                # Provider is usually the line after the name
                for i, line in enumerate(lines):
                    if name in line and i + 1 < len(lines):
                        potential_provider = lines[i + 1]
                        # Avoid classification badges and metrics
                        if not any(keyword in potential_provider.lower() for keyword in ['official', 'reference', 'community', 'est ', 'downloads', 'visitors']):
                            provider = potential_provider
                            break

            # Extract description (longest text that's not name/provider/metrics)
            description = None
            for line in lines:
                if (len(line) > 30 and
                    line != name and
                    line != provider and
                    'est ' not in line.lower() and
                    not re.match(r'^\d{4}', line)):  # not a date
                    description = line
                    break

            # Extract classification
            classification = None
            for line in lines:
                line_lower = line.lower()
                if 'official' in line_lower:
                    classification = 'official'
                    break
                elif 'reference' in line_lower:
                    classification = 'reference'
                    break
                elif 'community' in line_lower:
                    classification = 'community'
                    break

            # Extract metrics
            weekly_metric = None
            for line in lines:
                if 'est downloads' in line.lower():
                    match = re.search(r'([\d,]+)\s*est downloads', line, re.IGNORECASE)
                    if match:
                        weekly_metric = {
                            'type': 'downloads',
                            'value': int(match.group(1).replace(',', ''))
                        }
                    break
                elif 'est visitors' in line.lower():
                    match = re.search(r'([\d,]+)\s*est visitors', line, re.IGNORECASE)
                    if match:
                        weekly_metric = {
                            'type': 'visitors',
                            'value': int(match.group(1).replace(',', ''))
                        }
                    break

            # Extract release date
            release_date = None
            for line in lines:
                # Look for date pattern YYYY-MM-DD or "Month DD, YYYY"
                date_match = re.search(r'\b(\d{4})-(\d{2})-(\d{2})\b', line)
                if date_match:
                    release_date = date_match.group(0)
                    break

            # Build server object
            server_data = {
                'id': server_id,
                'name': name,
                'provider': provider,
                'description': description,
                'classification': classification,
                'weekly_metric': weekly_metric,
                'release_date': release_date,
                'url': url,
                'source_url': None,  # Will need to visit detail page for this
                'categories': [],
                'tags': [],
                'last_updated': None,
                'scraped_at': datetime.now().isoformat(),
                'metadata': {}
            }

            return server_data

        except Exception as e:
            print(f"  ❌ Error parsing server card: {e}")
            return None

    def save_server(self, server_data: Dict):
        """Save server data to JSON file"""
        # Determine subdirectory based on classification
        classification = server_data.get('classification', 'community')
        if classification not in ['official', 'reference', 'community']:
            classification = 'community'

        server_dir = DATA_DIR / classification
        server_dir.mkdir(parents=True, exist_ok=True)

        # Save to file
        file_path = server_dir / f"{server_data['id']}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(server_data, f, indent=2, ensure_ascii=False)

    def scrape_page(self, page: int) -> List[Dict]:
        """Scrape a single page of servers"""
        url = f"{SERVERS_URL}?page={page}"
        print(f"\n📄 Scraping page {page}: {url}")

        soup = self.fetch_page(url)
        if not soup:
            return []

        # Find all server cards (links to /servers/...)
        server_cards = soup.find_all('a', href=re.compile(r'^/servers/[^/]+$'))

        servers = []
        for card in server_cards:
            server_data = self.extract_server_data(card)
            if server_data:
                servers.append(server_data)
                self.save_server(server_data)
                self.servers_scraped += 1

        print(f"  ✅ Found {len(servers)} servers on page {page}")
        return servers

    def get_total_pages(self) -> int:
        """Get total number of pages"""
        print("🔍 Fetching first page to determine total pages...")
        soup = self.fetch_page(SERVERS_URL)
        if not soup:
            print("  ❌ Could not fetch first page")
            return 0

        # Look for pagination info or last page number
        # Try to find text like "1 - 42 of 6488 servers"
        text_content = soup.get_text()
        match = re.search(r'of\s+([\d,]+)\s+servers', text_content, re.IGNORECASE)
        if match:
            total_servers = int(match.group(1).replace(',', ''))
            servers_per_page = 42  # Known from analysis
            total_pages = (total_servers + servers_per_page - 1) // servers_per_page
            print(f"  📊 Found {total_servers:,} total servers")
            print(f"  📄 Calculated {total_pages} total pages")
            return total_pages

        # Fallback: look for last page link
        page_links = soup.find_all('a', href=re.compile(r'\?page=\d+'))
        if page_links:
            page_numbers = []
            for link in page_links:
                match = re.search(r'page=(\d+)', link.get('href', ''))
                if match:
                    page_numbers.append(int(match.group(1)))
            if page_numbers:
                total_pages = max(page_numbers)
                print(f"  📄 Found {total_pages} total pages from pagination links")
                return total_pages

        print("  ⚠️  Could not determine total pages, defaulting to 155")
        return 155  # Fallback based on previous analysis

    def run(self, start_page: int = 1, end_page: Optional[int] = None, resume: bool = False):
        """Run the scraper"""
        print("=" * 80)
        print("🌌 UNIVERSE MCP - Server Scraper")
        print("=" * 80)

        # Get total pages
        total_pages = self.get_total_pages()
        if total_pages == 0:
            print("❌ Could not determine total pages. Exiting.")
            return

        if end_page is None:
            end_page = total_pages

        # Resume from checkpoint if requested
        if resume and self.checkpoint_data['last_page'] > 0:
            start_page = self.checkpoint_data['last_page'] + 1
            self.servers_scraped = self.checkpoint_data['servers_scraped']
            print(f"\n🔄 Resuming from checkpoint:")
            print(f"   Last page completed: {self.checkpoint_data['last_page']}")
            print(f"   Servers already scraped: {self.servers_scraped}")

        print(f"\n🎯 Scraping pages {start_page} to {end_page}")
        print(f"⏱️  Delay between requests: {DELAY_BETWEEN_REQUESTS}s")
        print()

        # Scrape all pages
        for page in tqdm(range(start_page, end_page + 1), desc="Pages"):
            self.scrape_page(page)
            self.save_checkpoint(page)

            # Delay between requests (except for last page)
            if page < end_page:
                time.sleep(DELAY_BETWEEN_REQUESTS)

        print("\n" + "=" * 80)
        print(f"✅ Scraping completed!")
        print(f"📊 Total servers scraped: {self.servers_scraped}")
        print(f"📁 Data saved to: {DATA_DIR}")
        print("=" * 80)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape MCP servers from PulseMCP')
    parser.add_argument('--start', type=int, default=1, help='Start page (default: 1)')
    parser.add_argument('--end', type=int, default=None, help='End page (default: auto-detect)')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    parser.add_argument('--test', action='store_true', help='Test mode: scrape only first 2 pages')

    args = parser.parse_args()

    scraper = ServerScraper()

    if args.test:
        print("🧪 TEST MODE: Scraping only first 2 pages")
        scraper.run(start_page=1, end_page=2, resume=False)
    else:
        scraper.run(start_page=args.start, end_page=args.end, resume=args.resume)


if __name__ == '__main__':
    main()
