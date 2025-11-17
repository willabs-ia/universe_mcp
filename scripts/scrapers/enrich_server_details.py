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
            # Extract GitHub/Source URL - more specific search for GitHub icon link
            github_link = soup.find('a', href=re.compile(r'github\.com'))
            if github_link:
                details['source_url'] = github_link.get('href')

                # Try to extract GitHub stars from the link text
                link_text = github_link.get_text(strip=True)
                stars_match = re.search(r'([\d.]+[km]?)\s*stars?', link_text, re.I)
                if stars_match:
                    stars_str = stars_match.group(1).lower()
                    # Convert "5k" -> 5000, "72.7k" -> 72700, etc
                    if 'k' in stars_str:
                        details['github_stars'] = int(float(stars_str.replace('k', '')) * 1000)
                    elif 'm' in stars_str:
                        details['github_stars'] = int(float(stars_str.replace('m', '')) * 1000000)
                    else:
                        try:
                            details['github_stars'] = int(stars_str)
                        except:
                            pass

            # Extract NPM package name from npm links
            npm_link = soup.find('a', href=re.compile(r'npmjs\.com/package'))
            if npm_link:
                npm_href = npm_link.get('href', '')
                package_match = re.search(r'npmjs\.com/package/([^/?]+)', npm_href)
                if package_match:
                    details['npm_package'] = package_match.group(1)

            # Extract PyPI package name
            pypi_link = soup.find('a', href=re.compile(r'pypi\.org/project'))
            if pypi_link:
                pypi_href = pypi_link.get('href', '')
                package_match = re.search(r'pypi\.org/project/([^/?]+)', pypi_href)
                if package_match:
                    details['pypi_package'] = package_match.group(1)

            # Extract full description - look for main content paragraphs
            # Try multiple strategies to find the description
            desc_elem = soup.find('p', class_=lambda x: x and any(cls in str(x).lower() for cls in ['description', 'text-', 'leading']))
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                if len(desc_text) > 50:  # Meaningful description
                    details['description_full'] = desc_text

            # Extract installation commands from code blocks
            code_blocks = soup.find_all(['code', 'pre'])
            install_commands = []
            for code_elem in code_blocks:
                code_text = code_elem.get_text(strip=True)
                # Look for install commands
                if any(keyword in code_text.lower() for keyword in ['npm install', 'pip install', 'npx', 'uvx']):
                    if len(code_text) < 200:  # Reasonable command length
                        install_commands.append(code_text)
            if install_commands:
                details['installation_commands'] = install_commands

            # Extract use cases or examples
            use_case_elem = soup.find(['div', 'section'], string=re.compile(r'use case', re.I))
            if use_case_elem:
                use_case_text = use_case_elem.get_text(strip=True)[:500]
                if use_case_text:
                    details['use_case'] = use_case_text

            # Extract categories/tags - look for badge-like elements
            tags = []
            tag_elements = soup.find_all(['span', 'a', 'div'], class_=lambda x: x and any(cls in str(x).lower() for cls in ['tag', 'badge', 'label', 'category']))
            for tag_elem in tag_elements:
                tag_text = tag_elem.get_text(strip=True)
                # Filter out common non-tag text
                if tag_text and len(tag_text) < 30 and tag_text not in ['Home', 'Servers', 'Back', 'Share', 'Copy']:
                    tags.append(tag_text)
            if tags:
                # Remove duplicates while preserving order
                seen = set()
                unique_tags = []
                for tag in tags:
                    if tag.lower() not in seen:
                        seen.add(tag.lower())
                        unique_tags.append(tag)
                details['tags'] = unique_tags[:20]  # Limit to 20 tags

        except Exception as e:
            print(f"  ⚠️  Error extracting details: {e}")
            import traceback
            traceback.print_exc()

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

            # Update description if the enriched one is longer/better
            if details.get('description_full') and len(details['description_full']) > len(server_data.get('description', '')):
                server_data['description'] = details['description_full']

            # Always update source_url if found (it's the most important enrichment)
            if details.get('source_url'):
                server_data['source_url'] = details['source_url']

            # Update tags (merge with existing)
            if details.get('tags'):
                existing_tags = set(server_data.get('tags', []))
                existing_tags.update(details['tags'])
                server_data['tags'] = sorted(list(existing_tags))  # Sort for consistency

            # Update categories (merge with existing)
            if details.get('categories'):
                existing_cats = set(server_data.get('categories', []))
                existing_cats.update(details['categories'])
                server_data['categories'] = sorted(list(existing_cats))  # Sort for consistency

            # Add metadata
            if 'metadata' not in server_data:
                server_data['metadata'] = {}

            # Add new metadata fields
            metadata_fields = [
                'github_stars',
                'npm_package',
                'pypi_package',
                'installation_commands',
                'use_case'
            ]

            for key in metadata_fields:
                if details.get(key):
                    server_data['metadata'][key] = details[key]

            # Mark as enriched
            server_data['enriched_at'] = datetime.now().isoformat()

            # Count enrichments added
            enrichments_added = []
            if details.get('source_url'):
                enrichments_added.append('GitHub URL')
            if details.get('github_stars'):
                enrichments_added.append(f"{details['github_stars']} ⭐")
            if details.get('npm_package'):
                enrichments_added.append('NPM')
            if details.get('pypi_package'):
                enrichments_added.append('PyPI')
            if details.get('tags'):
                enrichments_added.append(f"{len(details['tags'])} tags")
            if details.get('installation_commands'):
                enrichments_added.append('install cmds')

            if enrichments_added:
                print(f"  ✅ Added: {', '.join(enrichments_added)}")

            # Save updated data
            with open(server_file, 'w', encoding='utf-8') as f:
                json.dump(server_data, f, indent=2, ensure_ascii=False)

            self.enriched_count += 1
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
