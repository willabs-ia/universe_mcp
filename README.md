# 🌌 Universe MCP

> **The world's largest, most comprehensive MCP (Model Context Protocol) library**

A fully organized, searchable, and open database of all MCP servers, clients, and use cases, automatically scraped and updated from [PulseMCP.com](https://www.pulsemcp.com).

[![Auto Update](https://github.com/willabs-ia/universe_mcp/actions/workflows/auto-update.yml/badge.svg)](https://github.com/willabs-ia/universe_mcp/actions/workflows/auto-update.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📊 Current Stats

- **6,488+** MCP Servers cataloged
- **3** Data categories (Servers, Clients, Use Cases)
- **Daily** automatic updates
- **100%** open source and free

---

## 🎯 What is Universe MCP?

Universe MCP is the definitive resource for discovering and integrating Model Context Protocol (MCP) servers and tools. We automatically scrape, organize, and index all available MCP resources to create:

- ✅ The most complete MCP server directory
- ✅ Searchable and categorized data
- ✅ JSON-based data for easy integration
- ✅ Daily automatic updates
- ✅ Compatible with Claude, Perplexity, and all LLM tools
- ✅ Ready for MCP server integration

---

## 🚀 Quick Start

### Clone the Repository

```bash
git clone https://github.com/willabs-ia/universe_mcp.git
cd universe_mcp
```

### Browse Data

```bash
# View all servers
cat indexes/all-servers.json | jq '.servers[] | {name, provider, description}' | head -20

# View statistics
cat indexes/statistics.json | jq '.totals'

# Find servers by classification
cat indexes/servers-by-classification.json | jq '.classifications.official[] | .name'
```

### Search for Specific Servers

```python
import json

# Load all servers
with open('indexes/all-servers.json') as f:
    data = json.load(f)

# Search for database servers
database_servers = [
    s for s in data['servers']
    if 'database' in s.get('description', '').lower()
]

print(f"Found {len(database_servers)} database-related servers")
```

---

## 📁 Repository Structure

```
universe_mcp/
├── data/                          # Raw scraped data
│   ├── servers/
│   │   ├── official/             # Official MCP servers
│   │   ├── reference/            # Reference implementations
│   │   └── community/            # Community servers
│   ├── clients/                  # MCP client applications
│   └── use-cases/                # Use case examples
├── indexes/                       # Pre-generated search indexes
│   ├── all-servers.json          # Complete server list
│   ├── all-clients.json          # Complete client list
│   ├── all-usecases.json         # Complete use case list
│   ├── servers-by-classification.json
│   ├── servers-by-provider.json
│   ├── servers-by-category.json
│   └── statistics.json           # Statistics and metrics
├── schemas/                       # JSON Schema definitions
│   ├── server.schema.json
│   ├── client.schema.json
│   └── usecase.schema.json
├── scripts/                       # Automation scripts
│   ├── scrapers/                 # Web scrapers
│   ├── validators/               # Data validation
│   ├── indexers/                 # Index generators
│   └── update.py                 # Main update script
├── docs/                          # Documentation
│   ├── INTEGRATION.md            # Integration guide
│   └── API.md                    # API reference
└── DIARIO_PROJETO.md             # Project diary (development log)
```

---

## 🔍 Usage Examples

### Find All Official Servers

```python
import json

with open('indexes/servers-by-classification.json') as f:
    data = json.load(f)
    official = data['classifications']['official']

for server in official:
    print(f"{server['name']} - {server['provider']}")
```

### Get Top Providers

```python
import json

with open('indexes/statistics.json') as f:
    stats = json.load(f)
    top_providers = stats['servers']['top_providers']

for provider, count in list(top_providers.items())[:10]:
    print(f"{provider}: {count} servers")
```

### Search by Category

```python
import json

with open('indexes/servers-by-category.json') as f:
    data = json.load(f)

# List all categories
print("Available categories:", list(data['categories'].keys()))

# Get servers in a specific category
database_servers = data['categories'].get('database', [])
```

---

## 🛠️ Development

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Run Scrapers

```bash
# Test mode (scrape only first 2 pages)
python scripts/scrapers/scrape_servers.py --test

# Full scrape
python scripts/scrapers/scrape_servers.py

# Resume from checkpoint
python scripts/scrapers/scrape_servers.py --resume

# Scrape specific page range
python scripts/scrapers/scrape_servers.py --start 10 --end 20
```

### Validate Data

```bash
python scripts/validators/validate_data.py
```

### Generate Indexes

```bash
python scripts/indexers/generate_indexes.py
```

### Complete Update (All in One)

```bash
# Full update: scrape + validate + index
python scripts/update.py

# Test mode
python scripts/update.py --test

# Update only servers
python scripts/update.py --servers-only
```

---

## 🔄 Automatic Updates

This repository automatically updates daily at 3 AM UTC via GitHub Actions.

The workflow:
1. Scrapes latest data from PulseMCP.com
2. Validates all data against schemas
3. Generates updated indexes
4. Commits and pushes changes

See [`.github/workflows/auto-update.yml`](.github/workflows/auto-update.yml) for details.

---

## 📚 Documentation

- **[Integration Guide](docs/INTEGRATION.md)** - How to integrate Universe MCP with your tools
- **[API Reference](docs/API.md)** - Complete data structure reference
- **[Project Diary](DIARIO_PROJETO.md)** - Development log and decisions

---

## 🔌 MCP Server Integration (Coming Soon)

Use Universe MCP as an MCP server itself:

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

This will allow AI agents to query the database directly with natural language.

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Report Issues
- Found incorrect data? [Open an issue](https://github.com/willabs-ia/universe_mcp/issues)
- Have suggestions? [Start a discussion](https://github.com/willabs-ia/universe_mcp/discussions)

### Submit Data
1. Fork the repository
2. Add/update JSON files in `/data/`
3. Run validation: `python scripts/validators/validate_data.py`
4. Submit a pull request

### Improve Scripts
- Enhance scrapers for better data extraction
- Add new indexing strategies
- Improve documentation

---

## 📊 Data Quality

- ✅ All data validated against JSON Schema
- ✅ Automatic validation in CI/CD
- ✅ Daily freshness checks
- ✅ Source tracking (PulseMCP URLs)
- ✅ Timestamp tracking (`scraped_at`, `last_updated`)

---

## 🌟 Use Cases

- **LLM Tool Discovery**: Help AI agents find the right MCP server for a task
- **Developer Research**: Explore available MCP integrations
- **Ecosystem Analysis**: Understand MCP adoption and trends
- **Automated Integration**: Build tools that auto-discover MCP capabilities
- **Documentation**: Reference for MCP learning resources

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

Feel free to use, modify, and distribute this data for any purpose.

---

## 🙏 Acknowledgments

- **PulseMCP.com** - Source of MCP data
- **Anthropic** - Creators of the Model Context Protocol
- **Community** - All MCP server and client developers

---

## 🔗 Links

- **PulseMCP**: https://www.pulsemcp.com
- **MCP Specification**: https://github.com/modelcontextprotocol
- **Official MCP Registry**: https://github.com/modelcontextprotocol/servers

---

## 📞 Contact

- **Issues**: https://github.com/willabs-ia/universe_mcp/issues
- **Discussions**: https://github.com/willabs-ia/universe_mcp/discussions
- **Author**: [@willabs-ia](https://github.com/willabs-ia)

---

<div align="center">

**Made with ❤️ for the MCP community**

[⭐ Star this repo](https://github.com/willabs-ia/universe_mcp) | [🐛 Report Bug](https://github.com/willabs-ia/universe_mcp/issues) | [💡 Request Feature](https://github.com/willabs-ia/universe_mcp/issues)

</div>