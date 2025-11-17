#!/usr/bin/env python3
"""
Example: Searching MCP Servers

This example demonstrates different ways to search and filter
the Universe MCP database.
"""

import json
from pathlib import Path

# Path to indexes
INDEX_DIR = Path(__file__).parent.parent / "indexes"


def load_servers():
    """Load all servers from index"""
    with open(INDEX_DIR / "all-servers.json") as f:
        data = json.load(f)
    return data['servers']


def example_1_keyword_search():
    """Example 1: Search by keyword"""
    print("=" * 60)
    print("EXAMPLE 1: Keyword Search")
    print("=" * 60)

    servers = load_servers()
    keyword = "database"

    results = [
        s for s in servers
        if keyword.lower() in s.get('description', '').lower()
        or keyword.lower() in s.get('name', '').lower()
    ]

    print(f"Found {len(results)} servers related to '{keyword}':\n")
    for server in results[:5]:  # Show first 5
        print(f"- {server['name']}")
        print(f"  {server.get('description', 'No description')[:80]}...")
        print()


def example_2_official_servers():
    """Example 2: Find all official servers"""
    print("=" * 60)
    print("EXAMPLE 2: Official Servers")
    print("=" * 60)

    with open(INDEX_DIR / "servers-by-classification.json") as f:
        data = json.load(f)

    official = data['classifications']['official']

    print(f"Found {len(official)} official servers:\n")
    for server in official[:10]:  # Show first 10
        print(f"- {server['name']} by {server.get('provider', 'Unknown')}")


def example_3_top_providers():
    """Example 3: Get top providers"""
    print("=" * 60)
    print("EXAMPLE 3: Top Providers")
    print("=" * 60)

    with open(INDEX_DIR / "statistics.json") as f:
        stats = json.load(f)

    top_providers = stats['servers']['top_providers']

    print("Top 10 MCP Server Providers:\n")
    for i, (provider, count) in enumerate(list(top_providers.items())[:10], 1):
        print(f"{i}. {provider}: {count} servers")


def example_4_by_category():
    """Example 4: Find servers by category"""
    print("=" * 60)
    print("EXAMPLE 4: Search by Category")
    print("=" * 60)

    with open(INDEX_DIR / "servers-by-category.json") as f:
        data = json.load(f)

    categories = data['categories']

    print(f"Available categories: {len(categories)}\n")

    # Show a specific category if exists
    if categories:
        category_name = list(categories.keys())[0]
        servers = categories[category_name]
        print(f"Servers in '{category_name}' ({len(servers)}):")
        for server in servers[:5]:
            print(f"- {server['name']}")


def example_5_custom_filter():
    """Example 5: Custom filtering"""
    print("=" * 60)
    print("EXAMPLE 5: Custom Filter (Community + High Activity)")
    print("=" * 60)

    servers = load_servers()

    # Find community servers with high weekly metrics
    results = [
        s for s in servers
        if s.get('classification') == 'community'
        and s.get('weekly_metric', {}).get('value', 0) > 100
    ]

    # Sort by metric
    results.sort(
        key=lambda s: s.get('weekly_metric', {}).get('value', 0),
        reverse=True
    )

    print(f"Found {len(results)} popular community servers:\n")
    for server in results[:10]:
        metric = server.get('weekly_metric', {})
        print(f"- {server['name']}")
        print(f"  {metric.get('type', 'metric')}: {metric.get('value', 0):,}")
        print()


def main():
    """Run all examples"""
    examples = [
        example_1_keyword_search,
        example_2_official_servers,
        example_3_top_providers,
        example_4_by_category,
        example_5_custom_filter,
    ]

    for example in examples:
        try:
            example()
            print("\n")
        except FileNotFoundError:
            print("❌ Index files not found. Run the indexer first:")
            print("   python scripts/indexers/generate_indexes.py")
            break
        except Exception as e:
            print(f"❌ Error in {example.__name__}: {e}")
            print()


if __name__ == '__main__':
    main()
