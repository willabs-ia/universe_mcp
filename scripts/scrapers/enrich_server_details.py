#!/usr/bin/env python3
"""
Universe MCP - Server Detail Enrichment
Visits individual server pages to extract complete metadata
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import re
from urllib.parse import urljoin

# Configuration
BASE_URL = "https://www.pulsemcp.com"
DELAY_BETWEEN_REQUESTS = 2.0  # Be more conservative for detail pages
MAX_RETRIES = 4
RETRY_DELAYS = [2, 4, 8, 16]

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "servers"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}


class ServerDetailEnricher:
    """Enriches server data by visiting individual pages"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.enriched_count = 0
        self.failed_count = 0

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
                print(f"  🔄 Retrying in {delay}s...")
                time.sleep(delay)
                return self.fetch_page(url, retry_count + 1)
            else:
                print(f"  ❌ Failed after {MAX_RETRIES} retries")
                return None

    def extract_detail_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract detailed information from server detail page"""
        details = {}

        try:
            # Extract full description (usually in a main content area)
            description_elem = soup.find('div', class_=re.compile(r'description|content|detail'))
            if description_elem:
                details['description_full'] = description_elem.get_text(strip=True)

            # Extract GitHub/Source URL
            github_link = soup.find('a', href=re.compile(r'github\.com'))
            if github_link:
                details['source_url'] = github_link.get('href')

            # Extract tags/categories (look for tag elements)
            tags = []
            tag_elements = soup.find_all(['span', 'a'], class_=re.compile(r'tag|category|label'))
            for tag_elem in tag_elements:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and len(tag_text) < 50:  # Reasonable tag length
                    tags.append(tag_text)
            if tags:
                details['tags'] = list(set(tags))  # Remove duplicates

            # Extract categories from breadcrumbs or navigation
            categories = []
            breadcrumb = soup.find(['nav', 'ol', 'ul'], class_=re.compile(r'breadcrumb|nav'))
            if breadcrumb:
                for item in breadcrumb.find_all(['a', 'span']):
                    cat_text = item.get_text(strip=True)
                    if cat_text and cat_text not in ['Home', 'Servers', 'Back']:
                        categories.append(cat_text)
            if categories:
                details['categories'] = categories

            # Extract author/maintainer
            author_elem = soup.find(['span', 'div', 'a'], class_=re.compile(r'author|maintainer|creator'))
            if author_elem:
                details['author'] = author_elem.get_text(strip=True)

            # Extract license information
            license_elem = soup.find(['span', 'div'], text=re.compile(r'license', re.I))
            if license_elem:
                license_text = license_elem.get_text(strip=True)
                details['license'] = license_text

            # Extract version if available
            version_elem = soup.find(['span', 'div'], class_=re.compile(r'version'))
            if version_elem:
                details['version'] = version_elem.get_text(strip=True)

            # Extract documentation URL
            doc_link = soup.find('a', text=re.compile(r'documentation|docs|guide', re.I))
            if doc_link:
                details['documentation_url'] = urljoin(BASE_URL, doc_link.get('href', ''))

            # Extract README or detailed info
            readme_elem = soup.find(['div', 'section'], class_=re.compile(r'readme|markdown'))
            if readme_elem:
                details['readme'] = readme_elem.get_text(strip=True)[:1000]  # First 1000 chars

            # Extract installation instructions
            install_elem = soup.find(['code', 'pre'], text=re.compile(r'npm|pip|install'))
            if install_elem:
                details['installation'] = install_elem.get_text(strip=True)

            # Extract last updated timestamp
            updated_elem = soup.find(['time', 'span'], class_=re.compile(r'updated|modified'))
            if updated_elem:
                details['last_updated'] = updated_elem.get('datetime') or updated_elem.get_text(strip=True)

        except Exception as e:
            print(f"  ⚠️  Error extracting details: {e}")

        return details

    def enrich_server(self, server_file: Path) -> bool:
        """Enrich a single server with detail page data"""
        try:
            # Load existing server data
            with open(server_file, 'r', encoding='utf-8') as f:
                server_data = json.load(f)

            # Skip if already enriched recently (within 7 days)
            if server_data.get('enriched_at'):
                enriched_date = datetime.fromisoformat(server_data['enriched_at'])
                days_since = (datetime.now() - enriched_date).days
                if days_since < 7:
                    print(f"  ⏭️  Skipping (enriched {days_since} days ago)")
                    return True

            server_url = server_data.get('url')
            if not server_url:
                print(f"  ⚠️  No URL found for {server_data.get('name')}")
                return False

            print(f"\n📄 Enriching: {server_data.get('name')}")
            print(f"   URL: {server_url}")

            # Fetch detail page
            soup = self.fetch_page(server_url)
            if not soup:
                self.failed_count += 1
                return False

            # Extract details
            details = self.extract_detail_data(soup, server_url)

            # Merge with existing data (don't overwrite existing good data)
            if details.get('description_full') and len(details['description_full']) > len(server_data.get('description', '')):
                server_data['description'] = details['description_full']

            if details.get('source_url') and not server_data.get('source_url'):
                server_data['source_url'] = details['source_url']

            if details.get('tags'):
                existing_tags = set(server_data.get('tags', []))
                existing_tags.update(details['tags'])
                server_data['tags'] = list(existing_tags)

            if details.get('categories'):
                existing_cats = set(server_data.get('categories', []))
                existing_cats.update(details['categories'])
                server_data['categories'] = list(existing_cats)

            # Add metadata
            if 'metadata' not in server_data:
                server_data['metadata'] = {}

            for key in ['author', 'license', 'version', 'documentation_url', 'readme', 'installation']:
                if details.get(key):
                    server_data['metadata'][key] = details[key]

            if details.get('last_updated'):
                server_data['last_updated'] = details['last_updated']

            # Mark as enriched
            server_data['enriched_at'] = datetime.now().isoformat()

            # Save updated data
            with open(server_file, 'w', encoding='utf-8') as f:
                json.dump(server_data, f, indent=2, ensure_ascii=False)

            self.enriched_count += 1
            print(f"  ✅ Enriched successfully")
            return True

        except Exception as e:
            print(f"  ❌ Error enriching server: {e}")
            self.failed_count += 1
            return False

    def run(self, classification: Optional[str] = None, limit: Optional[int] = None):
        """Run enrichment on servers"""
        print("=" * 80)
        print("🔍 UNIVERSE MCP - Server Detail Enrichment")
        print("=" * 80)

        # Get all server files
        if classification:
            server_files = list((DATA_DIR / classification).glob("*.json"))
        else:
            server_files = []
            for subdir in ['official', 'reference', 'community']:
                server_files.extend((DATA_DIR / subdir).glob("*.json"))

        if limit:
            server_files = server_files[:limit]

        total = len(server_files)
        print(f"\n📊 Found {total} servers to process")
        print(f"⏱️  Estimated time: ~{total * (DELAY_BETWEEN_REQUESTS + 2):.0f}s")
        print()

        for i, server_file in enumerate(server_files, 1):
            print(f"[{i}/{total}]", end=" ")
            self.enrich_server(server_file)

            # Delay between requests
            if i < total:
                time.sleep(DELAY_BETWEEN_REQUESTS)

        print("\n" + "=" * 80)
        print("📊 ENRICHMENT SUMMARY")
        print("=" * 80)
        print(f"✅ Successfully enriched: {self.enriched_count}")
        print(f"❌ Failed: {self.failed_count}")
        print(f"📁 Total processed: {total}")
        print("=" * 80)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Enrich MCP server data with details')
    parser.add_argument('--classification', choices=['official', 'reference', 'community'],
                        help='Enrich only servers of specific classification')
    parser.add_argument('--limit', type=int, help='Limit number of servers to enrich (for testing)')
    parser.add_argument('--test', action='store_true', help='Test mode: enrich only 3 servers')

    args = parser.parse_args()

    enricher = ServerDetailEnricher()

    if args.test:
        print("🧪 TEST MODE: Enriching only 3 servers")
        enricher.run(classification=args.classification, limit=3)
    else:
        enricher.run(classification=args.classification, limit=args.limit)


if __name__ == '__main__':
    main()
