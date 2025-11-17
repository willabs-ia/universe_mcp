#!/usr/bin/env python3
"""
Universe MCP - Index Generator
Generates search indexes and statistics
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict, Counter
from datetime import datetime


PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INDEX_DIR = PROJECT_ROOT / "indexes"


class IndexGenerator:
    """Generates indexes for MCP data"""

    def __init__(self):
        self.servers = []
        self.clients = []
        self.usecases = []

    def load_all_servers(self) -> List[Dict]:
        """Load all server JSON files"""
        servers = []
        server_dir = DATA_DIR / "servers"
        if server_dir.exists():
            for json_file in server_dir.glob("**/*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        servers.append(json.load(f))
                except Exception as e:
                    print(f"⚠️  Error loading {json_file}: {e}")
        return servers

    def load_all_clients(self) -> List[Dict]:
        """Load all client JSON files"""
        clients = []
        client_dir = DATA_DIR / "clients"
        if client_dir.exists():
            for json_file in client_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        clients.append(json.load(f))
                except Exception as e:
                    print(f"⚠️  Error loading {json_file}: {e}")
        return clients

    def load_all_usecases(self) -> List[Dict]:
        """Load all use case JSON files"""
        usecases = []
        usecase_dir = DATA_DIR / "use-cases"
        if usecase_dir.exists():
            for json_file in usecase_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        usecases.append(json.load(f))
                except Exception as e:
                    print(f"⚠️  Error loading {json_file}: {e}")
        return usecases

    def generate_server_indexes(self) -> Dict:
        """Generate server-specific indexes"""
        # All servers index
        all_servers = {
            'total': len(self.servers),
            'generated_at': datetime.now().isoformat(),
            'servers': self.servers
        }

        # By classification
        by_classification = defaultdict(list)
        for server in self.servers:
            classification = server.get('classification', 'community')
            by_classification[classification].append(server)

        # By provider
        by_provider = defaultdict(list)
        for server in self.servers:
            provider = server.get('provider', 'Unknown')
            if provider:
                by_provider[provider].append(server)

        # By category
        by_category = defaultdict(list)
        for server in self.servers:
            for category in server.get('categories', []):
                by_category[category].append(server)

        return {
            'all': all_servers,
            'by_classification': dict(by_classification),
            'by_provider': dict(by_provider),
            'by_category': dict(by_category)
        }

    def generate_statistics(self) -> Dict:
        """Generate statistics about the data"""
        # Server stats
        server_classifications = Counter(
            s.get('classification', 'community') for s in self.servers
        )
        server_providers = Counter(
            s.get('provider', 'Unknown') for s in self.servers if s.get('provider')
        )

        # Extract all categories
        all_categories = []
        for server in self.servers:
            all_categories.extend(server.get('categories', []))
        category_counts = Counter(all_categories)

        stats = {
            'generated_at': datetime.now().isoformat(),
            'totals': {
                'servers': len(self.servers),
                'clients': len(self.clients),
                'use_cases': len(self.usecases)
            },
            'servers': {
                'by_classification': dict(server_classifications),
                'top_providers': dict(server_providers.most_common(20)),
                'top_categories': dict(category_counts.most_common(20)),
                'with_description': sum(1 for s in self.servers if s.get('description')),
                'with_metrics': sum(1 for s in self.servers if s.get('weekly_metric'))
            },
            'clients': {
                'total': len(self.clients)
            },
            'use_cases': {
                'total': len(self.usecases)
            }
        }

        return stats

    def save_index(self, filename: str, data: Dict):
        """Save an index file"""
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        file_path = INDEX_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Generated {filename}")

    def run(self) -> Dict:
        """Generate all indexes"""
        print("=" * 80)
        print("📇 UNIVERSE MCP - Index Generation")
        print("=" * 80)

        # Load all data
        print("\n📂 Loading data...")
        self.servers = self.load_all_servers()
        self.clients = self.load_all_clients()
        self.usecases = self.load_all_usecases()

        print(f"  📦 Loaded {len(self.servers)} servers")
        print(f"  📦 Loaded {len(self.clients)} clients")
        print(f"  📦 Loaded {len(self.usecases)} use cases")

        # Generate indexes
        print("\n📇 Generating indexes...")

        # Server indexes
        server_indexes = self.generate_server_indexes()
        self.save_index('all-servers.json', server_indexes['all'])
        self.save_index('servers-by-classification.json', {
            'generated_at': datetime.now().isoformat(),
            'classifications': server_indexes['by_classification']
        })
        self.save_index('servers-by-provider.json', {
            'generated_at': datetime.now().isoformat(),
            'providers': server_indexes['by_provider']
        })
        if server_indexes['by_category']:
            self.save_index('servers-by-category.json', {
                'generated_at': datetime.now().isoformat(),
                'categories': server_indexes['by_category']
            })

        # Client index
        self.save_index('all-clients.json', {
            'total': len(self.clients),
            'generated_at': datetime.now().isoformat(),
            'clients': self.clients
        })

        # Use case index
        self.save_index('all-usecases.json', {
            'total': len(self.usecases),
            'generated_at': datetime.now().isoformat(),
            'use_cases': self.usecases
        })

        # Statistics
        print("\n📊 Generating statistics...")
        stats = self.generate_statistics()
        self.save_index('statistics.json', stats)

        # Summary
        print("\n" + "=" * 80)
        print("📊 INDEX GENERATION SUMMARY")
        print("=" * 80)
        print(f"Total servers indexed: {len(self.servers)}")
        print(f"Total clients indexed: {len(self.clients)}")
        print(f"Total use cases indexed: {len(self.usecases)}")
        print(f"Indexes saved to: {INDEX_DIR}")
        print("=" * 80)

        return stats


def main():
    """Main entry point"""
    generator = IndexGenerator()
    generator.run()


if __name__ == '__main__':
    main()
