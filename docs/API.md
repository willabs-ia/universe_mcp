# 📡 API Documentation

Complete data structure reference for Universe MCP.

## Data Schemas

### Server Schema

**Location**: `schemas/server.schema.json`

```typescript
interface Server {
  // Required fields
  id: string;              // Unique slug (e.g., "postgres-mcp")
  name: string;            // Display name
  url: string;             // PulseMCP page URL
  scraped_at: string;      // ISO 8601 timestamp

  // Optional fields
  provider?: string;       // Organization/author
  description?: string;    // Brief description
  classification?: "official" | "reference" | "community";

  weekly_metric?: {
    type: "downloads" | "visitors";
    value: number;
  };

  release_date?: string;   // YYYY-MM-DD
  source_url?: string;     // GitHub/source URL
  categories?: string[];   // Category tags
  tags?: string[];         // Additional tags
  last_updated?: string;   // ISO 8601 timestamp

  metadata?: {
    author?: string;
    license?: string;
    version?: string;
    documentation_url?: string;
  };
}
```

### Client Schema

**Location**: `schemas/client.schema.json`

```typescript
interface Client {
  // Required fields
  id: string;
  name: string;
  url: string;
  scraped_at: string;

  // Optional fields
  provider?: string;
  description?: string;
  source_url?: string;
  platforms?: ("web" | "desktop" | "mobile" | "cli" | "other")[];
  categories?: string[];
}
```

### Use Case Schema

**Location**: `schemas/usecase.schema.json`

```typescript
interface UseCase {
  // Required fields
  id: string;
  title: string;
  url: string;
  scraped_at: string;

  // Optional fields
  description?: string;
  servers_used?: string[];   // Server IDs referenced
  clients_used?: string[];   // Client IDs referenced
  categories?: string[];
}
```

## Index Files

All indexes are located in `/indexes/` and updated daily.

### All Servers

**File**: `indexes/all-servers.json`

```typescript
{
  total: number;
  generated_at: string;  // ISO 8601
  servers: Server[];
}
```

### Servers by Classification

**File**: `indexes/servers-by-classification.json`

```typescript
{
  generated_at: string;
  classifications: {
    official: Server[];
    reference: Server[];
    community: Server[];
  };
}
```

### Servers by Provider

**File**: `indexes/servers-by-provider.json`

```typescript
{
  generated_at: string;
  providers: {
    [providerName: string]: Server[];
  };
}
```

### Servers by Category

**File**: `indexes/servers-by-category.json`

```typescript
{
  generated_at: string;
  categories: {
    [categoryName: string]: Server[];
  };
}
```

### Statistics

**File**: `indexes/statistics.json`

```typescript
{
  generated_at: string;
  totals: {
    servers: number;
    clients: number;
    use_cases: number;
  };
  servers: {
    by_classification: {
      [classification: string]: number;
    };
    top_providers: {
      [provider: string]: number;
    };
    top_categories: {
      [category: string]: number;
    };
    with_description: number;
    with_metrics: number;
  };
  clients: {
    total: number;
  };
  use_cases: {
    total: number;
  };
}
```

## File Organization

```
universe_mcp/
├── data/
│   ├── servers/
│   │   ├── official/
│   │   │   └── {server-id}.json
│   │   ├── reference/
│   │   │   └── {server-id}.json
│   │   └── community/
│   │       └── {server-id}.json
│   ├── clients/
│   │   └── {client-id}.json
│   └── use-cases/
│       └── {usecase-id}.json
└── indexes/
    ├── all-servers.json
    ├── all-clients.json
    ├── all-usecases.json
    ├── servers-by-classification.json
    ├── servers-by-provider.json
    ├── servers-by-category.json
    └── statistics.json
```

## Query Examples

### Get All Official Servers

```python
import json

with open('indexes/servers-by-classification.json') as f:
    data = json.load(f)
    official_servers = data['classifications']['official']
```

### Get Server by ID

```python
from pathlib import Path
import json

def get_server(server_id: str, classification: str = 'community'):
    file_path = Path(f'data/servers/{classification}/{server_id}.json')
    if file_path.exists():
        with open(file_path) as f:
            return json.load(f)
    return None

server = get_server('postgres-mcp', 'official')
```

### Search Servers

```python
def search(query: str):
    with open('indexes/all-servers.json') as f:
        all_servers = json.load(f)['servers']

    results = []
    query_lower = query.lower()

    for server in all_servers:
        if (query_lower in server.get('name', '').lower() or
            query_lower in server.get('description', '').lower()):
            results.append(server)

    return results
```

### Get Statistics

```python
with open('indexes/statistics.json') as f:
    stats = json.load(f)
    print(f"Total servers: {stats['totals']['servers']}")
    print(f"Official: {stats['servers']['by_classification']['official']}")
    print(f"Community: {stats['servers']['by_classification']['community']}")
```

## Validation

All data files conform to JSON Schema definitions in `/schemas/`.

Validate your data:

```bash
python scripts/validators/validate_data.py
```

## Update Frequency

- **Automatic**: Daily at 3 AM UTC via GitHub Actions
- **Manual**: Run `python scripts/update.py`

## Data Freshness

Check the `generated_at` field in any index file:

```python
import json
from datetime import datetime

with open('indexes/statistics.json') as f:
    stats = json.load(f)
    last_update = datetime.fromisoformat(stats['generated_at'])
    print(f"Data last updated: {last_update}")
```
