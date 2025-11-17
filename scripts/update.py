#!/usr/bin/env python3
"""
Universe MCP - Main Update Script
Coordinates all scrapers and indexers
"""

import sys
from pathlib import Path
import subprocess
import time
from datetime import datetime

# Add scrapers to path
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR / "scrapers"))
sys.path.insert(0, str(SCRIPTS_DIR / "indexers"))

from scrape_servers import ServerScraper
from scrape_clients import ClientScraper
from scrape_usecases import UseCaseScraper


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def run_scraper(scraper_class, name: str, test_mode: bool = False):
    """Run a scraper and return stats"""
    print_header(f"Running {name} Scraper")
    start_time = time.time()

    try:
        scraper = scraper_class()
        if test_mode:
            scraper.run(start_page=1, end_page=1 if name != "Server" else 2, resume=False)
        else:
            scraper.run(resume=True)

        elapsed = time.time() - start_time
        if name == "Server":
            count = scraper.servers_scraped
        elif name == "Client":
            count = scraper.clients_scraped
        else:
            count = scraper.usecases_scraped

        print(f"\n✅ {name} scraper completed in {elapsed:.2f}s")
        print(f"📊 {name}s scraped: {count}")
        return {'success': True, 'count': count, 'time': elapsed}

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ {name} scraper failed: {e}")
        return {'success': False, 'error': str(e), 'time': elapsed}


def generate_indexes():
    """Generate all indexes"""
    print_header("Generating Indexes")
    start_time = time.time()

    try:
        # Import and run indexer
        from generate_indexes import IndexGenerator
        generator = IndexGenerator()
        stats = generator.run()

        elapsed = time.time() - start_time
        print(f"\n✅ Index generation completed in {elapsed:.2f}s")
        return {'success': True, 'stats': stats, 'time': elapsed}

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Index generation failed: {e}")
        return {'success': False, 'error': str(e), 'time': elapsed}


def main():
    """Main update workflow"""
    import argparse

    parser = argparse.ArgumentParser(description='Update Universe MCP data')
    parser.add_argument('--test', action='store_true', help='Test mode: scrape only first few pages')
    parser.add_argument('--servers-only', action='store_true', help='Update only servers')
    parser.add_argument('--clients-only', action='store_true', help='Update only clients')
    parser.add_argument('--usecases-only', action='store_true', help='Update only use cases')
    parser.add_argument('--no-index', action='store_true', help='Skip index generation')

    args = parser.parse_args()

    print("=" * 80)
    print("🌌 UNIVERSE MCP - COMPLETE UPDATE")
    print("=" * 80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.test:
        print("🧪 TEST MODE: Limited scraping for testing")
    print()

    overall_start = time.time()
    results = {}

    # Run scrapers
    if not args.clients_only and not args.usecases_only:
        results['servers'] = run_scraper(ServerScraper, "Server", args.test)

    if not args.servers_only and not args.usecases_only:
        results['clients'] = run_scraper(ClientScraper, "Client", args.test)

    if not args.servers_only and not args.clients_only:
        results['usecases'] = run_scraper(UseCaseScraper, "Use Case", args.test)

    # Generate indexes
    if not args.no_index:
        results['indexes'] = generate_indexes()

    # Print summary
    overall_elapsed = time.time() - overall_start

    print("\n" + "=" * 80)
    print("📊 UPDATE SUMMARY")
    print("=" * 80)

    total_items = 0
    for key, result in results.items():
        status = "✅" if result.get('success', False) else "❌"
        print(f"\n{status} {key.capitalize()}:")
        if result.get('success'):
            if 'count' in result:
                count = result['count']
                total_items += count
                print(f"   Items: {count}")
            if 'stats' in result:
                print(f"   Stats: {result['stats']}")
            print(f"   Time: {result['time']:.2f}s")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")

    print("\n" + "-" * 80)
    print(f"⏱️  Total time: {overall_elapsed:.2f}s ({overall_elapsed/60:.2f} minutes)")
    print(f"📦 Total items processed: {total_items}")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == '__main__':
    main()
