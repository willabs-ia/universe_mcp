# Universe MCP - Examples

This directory contains example scripts demonstrating how to use Universe MCP data.

## Available Examples

### 1. `search_servers.py`
Demonstrates various search and filter operations:
- Keyword search
- Filter by classification (official/reference/community)
- Search by provider
- Search by category
- Custom filtering

**Run it:**
```bash
python examples/search_servers.py
```

### 2. `integration_example.py`
Shows how to integrate Universe MCP into your application:
- Create a wrapper class
- Search functionality
- Get official servers
- Recommendation system
- Statistics access

**Run it:**
```bash
python examples/integration_example.py
```

## Prerequisites

Make sure you have generated the indexes first:
```bash
python scripts/indexers/generate_indexes.py
```

## Using in Your Project

### Option 1: Direct JSON Access
```python
import json

with open('indexes/all-servers.json') as f:
    data = json.load(f)
    servers = data['servers']
```

### Option 2: Use the Wrapper Class
```python
from examples.integration_example import UniverseMCP

mcp = UniverseMCP()
results = mcp.search("database")
```

### Option 3: Command-line Search
```bash
python scripts/search.py "keyword"
python scripts/search.py --classification official
python scripts/search.py --provider "Anthropic"
```

## Next Steps

- Browse the source code to understand the data structure
- Modify examples for your specific use case
- Build your own tools on top of Universe MCP
- Contribute your examples back to the project!

## Need Help?

- Check the [Integration Guide](../docs/INTEGRATION.md)
- Read the [API Reference](../docs/API.md)
- Open an [issue](https://github.com/willabs-ia/universe_mcp/issues)
