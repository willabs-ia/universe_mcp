#!/usr/bin/env python3
"""
GitHub Data Enrichment Script

Enriches MCP server data with comprehensive GitHub information:
- README parsing for capabilities, examples, and technical details
- GitHub API metadata (language, license, issues, freshness)
- Automatic categorization based on README content
- Quality scoring for AI decision-making

Usage:
    python enrich_github_data.py [--test] [--limit N] [--classification TYPE]
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
from urllib.parse import urlparse

import requests

# Rate limiting
DELAY_BETWEEN_REQUESTS = 2.0  # seconds
GITHUB_API_DELAY = 1.0  # Be nice to GitHub API

# GitHub API (60 requests/hour without auth)
GITHUB_API_RATE_LIMIT = 60
github_api_requests = 0
github_api_reset_time = None

# Categories for automatic classification
CATEGORY_KEYWORDS = {
    'database': ['database', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'db', 'sqlite', 'supabase'],
    'browser': ['browser', 'puppeteer', 'playwright', 'selenium', 'chrome', 'firefox', 'web automation'],
    'filesystem': ['filesystem', 'file system', 'files', 'directory', 'folders', 'disk'],
    'api': ['api', 'rest', 'graphql', 'http', 'endpoint', 'web service'],
    'search': ['search', 'elasticsearch', 'algolia', 'indexing', 'query'],
    'ai': ['ai', 'llm', 'machine learning', 'neural', 'gpt', 'claude', 'openai'],
    'cloud': ['aws', 'azure', 'gcp', 'cloud', 's3', 'lambda', 'cloudflare'],
    'git': ['git', 'github', 'gitlab', 'version control', 'repository'],
    'messaging': ['slack', 'discord', 'telegram', 'email', 'notification', 'messaging'],
    'documentation': ['documentation', 'docs', 'wiki', 'markdown', 'readme'],
    'testing': ['test', 'testing', 'qa', 'validation', 'assertion'],
    'monitoring': ['monitoring', 'logging', 'metrics', 'observability', 'analytics'],
    'security': ['security', 'auth', 'authentication', 'authorization', 'encryption'],
    'development': ['development', 'dev tools', 'debugging', 'code', 'programming'],
}

# Language detection patterns
LANGUAGE_PATTERNS = {
    'typescript': ['typescript', 'ts', 'tsx'],
    'javascript': ['javascript', 'js', 'node.js', 'nodejs'],
    'python': ['python', 'py', 'pip', 'pypi', 'python3'],
    'go': ['golang', 'go lang', 'go'],
    'rust': ['rust', 'cargo'],
    'java': ['java', 'maven', 'gradle'],
    'ruby': ['ruby', 'gem', 'bundler'],
    'php': ['php', 'composer'],
    'c#': ['c#', 'csharp', 'dotnet', '.net'],
}

class GitHubEnricher:
    def __init__(self, delay: float = DELAY_BETWEEN_REQUESTS):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Universe MCP Data Enrichment Bot)'
        })
        self.enriched_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def extract_github_owner_repo(self, url: str) -> Optional[tuple]:
        """Extract owner and repo from GitHub URL"""
        if not url:
            return None

        # Parse URL
        parsed = urlparse(url)
        if 'github.com' not in parsed.netloc:
            return None

        # Extract owner/repo from path
        parts = [p for p in parsed.path.split('/') if p]
        if len(parts) >= 2:
            return (parts[0], parts[1])
        return None

    def fetch_github_readme(self, owner: str, repo: str) -> Optional[str]:
        """Fetch README content from GitHub repository"""
        readme_urls = [
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/readme.md",
        ]

        for url in readme_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    return response.text
            except Exception as e:
                continue

        return None

    def fetch_github_api_data(self, owner: str, repo: str) -> Optional[Dict]:
        """Fetch repository metadata from GitHub API"""
        global github_api_requests, github_api_reset_time

        # Check rate limit
        if github_api_requests >= GITHUB_API_RATE_LIMIT - 5:  # Leave 5 as buffer
            print(f"  ⚠️  GitHub API rate limit approaching, skipping API call")
            return None

        try:
            url = f"https://api.github.com/repos/{owner}/{repo}"
            response = self.session.get(url, timeout=10)

            github_api_requests += 1

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                print(f"  ⚠️  GitHub API rate limit exceeded")
                return None
            else:
                return None

        except Exception as e:
            return None

    def extract_capabilities_from_readme(self, readme: str) -> List[str]:
        """Extract capabilities/tools/features from README"""
        capabilities = []

        # Look for features/tools sections
        features_section = re.search(r'##\s*(Features|Tools|Capabilities|What.*does)(.*?)(?=##|\Z)', readme, re.IGNORECASE | re.DOTALL)
        if features_section:
            content = features_section.group(2)
            # Extract bullet points
            bullets = re.findall(r'[-*]\s*([^\n]+)', content)
            capabilities.extend([b.strip() for b in bullets if len(b.strip()) > 5])

        # Look for usage examples to infer capabilities
        usage_section = re.search(r'##\s*(Usage|Examples|How to)(.*?)(?=##|\Z)', readme, re.IGNORECASE | re.DOTALL)
        if usage_section:
            content = usage_section.group(2)
            # Extract code snippets to understand what it does
            code_blocks = re.findall(r'```[\w]*\n(.*?)```', content, re.DOTALL)
            for code in code_blocks[:3]:  # Limit to first 3 examples
                # Extract function/method calls
                functions = re.findall(r'(\w+)\s*\(', code)
                capabilities.extend([f for f in functions if len(f) > 3])

        return list(set(capabilities))[:20]  # Limit to 20 unique capabilities

    def extract_installation_info(self, readme: str) -> Dict[str, Any]:
        """Extract installation commands and requirements"""
        info = {
            'commands': [],
            'requirements': [],
            'runtime': None,
        }

        # Look for installation section
        install_section = re.search(r'##\s*(Installation|Install|Setup|Getting Started)(.*?)(?=##|\Z)', readme, re.IGNORECASE | re.DOTALL)
        if install_section:
            content = install_section.group(2)

            # Extract code blocks
            code_blocks = re.findall(r'```(?:bash|shell|sh)?\n(.*?)```', content, re.DOTALL)
            for code in code_blocks:
                commands = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('#')]
                info['commands'].extend(commands[:5])  # Max 5 commands per block

            # Extract npm/pip/cargo commands even outside code blocks
            npm_cmds = re.findall(r'(npm install [^\n]+)', content)
            pip_cmds = re.findall(r'(pip install [^\n]+)', content)
            cargo_cmds = re.findall(r'(cargo install [^\n]+)', content)

            info['commands'].extend(npm_cmds + pip_cmds + cargo_cmds)

        # Detect runtime requirements
        readme_lower = readme.lower()
        if 'node' in readme_lower or 'npm' in readme_lower:
            node_version = re.search(r'node\.?js?\s*([0-9.]+|\d+\+)', readme_lower)
            if node_version:
                info['runtime'] = f"Node.js {node_version.group(1)}"
            else:
                info['runtime'] = "Node.js"
        elif 'python' in readme_lower:
            py_version = re.search(r'python\s*([0-9.]+|\d+\.\d+)', readme_lower)
            if py_version:
                info['runtime'] = f"Python {py_version.group(1)}"
            else:
                info['runtime'] = "Python"

        # Extract requirements
        if 'docker' in readme_lower:
            info['requirements'].append('Docker')
        if 'api key' in readme_lower or 'token' in readme_lower:
            info['requirements'].append('API Key')

        return info

    def categorize_mcp(self, readme: str, description: str) -> List[str]:
        """Automatically categorize MCP based on content"""
        text = (readme + ' ' + description).lower()
        categories = []

        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    categories.append(category)
                    break  # Only count once per category

        return categories

    def detect_language(self, readme: str, api_data: Optional[Dict]) -> Optional[str]:
        """Detect primary programming language"""
        # First try GitHub API (most reliable)
        if api_data and 'language' in api_data:
            return api_data['language']

        # Fallback to README analysis
        readme_lower = readme.lower()
        for lang, patterns in LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if pattern in readme_lower:
                    return lang.title()

        return None

    def calculate_quality_score(self, server_data: Dict, api_data: Optional[Dict]) -> int:
        """Calculate quality score (0-100) for AI decision-making"""
        score = 0

        # GitHub stars (max 30 points)
        stars = server_data.get('metadata', {}).get('github_stars', 0)
        if stars > 10000:
            score += 30
        elif stars > 1000:
            score += 25
        elif stars > 100:
            score += 20
        elif stars > 10:
            score += 10
        elif stars > 0:
            score += 5

        # Classification (max 15 points)
        classification = server_data.get('classification', '')
        if classification == 'official':
            score += 15
        elif classification == 'reference':
            score += 10
        elif classification == 'community':
            score += 5

        # Documentation quality (max 15 points)
        if api_data:
            if api_data.get('has_wiki'):
                score += 5
            readme_size = api_data.get('size', 0)
            if readme_size > 1000:
                score += 10
            elif readme_size > 100:
                score += 5

        # Freshness (max 20 points)
        if api_data and 'pushed_at' in api_data:
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

        # Issue management (max 10 points)
        if api_data:
            open_issues = api_data.get('open_issues_count', 0)
            if open_issues < 5:
                score += 10
            elif open_issues < 20:
                score += 5

        # License (max 10 points)
        if api_data and api_data.get('license'):
            license_name = api_data['license'].get('name', '').lower()
            if 'mit' in license_name or 'apache' in license_name:
                score += 10
            elif license_name:
                score += 5

        return min(score, 100)

    def enrich_from_github(self, server_data: Dict) -> Dict:
        """Enrich server data with comprehensive GitHub information"""
        source_url = server_data.get('source_url')
        if not source_url:
            return {}

        # Extract owner/repo
        github_info = self.extract_github_owner_repo(source_url)
        if not github_info:
            return {}

        owner, repo = github_info
        enriched = {}

        print(f"  🔍 Fetching GitHub data for {owner}/{repo}...")

        # Fetch README
        readme = self.fetch_github_readme(owner, repo)
        if readme:
            print(f"    ✅ README fetched ({len(readme)} chars)")

            # Extract capabilities
            capabilities = self.extract_capabilities_from_readme(readme)
            if capabilities:
                enriched['capabilities'] = capabilities
                print(f"    ✅ Found {len(capabilities)} capabilities")

            # Extract installation info
            install_info = self.extract_installation_info(readme)
            if install_info['commands']:
                enriched['installation_commands'] = install_info['commands'][:10]
                print(f"    ✅ Found {len(install_info['commands'])} installation commands")
            if install_info['runtime']:
                enriched['runtime'] = install_info['runtime']
                print(f"    ✅ Runtime: {install_info['runtime']}")
            if install_info['requirements']:
                enriched['requirements'] = install_info['requirements']
                print(f"    ✅ Requirements: {', '.join(install_info['requirements'])}")

            # Categorize
            categories = self.categorize_mcp(readme, server_data.get('description', ''))
            if categories:
                enriched['categories'] = categories
                print(f"    ✅ Categories: {', '.join(categories)}")

            # Store README excerpt
            enriched['readme_excerpt'] = readme[:1000]

        # Fetch GitHub API data
        time.sleep(GITHUB_API_DELAY)
        api_data = self.fetch_github_api_data(owner, repo)
        if api_data:
            print(f"    ✅ GitHub API data fetched")

            enriched['github_metadata'] = {
                'language': api_data.get('language'),
                'license': api_data.get('license', {}).get('name') if api_data.get('license') else None,
                'forks': api_data.get('forks_count', 0),
                'open_issues': api_data.get('open_issues_count', 0),
                'watchers': api_data.get('watchers_count', 0),
                'last_pushed': api_data.get('pushed_at'),
                'created_at': api_data.get('created_at'),
                'topics': api_data.get('topics', []),
                'has_wiki': api_data.get('has_wiki', False),
                'has_pages': api_data.get('has_pages', False),
            }

            # Detect language
            language = self.detect_language(readme or '', api_data)
            if language:
                enriched['language'] = language
                print(f"    ✅ Language: {language}")

        # Calculate quality score
        quality_score = self.calculate_quality_score(server_data, api_data)
        enriched['quality_score'] = quality_score
        print(f"    ✅ Quality Score: {quality_score}/100")

        return enriched

    def enrich_server(self, file_path: Path) -> bool:
        """Enrich a single server with GitHub data"""
        try:
            # Read existing data
            with open(file_path, 'r', encoding='utf-8') as f:
                server_data = json.load(f)

            # Check if already enriched recently (skip if enriched in last 7 days)
            github_enriched_at = server_data.get('metadata', {}).get('github_enriched_at')
            if github_enriched_at:
                enriched_date = datetime.fromisoformat(github_enriched_at)
                days_since = (datetime.now() - enriched_date).days
                if days_since < 7:
                    print(f"  ⏭️  Skipping (already enriched {days_since} days ago)")
                    self.skipped_count += 1
                    return False

            # Check if has source_url
            if not server_data.get('source_url'):
                print(f"  ⏭️  Skipping (no source_url)")
                self.skipped_count += 1
                return False

            # Enrich from GitHub
            enriched = self.enrich_from_github(server_data)

            if not enriched:
                print(f"  ❌ No GitHub data found")
                self.error_count += 1
                return False

            # Merge enriched data
            if 'metadata' not in server_data:
                server_data['metadata'] = {}

            # Add all enriched fields
            for key, value in enriched.items():
                if key == 'github_metadata':
                    server_data['metadata'].update(value)
                elif key == 'capabilities':
                    server_data['capabilities'] = value
                elif key == 'categories':
                    # Merge with existing categories
                    existing = set(server_data.get('categories', []))
                    existing.update(value)
                    server_data['categories'] = list(existing)
                elif key == 'installation_commands':
                    server_data['metadata']['installation_commands'] = value
                elif key == 'runtime':
                    server_data['runtime'] = value
                elif key == 'requirements':
                    server_data['requirements'] = value
                elif key == 'language':
                    server_data['language'] = value
                elif key == 'quality_score':
                    server_data['quality_score'] = value
                elif key == 'readme_excerpt':
                    server_data['metadata']['readme_excerpt'] = value

            # Update timestamp
            server_data['metadata']['github_enriched_at'] = datetime.now().isoformat()

            # Save back
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(server_data, f, indent=2, ensure_ascii=False)

            self.enriched_count += 1
            print(f"  ✅ GitHub enrichment successful!")
            return True

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.error_count += 1
            return False

    def run(self, test_mode: bool = False, limit: Optional[int] = None, classification: Optional[str] = None):
        """Run GitHub enrichment on all servers"""
        base_dir = Path(__file__).parent.parent.parent
        data_dir = base_dir / 'data' / 'servers'

        # Collect all server files
        server_files = []
        for classification_dir in ['official', 'reference', 'community']:
            if classification and classification_dir != classification:
                continue

            class_path = data_dir / classification_dir
            if class_path.exists():
                server_files.extend(list(class_path.glob('*.json')))

        total_files = len(server_files)

        if test_mode:
            server_files = server_files[:3]
            print(f"🧪 TEST MODE: Processing only {len(server_files)} servers\n")

        if limit:
            server_files = server_files[:limit]

        print(f"🚀 Starting GitHub enrichment for {len(server_files)} servers (total: {total_files})\n")

        for i, file_path in enumerate(server_files, 1):
            print(f"\n[{i}/{len(server_files)}] Processing: {file_path.name}")

            self.enrich_server(file_path)

            # Rate limiting
            if i < len(server_files):
                time.sleep(self.delay)

        # Print summary
        print(f"\n{'='*80}")
        print(f"✅ GitHub Enrichment Complete!")
        print(f"{'='*80}")
        print(f"Total processed: {len(server_files)}")
        print(f"Enriched: {self.enriched_count}")
        print(f"Skipped: {self.skipped_count}")
        print(f"Errors: {self.error_count}")
        print(f"GitHub API requests used: {github_api_requests}/{GITHUB_API_RATE_LIMIT}")

def main():
    parser = argparse.ArgumentParser(description='Enrich MCP servers with GitHub data')
    parser.add_argument('--test', action='store_true', help='Test mode (only 3 servers)')
    parser.add_argument('--limit', type=int, help='Limit number of servers to enrich')
    parser.add_argument('--classification', choices=['official', 'reference', 'community'],
                        help='Only enrich servers of this classification')
    parser.add_argument('--delay', type=float, default=DELAY_BETWEEN_REQUESTS,
                        help=f'Delay between requests (default: {DELAY_BETWEEN_REQUESTS}s)')

    args = parser.parse_args()

    enricher = GitHubEnricher(delay=args.delay)
    enricher.run(test_mode=args.test, limit=args.limit, classification=args.classification)

if __name__ == '__main__':
    main()
