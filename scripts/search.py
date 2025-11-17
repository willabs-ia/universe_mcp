#!/usr/bin/env python3
"""
Universe MCP - Search Helper
Command-line tool to search MCP servers
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import argparse
import sys

PROJECT_ROOT = Path(__file__).parent.parent
INDEX_DIR = PROJECT_ROOT / "indexes"


class MCPSearch:
    """Search utility for MCP servers"""

    def __init__(self):
        self.servers = []
        self.load_data()

    def load_data(self):
        """Load server data from indexes"""
        index_file = INDEX_DIR / "all-servers.json"
        if not index_file.exists():
            print("❌ Index file not found. Run indexer first:")
            print("   python scripts/indexers/generate_indexes.py")
            sys.exit(1)

        with open(index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.servers = data.get('servers', [])

        print(f"📚 Loaded {len(self.servers)} servers\n")

    def search_by_keyword(self, keyword: str) -> List[Dict]:
        """Search servers by keyword in name, description, or tags"""
        keyword_lower = keyword.lower()
        results = []

        for server in self.servers:
            if (keyword_lower in server.get('name', '').lower() or
                keyword_lower in server.get('description', '').lower() or
                keyword_lower in ' '.join(server.get('tags', [])).lower() or
                keyword_lower in server.get('provider', '').lower()):
                results.append(server)

        return results

    def search_by_classification(self, classification: str) -> List[Dict]:
        """Search servers by classification"""
        return [s for s in self.servers if s.get('classification') == classification]

    def search_by_provider(self, provider: str) -> List[Dict]:
        """Search servers by provider"""
        provider_lower = provider.lower()
        return [s for s in self.servers
                if provider_lower in s.get('provider', '').lower()]

    def search_by_category(self, category: str) -> List[Dict]:
        """Search servers by category"""
        category_lower = category.lower()
        return [s for s in self.servers
                if any(category_lower in cat.lower() for cat in s.get('categories', []))]

    def display_results(self, results: List[Dict], limit: Optional[int] = None):
        """Display search results"""
        if not results:
            print("🔍 No results found.")
            return

        total = len(results)
        display_count = min(limit, total) if limit else total

        print(f"🔍 Found {total} result(s)")
        if limit and total > limit:
            print(f"   Showing first {limit} results\n")
        else:
            print()

        for i, server in enumerate(results[:display_count], 1):
            classification = server.get('classification', 'unknown')
            badge = {
                'official': '🟢',
                'reference': '🔵',
                'community': '⚪'
            }.get(classification, '⚫')

            print(f"{i}. {badge} {server.get('name', 'Unknown')}")
            if server.get('provider'):
                print(f"   Provider: {server['provider']}")
            if server.get('description'):
                desc = server['description']
                if len(desc) > 100:
                    desc = desc[:100] + "..."
                print(f"   Description: {desc}")
            if server.get('url'):
                print(f"   URL: {server['url']}")
            if server.get('categories'):
                print(f"   Categories: {', '.join(server['categories'][:3])}")
            print()


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Search MCP servers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search by keyword
  python scripts/search.py "database"

  # Search official servers
  python scripts/search.py --classification official

  # Search by provider
  python scripts/search.py --provider "anthropic"

  # Search by category
  python scripts/search.py --category "ai"

  # Limit results
  python scripts/search.py "server" --limit 5
        """
    )

    parser.add_argument('keyword', nargs='?', help='Keyword to search for')
    parser.add_argument('-c', '--classification',
                        choices=['official', 'reference', 'community'],
                        help='Filter by classification')
    parser.add_argument('-p', '--provider', help='Filter by provider')
    parser.add_argument('--category', help='Filter by category')
    parser.add_argument('-l', '--limit', type=int, default=20,
                        help='Limit number of results (default: 20)')
    parser.add_argument('--json', action='store_true',
                        help='Output results as JSON')

    args = parser.parse_args()

    # Initialize search
    search = MCPSearch()

    # Perform search based on arguments
    results = search.servers  # Start with all servers

    if args.classification:
        results = [s for s in results if s.get('classification') == args.classification]

    if args.provider:
        provider_lower = args.provider.lower()
        results = [s for s in results
                  if provider_lower in s.get('provider', '').lower()]

    if args.category:
        category_lower = args.category.lower()
        results = [s for s in results
                  if any(category_lower in cat.lower() for cat in s.get('categories', []))]

    if args.keyword:
        keyword_lower = args.keyword.lower()
        results = [s for s in results
                  if (keyword_lower in s.get('name', '').lower() or
                      keyword_lower in s.get('description', '').lower() or
                      keyword_lower in ' '.join(s.get('tags', [])).lower())]

    # Output results
    if args.json:
        print(json.dumps(results[:args.limit], indent=2, ensure_ascii=False))
    else:
        search.display_results(results, limit=args.limit)


if __name__ == '__main__':
    main()
