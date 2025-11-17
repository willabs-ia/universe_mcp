# 🔌 Integration Guide

How to integrate Universe MCP with your tools and agents.

## Overview

Universe MCP provides a comprehensive, searchable database of all MCP servers, clients, and use cases. The data is available in multiple formats optimized for different use cases.

## Data Access

### 1. Direct File Access

Clone the repository and access JSON files directly:

```bash
git clone https://github.com/willabs-ia/universe_mcp.git
cd universe_mcp
```

#### Server Data Structure

```bash
data/servers/
├── official/      # Official MCP servers
├── reference/     # Reference implementations
└── community/     # Community servers
```

Each server JSON contains:
```json
{
  "id": "server-slug",
  "name": "Server Name",
  "provider": "Organization",
  "description": "What this server does",
  "classification": "official|reference|community",
  "weekly_metric": {
    "type": "downloads|visitors",
    "value": 12345
  },
  "url": "https://pulsemcp.com/servers/...",
  "categories": ["category1", "category2"],
  "tags": ["tag1", "tag2"]
}
```

### 2. Using Indexes

Pre-generated indexes are available in `/indexes/`:

```python
import json

# Load all servers
with open('indexes/all-servers.json') as f:
    data = json.load(f)
    servers = data['servers']

# Load by classification
with open('indexes/servers-by-classification.json') as f:
    data = json.load(f)
    official = data['classifications']['official']
    community = data['classifications']['community']

# Load statistics
with open('indexes/statistics.json') as f:
    stats = json.load(f)
    print(f"Total servers: {stats['totals']['servers']}")
```

### 3. MCP Server Integration

Use Universe MCP as an MCP server itself (coming soon):

```json
{
  "mcpServers": {
    "universe-mcp": {
      "command": "npx",
      "args": ["-y", "@universe-mcp/server"]
    }
  }
}
```

This will allow AI agents to query the database directly.

## Search Patterns

### Find Servers by Category

```python
import json
from pathlib import Path

def find_by_category(category: str):
    with open('indexes/servers-by-category.json') as f:
        data = json.load(f)
        return data['categories'].get(category, [])

# Example
database_servers = find_by_category('database')
```

### Find Official Servers Only

```python
def get_official_servers():
    servers = []
    for json_file in Path('data/servers/official').glob('*.json'):
        with open(json_file) as f:
            servers.append(json.load(f))
    return servers
```

### Search by Keywords

```python
def search_servers(keyword: str):
    results = []
    with open('indexes/all-servers.json') as f:
        all_servers = json.load(f)['servers']

    keyword_lower = keyword.lower()
    for server in all_servers:
        if (keyword_lower in server.get('name', '').lower() or
            keyword_lower in server.get('description', '').lower() or
            keyword_lower in ' '.join(server.get('tags', [])).lower()):
            results.append(server)

    return results
```

## LLM Integration Examples

### Claude Desktop

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "universe-mcp": {
      "command": "python",
      "args": ["/path/to/universe_mcp/mcp_server.py"]
    }
  }
}
```

### Perplexity / Other LLMs

Reference the repository URL or clone locally and provide the path:

```
System prompt: You have access to the Universe MCP database at /path/to/universe_mcp/
Use the indexes in /indexes/ for fast lookups.
```

## API Patterns (Planned)

Future releases will include:

### REST API

```bash
GET /api/servers
GET /api/servers/{id}
GET /api/servers?classification=official
GET /api/servers?category=database
GET /api/search?q=postgres
```

### GraphQL API

```graphql
query {
  servers(classification: "official") {
    name
    description
    provider
    categories
  }
}
```

## Contributing Data

If you find missing or incorrect data:

1. Fork the repository
2. Update the JSON files in `/data/`
3. Run validation: `python scripts/validators/validate_data.py`
4. Submit a pull request

Or open an issue with the details.

## Rate Limits and Usage

- All data is freely available under MIT license
- No rate limits for local usage
- For large-scale integration, consider cloning the repo
- Data updates daily via GitHub Actions

## Support

- Issues: https://github.com/willabs-ia/universe_mcp/issues
- Discussions: https://github.com/willabs-ia/universe_mcp/discussions

## Examples

See `/examples/` directory for complete integration examples:
- Python integration
- Node.js integration
- MCP server implementation
- Search utilities
