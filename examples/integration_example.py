#!/usr/bin/env python3
"""
Example: Integration with Your Application

This example shows how to integrate Universe MCP data
into your own application or tool.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class UniverseMCP:
    """
    Simple wrapper class for Universe MCP data.
    Use this in your application to access MCP server data.
    """

    def __init__(self, repo_path: str = "."):
        """
        Initialize with path to Universe MCP repository.

        Args:
            repo_path: Path to universe_mcp repository
        """
        self.repo_path = Path(repo_path)
        self.index_dir = self.repo_path / "indexes"
        self.data_dir = self.repo_path / "data"

        # Load indexes
        self._load_indexes()

    def _load_indexes(self):
        """Load all index files"""
        with open(self.index_dir / "all-servers.json") as f:
            self.all_servers = json.load(f)

        with open(self.index_dir / "statistics.json") as f:
            self.stats = json.load(f)

        try:
            with open(self.index_dir / "servers-by-classification.json") as f:
                self.by_classification = json.load(f)
        except FileNotFoundError:
            self.by_classification = {}

        try:
            with open(self.index_dir / "servers-by-provider.json") as f:
                self.by_provider = json.load(f)
        except FileNotFoundError:
            self.by_provider = {}

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for servers matching query.

        Args:
            query: Search term
            max_results: Maximum number of results

        Returns:
            List of matching servers
        """
        query_lower = query.lower()
        results = []

        for server in self.all_servers['servers']:
            if (query_lower in server.get('name', '').lower() or
                query_lower in server.get('description', '').lower() or
                query_lower in server.get('provider', '').lower()):
                results.append(server)

                if len(results) >= max_results:
                    break

        return results

    def get_official_servers(self) -> List[Dict]:
        """Get all official MCP servers"""
        return self.by_classification.get('classifications', {}).get('official', [])

    def get_by_provider(self, provider: str) -> List[Dict]:
        """Get all servers by specific provider"""
        return self.by_provider.get('providers', {}).get(provider, [])

    def get_statistics(self) -> Dict:
        """Get ecosystem statistics"""
        return self.stats

    def recommend_servers(self, task: str) -> List[Dict]:
        """
        Recommend servers for a specific task.

        Args:
            task: Description of the task

        Returns:
            List of recommended servers
        """
        # Simple keyword matching (can be enhanced with ML)
        keywords = task.lower().split()
        results = []

        for server in self.all_servers['servers']:
            score = 0
            server_text = (
                server.get('name', '') + ' ' +
                server.get('description', '') + ' ' +
                ' '.join(server.get('categories', []))
            ).lower()

            for keyword in keywords:
                if keyword in server_text:
                    score += 1

            if score > 0:
                results.append((score, server))

        # Sort by score and return top results
        results.sort(key=lambda x: x[0], reverse=True)
        return [server for score, server in results[:5]]


# Example usage
def example_usage():
    """Demonstrate usage of UniverseMCP class"""

    # Initialize (assumes you're running from universe_mcp directory)
    mcp = UniverseMCP()

    print("=" * 60)
    print("INTEGRATION EXAMPLE")
    print("=" * 60)
    print()

    # 1. Search for servers
    print("1. Search for 'database' servers:")
    results = mcp.search("database", max_results=3)
    for server in results:
        print(f"   - {server['name']}")
    print()

    # 2. Get official servers
    print("2. Get official servers:")
    official = mcp.get_official_servers()
    print(f"   Found {len(official)} official servers")
    for server in official[:3]:
        print(f"   - {server['name']}")
    print()

    # 3. Get statistics
    print("3. Ecosystem statistics:")
    stats = mcp.get_statistics()
    print(f"   Total servers: {stats['totals']['servers']}")
    print(f"   Total clients: {stats['totals']['clients']}")
    print()

    # 4. Recommend servers for a task
    print("4. Recommend servers for task:")
    task = "I need to connect to a PostgreSQL database"
    recommendations = mcp.recommend_servers(task)
    print(f"   Task: {task}")
    print(f"   Recommendations:")
    for server in recommendations:
        print(f"   - {server['name']}")
        print(f"     {server.get('description', '')[:60]}...")
    print()

    # 5. Get servers by provider
    print("5. Servers by provider 'Anthropic':")
    anthropic_servers = mcp.get_by_provider('Anthropic')
    print(f"   Found {len(anthropic_servers)} servers")
    for server in anthropic_servers[:3]:
        print(f"   - {server['name']}")


if __name__ == '__main__':
    example_usage()
