#!/usr/bin/env python3
"""
Validate enrichment quality and completeness

Checks:
- How many servers have GitHub URLs
- How many have quality scores
- How many have capabilities
- How many have categories
- Distribution of quality scores
- Language distribution
- Runtime distribution
"""

import json
from pathlib import Path
from collections import Counter
from typing import Dict, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "servers"


def load_all_servers(classification: str = None) -> List[Dict]:
    """Load all server JSON files"""
    servers = []

    classifications = [classification] if classification else ['official', 'reference', 'community']

    for class_name in classifications:
        class_path = DATA_DIR / class_name
        if class_path.exists():
            for file_path in class_path.glob('*.json'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        server = json.load(f)
                        server['_classification'] = class_name
                        servers.append(server)
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")

    return servers


def validate_enrichment(classification: str = None):
    """Validate enrichment quality"""
    print("=" * 80)
    print("🔍 ENRICHMENT VALIDATION REPORT")
    print("=" * 80)

    servers = load_all_servers(classification)
    total = len(servers)

    print(f"\n📊 Total servers analyzed: {total}")
    if classification:
        print(f"   Classification: {classification}")

    # Count enriched fields
    with_github_url = sum(1 for s in servers if s.get('source_url'))
    with_quality_score = sum(1 for s in servers if s.get('quality_score') is not None)
    with_capabilities = sum(1 for s in servers if s.get('capabilities'))
    with_categories = sum(1 for s in servers if s.get('categories'))
    with_runtime = sum(1 for s in servers if s.get('runtime'))
    with_language = sum(1 for s in servers if s.get('language'))
    with_readme = sum(1 for s in servers if s.get('metadata', {}).get('readme_excerpt'))
    with_github_stars = sum(1 for s in servers if s.get('metadata', {}).get('github_stars'))

    print("\n" + "=" * 80)
    print("📈 ENRICHMENT COVERAGE")
    print("=" * 80)

    def print_stat(label, count):
        pct = (count / total * 100) if total > 0 else 0
        bar_len = int(pct / 2)  # 50 chars max
        bar = "█" * bar_len + "░" * (50 - bar_len)
        print(f"{label:30} {count:4}/{total} ({pct:5.1f}%) {bar}")

    print_stat("GitHub URL", with_github_url)
    print_stat("Quality Score", with_quality_score)
    print_stat("Capabilities", with_capabilities)
    print_stat("Categories", with_categories)
    print_stat("Runtime", with_runtime)
    print_stat("Language", with_language)
    print_stat("README Excerpt", with_readme)
    print_stat("GitHub Stars", with_github_stars)

    # Quality score distribution
    if with_quality_score > 0:
        print("\n" + "=" * 80)
        print("🏆 QUALITY SCORE DISTRIBUTION")
        print("=" * 80)

        scores = [s.get('quality_score', 0) for s in servers if s.get('quality_score') is not None]

        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)

        print(f"\nAverage: {avg_score:.1f}/100")
        print(f"Min:     {min_score}/100")
        print(f"Max:     {max_score}/100")

        # Distribution by ranges
        ranges = {
            "90-100 (Excellent)": len([s for s in scores if s >= 90]),
            "80-89  (Very Good)": len([s for s in scores if 80 <= s < 90]),
            "70-79  (Good)":      len([s for s in scores if 70 <= s < 80]),
            "60-69  (Fair)":      len([s for s in scores if 60 <= s < 70]),
            "50-59  (Average)":   len([s for s in scores if 50 <= s < 60]),
            "40-49  (Below Avg)": len([s for s in scores if 40 <= s < 50]),
            "0-39   (Poor)":      len([s for s in scores if s < 40]),
        }

        print("\nDistribution:")
        for range_label, count in ranges.items():
            pct = (count / len(scores) * 100) if len(scores) > 0 else 0
            bar_len = int(pct / 2)
            bar = "█" * bar_len
            print(f"  {range_label}: {count:3} ({pct:5.1f}%) {bar}")

    # Language distribution
    if with_language > 0:
        print("\n" + "=" * 80)
        print("💻 LANGUAGE DISTRIBUTION")
        print("=" * 80)

        languages = Counter(s.get('language') for s in servers if s.get('language'))

        print("\nTop 10 languages:")
        for lang, count in languages.most_common(10):
            pct = (count / total * 100) if total > 0 else 0
            bar_len = int(pct / 2)
            bar = "█" * bar_len
            print(f"  {lang:15} {count:3} ({pct:5.1f}%) {bar}")

    # Runtime distribution
    if with_runtime > 0:
        print("\n" + "=" * 80)
        print("🏃 RUNTIME DISTRIBUTION")
        print("=" * 80)

        runtimes = Counter(s.get('runtime') for s in servers if s.get('runtime'))

        print("\nRuntimes:")
        for runtime, count in runtimes.most_common():
            pct = (count / total * 100) if total > 0 else 0
            bar_len = int(pct / 2)
            bar = "█" * bar_len
            print(f"  {runtime:15} {count:3} ({pct:5.1f}%) {bar}")

    # Category distribution
    if with_categories > 0:
        print("\n" + "=" * 80)
        print("📂 CATEGORY DISTRIBUTION")
        print("=" * 80)

        all_categories = []
        for s in servers:
            all_categories.extend(s.get('categories', []))

        categories = Counter(all_categories)

        print("\nTop 15 categories:")
        for cat, count in categories.most_common(15):
            pct = (count / total * 100) if total > 0 else 0
            bar_len = int(pct / 2)
            bar = "█" * bar_len
            print(f"  {cat:15} {count:3} ({pct:5.1f}%) {bar}")

    # Top quality servers
    if with_quality_score > 0:
        print("\n" + "=" * 80)
        print("🌟 TOP 10 HIGHEST QUALITY SERVERS")
        print("=" * 80)

        top_servers = sorted(
            [s for s in servers if s.get('quality_score') is not None],
            key=lambda x: x.get('quality_score', 0),
            reverse=True
        )[:10]

        print()
        for i, server in enumerate(top_servers, 1):
            score = server.get('quality_score', 0)
            name = server.get('name', 'Unknown')
            stars = server.get('metadata', {}).get('github_stars', 0)
            lang = server.get('language', 'N/A')
            print(f"{i:2}. {name:35} {score:3}/100  ⭐ {stars:6,}  {lang:12}")

    # Servers without GitHub URLs (need attention)
    without_github = [s for s in servers if not s.get('source_url')]
    if without_github:
        print("\n" + "=" * 80)
        print(f"⚠️  SERVERS WITHOUT GITHUB URL ({len(without_github)})")
        print("=" * 80)

        if len(without_github) <= 20:
            for server in without_github:
                print(f"  - {server.get('name', 'Unknown')} ({server.get('_classification')})")
        else:
            print(f"\n  (Showing first 20 of {len(without_github)})")
            for server in without_github[:20]:
                print(f"  - {server.get('name', 'Unknown')} ({server.get('_classification')})")

    print("\n" + "=" * 80)
    print("✅ VALIDATION COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Validate enrichment quality')
    parser.add_argument('--classification', choices=['official', 'reference', 'community'],
                        help='Validate only specific classification')

    args = parser.parse_args()

    validate_enrichment(args.classification)
