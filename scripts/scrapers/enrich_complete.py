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
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "https://www.pulsemcp.com"
DELAY_BETWEEN_REQUESTS = 2.5  # Seconds between requests
GITHUB_API_DELAY = 1.2  # Be nice to GitHub API
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]

# GitHub API rate limit (60 req/hour without auth)
github_api_requests = 0
GITHUB_API_LIMIT = 55  # Leave buffer

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "servers"

# Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Universe MCP Enrichment Bot)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# Category keywords for automatic classification
CATEGORY_KEYWORDS = {
    'database': ['database', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'sqlite', 'supabase', 'prisma'],
    'browser': ['browser', 'puppeteer', 'playwright', 'selenium', 'chrome', 'firefox', 'web automation'],
    'filesystem': ['filesystem', 'file system', 'files', 'directory', 'folders', 'storage'],
    'api': ['api', 'rest', 'graphql', 'http', 'endpoint', 'web service', 'webhook'],
    'search': ['search', 'elasticsearch', 'algolia', 'indexing', 'query', 'find'],
    'ai': ['ai', 'llm', 'machine learning', 'neural', 'gpt', 'claude', 'openai', 'anthropic'],
    'cloud': ['aws', 'azure', 'gcp', 'cloud', 's3', 'lambda', 'cloudflare'],
    'git': ['git', 'github', 'gitlab', 'version control', 'repository', 'commit'],
    'messaging': ['slack', 'discord', 'telegram', 'email', 'notification', 'messaging', 'chat'],
    'documentation': ['documentation', 'docs', 'wiki', 'markdown', 'readme'],
    'testing': ['test', 'testing', 'qa', 'validation', 'assertion', 'spec'],
    'monitoring': ['monitoring', 'logging', 'metrics', 'observability', 'analytics', 'tracking'],
    'security': ['security', 'auth', 'authentication', 'authorization', 'encryption', 'oauth'],
    'development': ['development', 'dev tools', 'debugging', 'code', 'programming', 'ide'],
    'data': ['data', 'analytics', 'visualization', 'chart', 'graph', 'report'],
}


class CompleteEnricher:
    """Complete MCP server enrichment with PulseMCP + GitHub data"""

    def __init__(self, delay: float = DELAY_BETWEEN_REQUESTS):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.enriched_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def fetch_with_retry(self, url: str, retry_count: int = 0) -> Optional[requests.Response]:
        """Fetch URL with retry logic"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if retry_count < MAX_RETRIES:
                delay = RETRY_DELAYS[retry_count]
                print(f"    ⚠️  Retry {retry_count + 1}/{MAX_RETRIES} in {delay}s...")
                time.sleep(delay)
                return self.fetch_with_retry(url, retry_count + 1)
            return None

    def extract_github_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract GitHub URL from PulseMCP page"""
        # Look for GitHub link
        github_link = soup.find('a', href=re.compile(r'github\.com'))
        if github_link:
            url = github_link.get('href', '')
            # Clean up URL
            if url.startswith('//'):
                url = 'https:' + url
            return url
        return None

    def extract_github_stars(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract GitHub stars from PulseMCP page"""
        # Look for star count near GitHub link
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
        return None

    def extract_github_owner_repo(self, url: str) -> Optional[tuple]:
        """Extract owner and repo from GitHub URL"""
        if not url:
            return None
        parsed = urlparse(url)
        if 'github.com' not in parsed.netloc:
            return None
        parts = [p for p in parsed.path.split('/') if p]
        if len(parts) >= 2:
            return (parts[0], parts[1])
        return None

    def fetch_github_readme(self, owner: str, repo: str) -> Optional[str]:
        """Fetch README from GitHub repository"""
        readme_urls = [
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
        ]
        for url in readme_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    return response.text
            except:
                continue
        return None

    def fetch_github_api_data(self, owner: str, repo: str) -> Optional[Dict]:
        """Fetch repository metadata from GitHub API"""
        global github_api_requests

        if github_api_requests >= GITHUB_API_LIMIT:
            print(f"    ⚠️  GitHub API limit reached, skipping")
            return None

        try:
            url = f"https://api.github.com/repos/{owner}/{repo}"
            response = self.session.get(url, timeout=10)
            github_api_requests += 1

            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

    def extract_capabilities(self, readme: str) -> List[str]:
        """Extract capabilities/features from README"""
        capabilities = []

        # Look for features section
        features_match = re.search(r'##\s*(Features|Tools|Capabilities|What.*does)(.*?)(?=##|\Z)',
                                   readme, re.IGNORECASE | re.DOTALL)
        if features_match:
            content = features_match.group(2)
            # Extract bullet points
            bullets = re.findall(r'[-*+]\s*([^\n]+)', content)
            capabilities.extend([b.strip() for b in bullets if 10 < len(b.strip()) < 200])

        return list(set(capabilities))[:15]  # Max 15 unique

    def extract_installation_info(self, readme: str) -> Dict[str, Any]:
        """Extract installation commands and runtime info"""
        info = {
            'commands': [],
            'runtime': None,
            'package_manager': None,
        }

        # Look for installation section
        install_match = re.search(r'##\s*(Installation|Install|Setup|Getting Started)(.*?)(?=##|\Z)',
                                  readme, re.IGNORECASE | re.DOTALL)
        if install_match:
            content = install_match.group(2)

            # Extract code blocks
            code_blocks = re.findall(r'```(?:bash|shell|sh)?\n(.*?)```', content, re.DOTALL)
            for code in code_blocks[:2]:  # Max 2 code blocks
                commands = [line.strip() for line in code.split('\n')
                           if line.strip() and not line.strip().startswith('#')]
                info['commands'].extend(commands[:3])

        # Detect runtime
        readme_lower = readme.lower()
        if 'node' in readme_lower or 'npm' in readme_lower or 'npx' in readme_lower:
            info['runtime'] = 'Node.js'
            info['package_manager'] = 'npm'
        elif 'python' in readme_lower or 'pip' in readme_lower:
            py_match = re.search(r'python\s*([0-9.]+)', readme_lower)
            info['runtime'] = f"Python {py_match.group(1)}" if py_match else "Python"
            info['package_manager'] = 'pip'
        elif 'go' in readme_lower and 'golang' in readme_lower:
            info['runtime'] = 'Go'

        return info

    def categorize_server(self, readme: str, description: str, name: str) -> List[str]:
        """Automatically categorize server based on content"""
        text = (readme + ' ' + description + ' ' + name).lower()
        categories = []

        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    categories.append(category)
                    break

        return list(set(categories))

    def calculate_quality_score(self, server_data: Dict, api_data: Optional[Dict],
                                has_readme: bool) -> int:
        """Calculate quality score (0-100) for AI decision-making"""
        score = 0

        # GitHub stars (30 points max)
        stars = server_data.get('metadata', {}).get('github_stars', 0)
        if stars > 50000:
            score += 30
        elif stars > 10000:
            score += 27
        elif stars > 1000:
            score += 22
        elif stars > 100:
            score += 15
        elif stars > 10:
            score += 8
        elif stars > 0:
            score += 4

        # Classification (15 points max)
        classification = server_data.get('classification', '')
        if classification == 'official':
            score += 15
        elif classification == 'reference':
            score += 12
        elif classification == 'community':
            score += 7

        # Documentation (15 points max)
        if has_readme:
            score += 10
        if server_data.get('capabilities'):
            score += 5

        # Freshness (20 points max)
        if api_data and 'pushed_at' in api_data:
            try:
                pushed_at = datetime.fromisoformat(api_data['pushed_at'].replace('Z', '+00:00'))
                days_old = (datetime.now(pushed_at.tzinfo) - pushed_at).days
                if days_old < 30:
                    score += 20
                elif days_old < 90:
                    score += 15
                elif days_old < 180:
                    score += 10
                elif days_old < 365:
                    score += 5
            except:
                pass

        # Maintenance (10 points max)
        if api_data:
            open_issues = api_data.get('open_issues_count', 0)
            if open_issues < 5:
                score += 10
            elif open_issues < 20:
                score += 6
            elif open_issues < 50:
                score += 3

        # License (10 points max)
        if api_data and api_data.get('license'):
            license_name = api_data['license'].get('name', '').lower()
            if any(lic in license_name for lic in ['mit', 'apache', 'bsd']):
                score += 10
            elif license_name:
                score += 5

        return min(score, 100)

    def enrich_server(self, file_path: Path) -> bool:
        """Complete enrichment of a single server"""
        try:
            # Load server data
            with open(file_path, 'r', encoding='utf-8') as f:
                server_data = json.load(f)

            # Check if recently enriched
            enriched_at = server_data.get('metadata', {}).get('complete_enriched_at')
            if enriched_at:
                enriched_date = datetime.fromisoformat(enriched_at)
                days_since = (datetime.now() - enriched_date).days
                if days_since < 7:
                    print(f"    ⏭️  Skipped (enriched {days_since} days ago)")
                    self.skipped_count += 1
                    return False

            server_url = server_data.get('url')
            if not server_url:
                print(f"    ⚠️  No URL")
                self.error_count += 1
                return False

            print(f"\n🔍 {server_data.get('name', 'Unknown')}")

            # STEP 1: Enrich from PulseMCP page
            print(f"    📄 Fetching PulseMCP page...")
            response = self.fetch_with_retry(server_url)
            if response:
                soup = BeautifulSoup(response.content, 'lxml')

                # Extract GitHub URL
                github_url = self.extract_github_url(soup)
                if github_url:
                    server_data['source_url'] = github_url
                    print(f"    ✅ GitHub URL: {github_url}")

                # Extract stars from page
                stars = self.extract_github_stars(soup)
                if stars:
                    if 'metadata' not in server_data:
                        server_data['metadata'] = {}
                    server_data['metadata']['github_stars'] = stars
                    print(f"    ✅ Stars: {stars:,}")

            # STEP 2: Enrich from GitHub
            github_url = server_data.get('source_url')
            if github_url:
                github_info = self.extract_github_owner_repo(github_url)
                if github_info:
                    owner, repo = github_info
                    print(f"    🐙 GitHub: {owner}/{repo}")

                    # Fetch README
                    readme = self.fetch_github_readme(owner, repo)
                    has_readme = readme is not None

                    if readme:
                        print(f"    ✅ README ({len(readme)} chars)")

                        # Extract capabilities
                        capabilities = self.extract_capabilities(readme)
                        if capabilities:
                            server_data['capabilities'] = capabilities
                            print(f"    ✅ {len(capabilities)} capabilities")

                        # Extract installation
                        install_info = self.extract_installation_info(readme)
                        if install_info['commands']:
                            server_data['metadata']['installation_commands'] = install_info['commands']
                            print(f"    ✅ {len(install_info['commands'])} install commands")
                        if install_info['runtime']:
                            server_data['runtime'] = install_info['runtime']
                            print(f"    ✅ Runtime: {install_info['runtime']}")
                        if install_info['package_manager']:
                            server_data['package_manager'] = install_info['package_manager']

                        # Categorize
                        categories = self.categorize_server(
                            readme,
                            server_data.get('description', ''),
                            server_data.get('name', '')
                        )
                        if categories:
                            server_data['categories'] = categories
                            print(f"    ✅ Categories: {', '.join(categories[:3])}")

                        # Store README excerpt
                        server_data['metadata']['readme_excerpt'] = readme[:1500]

                    # Fetch GitHub API data
                    time.sleep(GITHUB_API_DELAY)
                    api_data = self.fetch_github_api_data(owner, repo)

                    if api_data:
                        print(f"    ✅ GitHub API data")

                        # Store key metadata
                        server_data['metadata'].update({
                            'language': api_data.get('language'),
                            'license': api_data.get('license', {}).get('name') if api_data.get('license') else None,
                            'github_stars': api_data.get('stargazers_count', server_data['metadata'].get('github_stars')),
                            'forks': api_data.get('forks_count'),
                            'open_issues': api_data.get('open_issues_count'),
                            'watchers': api_data.get('watchers_count'),
                            'last_pushed': api_data.get('pushed_at'),
                            'created_at': api_data.get('created_at'),
                            'topics': api_data.get('topics', []),
                        })

                        if api_data.get('language'):
                            server_data['language'] = api_data['language']
                            print(f"    ✅ Language: {api_data['language']}")

                    # Calculate quality score
                    quality_score = self.calculate_quality_score(server_data, api_data, has_readme)
                    server_data['quality_score'] = quality_score
                    print(f"    ✅ Quality: {quality_score}/100")

            # Mark as enriched
            if 'metadata' not in server_data:
                server_data['metadata'] = {}
            server_data['metadata']['complete_enriched_at'] = datetime.now().isoformat()

            # Save
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(server_data, f, indent=2, ensure_ascii=False)

            self.enriched_count += 1
            print(f"    ✅ COMPLETE!")
            return True

        except Exception as e:
            print(f"    ❌ Error: {e}")
            self.error_count += 1
            return False

    def run(self, test_mode: bool = False, limit: Optional[int] = None,
            classification: Optional[str] = None):
        """Run complete enrichment"""
        print("=" * 80)
        print("🚀 UNIVERSE MCP - COMPLETE SERVER ENRICHMENT")
        print("=" * 80)

        # Collect server files
        server_files = []
        classifications = [classification] if classification else ['official', 'reference', 'community']

        for class_name in classifications:
            class_path = DATA_DIR / class_name
            if class_path.exists():
                server_files.extend(list(class_path.glob('*.json')))

        total_files = len(server_files)

        if test_mode:
            server_files = server_files[:5]
            print(f"🧪 TEST MODE: Processing {len(server_files)} servers")

        if limit:
            server_files = server_files[:limit]

        print(f"\n📊 Total servers: {len(server_files)} (of {total_files})")
        print(f"⏱️  Estimated time: ~{len(server_files) * (self.delay + 3):.0f}s ({len(server_files) * (self.delay + 3) / 60:.1f} minutes)")
        print()

        for i, file_path in enumerate(server_files, 1):
            print(f"\n[{i}/{len(server_files)}]", end=" ")
            self.enrich_server(file_path)

            # Rate limiting
            if i < len(server_files):
                time.sleep(self.delay)

        # Summary
        print("\n" + "=" * 80)
        print("📊 ENRICHMENT SUMMARY")
        print("=" * 80)
        print(f"✅ Enriched: {self.enriched_count}")
        print(f"⏭️  Skipped: {self.skipped_count}")
        print(f"❌ Errors: {self.error_count}")
        print(f"📁 Total: {len(server_files)}")
        print(f"🐙 GitHub API requests: {github_api_requests}/{GITHUB_API_LIMIT}")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Complete MCP server enrichment')
    parser.add_argument('--test', action='store_true', help='Test mode (5 servers)')
    parser.add_argument('--limit', type=int, help='Limit number of servers')
    parser.add_argument('--classification', choices=['official', 'reference', 'community'],
                        help='Only enrich specific classification')
    parser.add_argument('--delay', type=float, default=DELAY_BETWEEN_REQUESTS,
                        help=f'Delay between requests (default: {DELAY_BETWEEN_REQUESTS}s)')

    args = parser.parse_args()

    enricher = CompleteEnricher(delay=args.delay)
    enricher.run(test_mode=args.test, limit=args.limit, classification=args.classification)


if __name__ == '__main__':
    main()
