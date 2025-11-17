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
import argparse


PROJECT_ROOT = Path(__file__).parent.parent.parent


def validate_enrichment(classification: str = None):
    """Validate enrichment quality"""

    # Build list of servers
    data_dir = PROJECT_ROOT / 'data' / 'servers'

    if classification:
        dirs = [data_dir / classification]
    else:
        dirs = [data_dir / 'official', data_dir / 'community', data_dir / 'reference']

    server_files = []
    for d in dirs:
        if d.exists():
            server_files.extend(sorted(d.glob('*.json')))

    # Statistics
    total_servers = len(server_files)
    has_source_url = 0
    has_github_stars = 0
    has_quality_score = 0
    has_capabilities = 0
    has_categories = 0
    has_language = 0
    has_license = 0
    has_readme = 0

    quality_scores = []
    languages = []
    runtimes = []
    categories = []
    licenses = []

    no_github_url = []
    top_quality = []

    for server_file in server_files:
        with open(server_file, 'r', encoding='utf-8') as f:
            server_data = json.load(f)

        metadata = server_data.get('metadata', {})

        # Check presence
        if server_data.get('source_url'):
            has_source_url += 1
        else:
            no_github_url.append(server_data.get('name', server_file.stem))

        if metadata.get('github_stars'):
            has_github_stars += 1

        if metadata.get('quality_score') is not None:
            has_quality_score += 1
            quality_scores.append(metadata['quality_score'])
            top_quality.append((server_data.get('name'), metadata['quality_score']))

        if metadata.get('capabilities'):
            has_capabilities += 1

        if server_data.get('categories'):
            has_categories += 1
            categories.extend(server_data['categories'])

        if metadata.get('language'):
            has_language += 1
            languages.append(metadata['language'])

        if metadata.get('license'):
            has_license += 1
            licenses.append(metadata['license'])

        if metadata.get('runtime'):
            runtimes.append(metadata['runtime'])

        if metadata.get('readme_excerpt'):
            has_readme += 1

    # Calculate percentages
    def pct(count):
        return (count / total_servers * 100) if total_servers > 0 else 0

    # Print report
    print(f"{'='*80}")
    print(f"📊 ENRICHMENT VALIDATION REPORT")
    print(f"{'='*80}")
    print(f"")
    print(f"Total servers: {total_servers}")
    print(f"")

    print(f"{'='*80}")
    print(f"📈 COVERAGE")
    print(f"{'='*80}")
    print(f"GitHub URLs:      {has_source_url:4d} / {total_servers} ({pct(has_source_url):5.1f}%)")
    print(f"GitHub Stars:     {has_github_stars:4d} / {total_servers} ({pct(has_github_stars):5.1f}%)")
    print(f"Quality Scores:   {has_quality_score:4d} / {total_servers} ({pct(has_quality_score):5.1f}%)")
    print(f"Capabilities:     {has_capabilities:4d} / {total_servers} ({pct(has_capabilities):5.1f}%)")
    print(f"Categories:       {has_categories:4d} / {total_servers} ({pct(has_categories):5.1f}%)")
    print(f"Languages:        {has_language:4d} / {total_servers} ({pct(has_language):5.1f}%)")
    print(f"Licenses:         {has_license:4d} / {total_servers} ({pct(has_license):5.1f}%)")
    print(f"README excerpts:  {has_readme:4d} / {total_servers} ({pct(has_readme):5.1f}%)")
    print(f"")

    if quality_scores:
        print(f"{'='*80}")
        print(f"🏆 QUALITY SCORE DISTRIBUTION")
        print(f"{'='*80}")
        avg_quality = sum(quality_scores) / len(quality_scores)
        min_quality = min(quality_scores)
        max_quality = max(quality_scores)

        print(f"Average:  {avg_quality:.1f}/100")
        print(f"Min:      {min_quality}/100")
        print(f"Max:      {max_quality}/100")
        print(f"")

        # Distribution
        ranges = {
            '90-100': len([s for s in quality_scores if s >= 90]),
            '80-89':  len([s for s in quality_scores if 80 <= s < 90]),
            '70-79':  len([s for s in quality_scores if 70 <= s < 80]),
            '60-69':  len([s for s in quality_scores if 60 <= s < 70]),
            '50-59':  len([s for s in quality_scores if 50 <= s < 60]),
            '0-49':   len([s for s in quality_scores if s < 50]),
        }

        print(f"Distribution:")
        for range_name, count in ranges.items():
            bar = '█' * (count // 5 if count > 0 else 0)
            print(f"  {range_name}: {count:4d} {bar}")
        print(f"")

    if languages:
        print(f"{'='*80}")
        print(f"💻 TOP LANGUAGES")
        print(f"{'='*80}")
        lang_counter = Counter(languages)
        for lang, count in lang_counter.most_common(10):
            bar = '█' * (count // 5 if count > 0 else 0)
            print(f"  {lang:20s}: {count:4d} {bar}")
        print(f"")

    if runtimes:
        print(f"{'='*80}")
        print(f"🏃 RUNTIME DISTRIBUTION")
        print(f"{'='*80}")
        runtime_counter = Counter(runtimes)
        for runtime, count in runtime_counter.most_common(10):
            bar = '█' * (count // 5 if count > 0 else 0)
            print(f"  {runtime:20s}: {count:4d} {bar}")
        print(f"")

    if categories:
        print(f"{'='*80}")
        print(f"📂 TOP CATEGORIES")
        print(f"{'='*80}")
        cat_counter = Counter(categories)
        for cat, count in cat_counter.most_common(15):
            bar = '█' * (count // 5 if count > 0 else 0)
            print(f"  {cat:20s}: {count:4d} {bar}")
        print(f"")

    if licenses:
        print(f"{'='*80}")
        print(f"⚖️  TOP LICENSES")
        print(f"{'='*80}")
        license_counter = Counter(licenses)
        for lic, count in license_counter.most_common(10):
            bar = '█' * (count // 5 if count > 0 else 0)
            print(f"  {lic:30s}: {count:4d} {bar}")
        print(f"")

    if top_quality:
        print(f"{'='*80}")
        print(f"🌟 TOP 10 HIGHEST QUALITY SERVERS")
        print(f"{'='*80}")
        top_quality.sort(key=lambda x: x[1], reverse=True)
        for idx, (name, score) in enumerate(top_quality[:10], 1):
            print(f"  {idx:2d}. {name:50s} - {score}/100")
        print(f"")

    if no_github_url:
        print(f"{'='*80}")
        print(f"⚠️  SERVERS WITHOUT GITHUB URL ({len(no_github_url)})")
        print(f"{'='*80}")
        for name in no_github_url[:20]:
            print(f"  - {name}")
        if len(no_github_url) > 20:
            print(f"  ... and {len(no_github_url) - 20} more")
        print(f"")


def main():
    parser = argparse.ArgumentParser(description='Validate MCP enrichment quality')
    parser.add_argument('--classification', choices=['official', 'community', 'reference'],
                        help='Only validate servers of this classification')

    args = parser.parse_args()

    validate_enrichment(classification=args.classification)


if __name__ == '__main__':
    main()
