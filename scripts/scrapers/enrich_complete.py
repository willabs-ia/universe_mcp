#!/usr/bin/env python3
"""
Universe MCP - Complete Server Enrichment

Unified enrichment script that combines:
1. PulseMCP page scraping (source_url, tags, stars)
2. GitHub README analysis (capabilities, installation, runtime)
3. GitHub API data (language, license, freshness, issues)
4. Automatic categorization
5. Quality scoring for AI decision-making

This provides maximum data richness for AI agents to choose the best MCP server.

Usage:
    python enrich_complete.py [--test] [--limit N] [--classification TYPE]
"""

import os
import sys
import json
import time
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from collections import Counter

import requests
from bs4 import BeautifulSoup

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class CompleteEnricher:
    """Complete enrichment combining PulseMCP + GitHub data"""

    def __init__(self, delay: float = 2.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        self.enriched_count = 0
        self.error_count = 0
        self.skipped_count = 0
        self.github_api_calls = 0

        # Categories for automatic classification
        self.category_keywords = {
            'database': ['database', 'sql', 'postgres', 'mysql', 'mongodb', 'redis', 'sqlite'],
            'browser': ['browser', 'puppeteer', 'playwright', 'selenium', 'chrome'],
            'api': ['api', 'rest', 'graphql', 'http', 'request'],
            'ai': ['ai', 'ml', 'machine learning', 'llm', 'gpt', 'anthropic'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 's3', 'lambda'],
            'search': ['search', 'elastic', 'algolia', 'index'],
            'development': ['dev', 'code', 'github', 'git', 'vscode'],
            'git': ['git', 'github', 'gitlab', 'version control'],
            'documentation': ['docs', 'documentation', 'readme', 'wiki'],
            'filesystem': ['file', 'directory', 'path', 'storage'],
            'testing': ['test', 'testing', 'jest', 'pytest', 'mocha'],
            'security': ['security', 'auth', 'oauth', 'encryption'],
            'monitoring': ['monitor', 'log', 'analytics', 'metrics'],
            'data': ['data', 'analytics', 'etl', 'pipeline'],
            'workflow': ['workflow', 'automation', 'pipeline', 'ci/cd']
        }

    def enrich_all(self, classification: Optional[str] = None, limit: Optional[int] = None, test: bool = False):
        """Enrich all servers"""

        # Build list of servers to enrich
        data_dir = PROJECT_ROOT / 'data' / 'servers'

        if classification:
            dirs = [data_dir / classification]
        else:
            dirs = [data_dir / 'official', data_dir / 'community', data_dir / 'reference']

        server_files = []
        for d in dirs:
            if d.exists():
                server_files.extend(sorted(d.glob('*.json')))

        if limit:
            server_files = server_files[:limit]

        if test:
            server_files = server_files[:5]

        total = len(server_files)

        print(f"{'='*80}")
        print(f"🚀 UNIVERSE MCP - COMPLETE ENRICHMENT")
        print(f"{'='*80}")
        print(f"Total servers to enrich: {total}")
        print(f"Delay between requests: {self.delay}s")
        print(f"")

        for idx, server_file in enumerate(server_files, 1):
            print(f"\n[{idx}/{total}]")

            # Read server data
            with open(server_file, 'r', encoding='utf-8') as f:
                server_data = json.load(f)

            server_name = server_data.get('name', server_file.stem)
            print(f"🔍 {server_name}")

            # Skip if already enriched
            if server_data.get('enriched_at') and not test:
                print(f"  ⏭️  Skipped (already enriched)")
                self.skipped_count += 1
                continue

            # Enrich the server
            success = self.enrich_server(server_data, server_file)

            if success:
                print(f"  ✅ COMPLETE!")
                self.enriched_count += 1
            else:
                self.error_count += 1

            # Rate limiting
            if idx < total:
                time.sleep(self.delay)

        # Final summary
        print(f"\n{'='*80}")
        print(f"📊 ENRICHMENT SUMMARY")
        print(f"{'='*80}")
        print(f"✅ Successfully enriched: {self.enriched_count}")
        print(f"⏭️  Skipped: {self.skipped_count}")
        print(f"❌ Errors: {self.error_count}")
        print(f"🔧 GitHub API requests used: {self.github_api_calls}/60")
        print(f"")

    def enrich_server(self, server_data: Dict, server_file: Path) -> bool:
        """Enrich a single server with complete data"""

        try:
            # STEP 1: Get GitHub URL from PulseMCP page (if not already present)
            if not server_data.get('source_url'):
                print(f"  📄 Fetching PulseMCP page...")
                github_url = self.extract_github_url_from_page(server_data.get('url'))
                if github_url:
                    server_data['source_url'] = github_url
                    print(f"  ✅ GitHub URL: {github_url}")
            else:
                github_url = server_data.get('source_url')
                print(f"  ✅ GitHub URL: {github_url}")

            # If no GitHub URL, skip detailed enrichment
            if not github_url:
                print(f"  ⚠️  No GitHub URL found")
                return self.save_server(server_data, server_file)

            # STEP 2: Extract GitHub stars from PulseMCP page
            if server_data.get('url'):
                stars = self.extract_github_stars_from_page(server_data.get('url'))
                if stars:
                    if 'metadata' not in server_data:
                        server_data['metadata'] = {}
                    server_data['metadata']['github_stars'] = stars

            # STEP 3: Fetch GitHub README
            print(f"  📖 Fetching GitHub README...")
            readme_data = self.fetch_github_readme(github_url)

            if readme_data:
                # Extract capabilities
                capabilities = self.extract_capabilities(readme_data)
                if capabilities:
                    if 'metadata' not in server_data:
                        server_data['metadata'] = {}
                    server_data['metadata']['capabilities'] = capabilities
                    print(f"  ✅ Extracted {len(capabilities)} capabilities")

                # Extract runtime/language
                runtime = self.detect_runtime(readme_data)
                if runtime:
                    if 'metadata' not in server_data:
                        server_data['metadata'] = {}
                    server_data['metadata']['runtime'] = runtime
                    print(f"  ✅ Runtime: {runtime}")

                # Store README excerpt
                if 'metadata' not in server_data:
                    server_data['metadata'] = {}
                server_data['metadata']['readme_excerpt'] = readme_data[:1500]

            # STEP 4: Fetch GitHub API data
            print(f"  🔧 Fetching GitHub API data...")
            api_data = self.fetch_github_api_data(github_url)

            if api_data:
                if 'metadata' not in server_data:
                    server_data['metadata'] = {}

                server_data['metadata']['language'] = api_data.get('language')
                server_data['metadata']['license'] = api_data.get('license')
                server_data['metadata']['github_stars'] = api_data.get('stars', server_data.get('metadata', {}).get('github_stars'))
                server_data['metadata']['forks'] = api_data.get('forks')
                server_data['metadata']['open_issues'] = api_data.get('open_issues')
                server_data['metadata']['last_pushed'] = api_data.get('pushed_at')
                server_data['metadata']['topics'] = api_data.get('topics', [])

                print(f"  ✅ Language: {api_data.get('language')}")
                print(f"  ✅ Stars: {api_data.get('stars')}")
                print(f"  ✅ License: {api_data.get('license')}")

            # STEP 5: Automatic categorization
            categories = self.categorize_server(server_data, readme_data)
            if categories:
                server_data['categories'] = list(categories)
                print(f"  ✅ Categories: {len(categories)}")

            # STEP 6: Calculate quality score
            quality_score = self.calculate_quality_score(server_data)
            if 'metadata' not in server_data:
                server_data['metadata'] = {}
            server_data['metadata']['quality_score'] = quality_score
            print(f"  ✅ Quality Score: {quality_score}/100")

            # Mark as enriched
            server_data['enriched_at'] = datetime.utcnow().isoformat()

            # Save
            return self.save_server(server_data, server_file)

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return False

    def extract_github_url_from_page(self, page_url: str) -> Optional[str]:
        """Extract GitHub URL from PulseMCP server page"""
        if not page_url:
            return None

        try:
            response = self.session.get(page_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for GitHub link
            github_link = soup.find('a', href=re.compile(r'github\.com'))
            if github_link:
                return github_link.get('href')

        except Exception as e:
            print(f"  ⚠️  Error fetching page: {e}")

        return None

    def extract_github_stars_from_page(self, page_url: str) -> Optional[int]:
        """Extract GitHub stars from PulseMCP page"""
        if not page_url:
            return None

        try:
            response = self.session.get(page_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for star count
            star_elem = soup.find(string=re.compile(r'⭐|stars?', re.I))
            if star_elem:
                star_text = star_elem.get_text() if hasattr(star_elem, 'get_text') else str(star_elem)

                # Extract number (e.g., "72.7k" -> 72700)
                match = re.search(r'(\d+\.?\d*)\s*([kK])?', star_text)
                if match:
                    try:
                        num = float(match.group(1))
                        if match.group(2):  # 'k' or 'K'
                            num *= 1000
                        return int(num)
                    except (ValueError, AttributeError):
                        pass

        except Exception:
            pass

        return None

    def fetch_github_readme(self, github_url: str) -> Optional[str]:
        """Fetch GitHub README content"""
        if not github_url:
            return None

        try:
            # Parse owner/repo from URL
            match = re.search(r'github\.com/([^/]+)/([^/]+)', github_url)
            if not match:
                return None

            owner, repo = match.groups()
            repo = repo.replace('.git', '')

            # Fetch README via raw.githubusercontent.com
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
            response = self.session.get(readme_url, timeout=10)

            if response.status_code == 404:
                # Try master branch
                readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
                response = self.session.get(readme_url, timeout=10)

            if response.status_code == 200:
                return response.text

        except Exception as e:
            print(f"  ⚠️  Error fetching README: {e}")

        return None

    def fetch_github_api_data(self, github_url: str) -> Optional[Dict]:
        """Fetch GitHub API data"""
        if not github_url:
            return None

        try:
            # Parse owner/repo from URL
            match = re.search(r'github\.com/([^/]+)/([^/]+)', github_url)
            if not match:
                return None

            owner, repo = match.groups()
            repo = repo.replace('.git', '')

            # Fetch from GitHub API (no auth = 60 requests/hour)
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = self.session.get(api_url, timeout=10)

            self.github_api_calls += 1

            if response.status_code == 200:
                data = response.json()
                return {
                    'language': data.get('language'),
                    'license': data.get('license', {}).get('name') if data.get('license') else None,
                    'stars': data.get('stargazers_count'),
                    'forks': data.get('forks_count'),
                    'open_issues': data.get('open_issues_count'),
                    'pushed_at': data.get('pushed_at'),
                    'topics': data.get('topics', [])
                }

        except Exception as e:
            print(f"  ⚠️  Error fetching GitHub API: {e}")

        return None

    def extract_capabilities(self, readme: str) -> List[str]:
        """Extract capabilities from README"""
        if not readme:
            return []

        capabilities = set()

        # Look for features section
        features_match = re.search(r'##\s*(?:Features|Capabilities|What it does)(.+?)(?=##|\Z)', readme, re.I | re.DOTALL)
        if features_match:
            features_text = features_match.group(1)

            # Extract bullet points
            for line in features_text.split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('*'):
                    capability = line.lstrip('-*').strip()
                    if capability and len(capability) < 200:
                        # Clean up
                        capability = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', capability)  # Remove markdown links
                        capabilities.add(capability)

        return list(capabilities)[:15]  # Max 15 capabilities

    def detect_runtime(self, readme: str) -> Optional[str]:
        """Detect runtime from README"""
        if not readme:
            return None

        readme_lower = readme.lower()

        # Check for runtime indicators
        if 'node' in readme_lower or 'npm install' in readme_lower or 'package.json' in readme_lower:
            return 'Node.js'
        elif 'python' in readme_lower or 'pip install' in readme_lower or 'requirements.txt' in readme_lower:
            return 'Python'
        elif 'go get' in readme_lower or 'package main' in readme_lower:
            return 'Go'
        elif 'cargo' in readme_lower or 'rust' in readme_lower:
            return 'Rust'

        return None

    def categorize_server(self, server_data: Dict, readme: Optional[str] = None) -> Set[str]:
        """Automatically categorize server based on content"""
        categories = set()

        # Combine all text for analysis
        text_parts = [
            server_data.get('name', ''),
            server_data.get('description', ''),
            server_data.get('provider', ''),
            ' '.join(server_data.get('tags', [])),
        ]

        if readme:
            text_parts.append(readme[:2000])  # First 2000 chars

        if server_data.get('metadata', {}).get('topics'):
            text_parts.extend(server_data['metadata']['topics'])

        combined_text = ' '.join(text_parts).lower()

        # Check each category
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    categories.add(category)
                    break

        return categories

    def calculate_quality_score(self, server_data: Dict) -> int:
        """Calculate quality score (0-100)"""
        score = 0
        metadata = server_data.get('metadata', {})

        # GitHub stars (max 30 points)
        stars = metadata.get('github_stars', 0)
        if stars:
            if stars >= 10000:
                score += 30
            elif stars >= 1000:
                score += 25
            elif stars >= 100:
                score += 20
            elif stars >= 10:
                score += 15
            else:
                score += 10

        # Has README (10 points)
        if metadata.get('readme_excerpt'):
            score += 10

        # Has capabilities (10 points)
        if metadata.get('capabilities'):
            score += 10

        # License (10 points)
        if metadata.get('license'):
            score += 10

        # Recent activity (15 points)
        if metadata.get('last_pushed'):
            try:
                from datetime import datetime
                last_push = datetime.fromisoformat(metadata['last_pushed'].replace('Z', '+00:00'))
                days_ago = (datetime.now(last_push.tzinfo) - last_push).days

                if days_ago <= 30:
                    score += 15
                elif days_ago <= 90:
                    score += 12
                elif days_ago <= 180:
                    score += 8
                elif days_ago <= 365:
                    score += 5
            except:
                pass

        # Low open issues ratio (10 points)
        open_issues = metadata.get('open_issues', 0)
        if open_issues == 0:
            score += 10
        elif open_issues <= 5:
            score += 7
        elif open_issues <= 20:
            score += 4

        # Has categories (5 points)
        if server_data.get('categories'):
            score += 5

        # Official classification (10 points)
        if server_data.get('classification') == 'official':
            score += 10

        return min(score, 100)

    def save_server(self, server_data: Dict, server_file: Path) -> bool:
        """Save enriched server data"""
        try:
            with open(server_file, 'w', encoding='utf-8') as f:
                json.dump(server_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"  ❌ Error saving: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Complete MCP server enrichment')
    parser.add_argument('--classification', choices=['official', 'community', 'reference'],
                        help='Only enrich servers of this classification')
    parser.add_argument('--limit', type=int, help='Limit number of servers to enrich')
    parser.add_argument('--test', action='store_true', help='Test mode (only 5 servers)')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests (seconds)')

    args = parser.parse_args()

    enricher = CompleteEnricher(delay=args.delay)
    enricher.enrich_all(
        classification=args.classification,
        limit=args.limit,
        test=args.test
    )


if __name__ == '__main__':
    main()
