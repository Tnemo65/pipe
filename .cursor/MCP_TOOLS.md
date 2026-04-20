# MCP & Plugins for StreamDQ

---

## Cursor Plugins (Enabled)

### paper-desktop
- `/code-to-design`: Generate design from codebase
- `/design-to-code`: Generate code from design

### parallel
- Parallel task execution
- Concurrent agent workflows

### astronomer-data
- Airflow/data pipeline orchestration
- Data quality checks

### dbt
- Data transformation
- SQL-based analytics engineering

---

## Recommended MCPs by Category

### 1. Streaming & Messaging

| MCP | Purpose | Status |
|-----|---------|--------|
| **Kafka MCP** | Produce/consume streaming events | Needed |
| **Confluent Kafka** | Confluent Cloud integration | Future |

### 2. Analytics & Storage

| MCP | Purpose | Status |
|-----|---------|--------|
| **DuckDB MCP** | Fast analytical queries on violations | Needed |
| **PostgreSQL MCP** | Production violation storage | Needed |
| **SQLite** | Demo violation storage (built-in) | Ready |

### 3. Observability

| MCP | Purpose | Status |
|-----|---------|--------|
| **Prometheus MCP** | Metrics collection | Needed |
| **Grafana MCP** | Dashboards & alerting | Needed |

### 4. Infrastructure

| MCP | Purpose | Status |
|-----|---------|--------|
| **Docker MCP** | Container orchestration | Optional |
| **Airflow MCP** | Workflow scheduling (via astronomer-data) | Ready |

---

## Priority MCPs to Add

### High Priority (Required for MVP)

```json
// c:\Users\Admin\.cursor\mcp.json
{
  "mcpServers": {
    "kafka": {
      "command": "mcp-kafka"
    },
    "duckdb": {
      "command": "duckdb-mcp-server",
      "args": ["--db-path", "d:\\dtl\\pipeline_real\\data\\streamdq_violations.duckdb"]
    }
  }
}
```

> **Note:** Postgres MCP requires Docker running with `docker-compose up -d postgres`. It needs `--host`, `--database`, `--user`, `--password` arguments.

### Medium Priority (Production)

```json
{
  "mcpServers": {
    "grafana-mcp": {
      "command": "uvx",
      "args": ["mcp-grafana"]
    },
    "prometheus-mcp": {
      "command": "uvx",
      "args": ["mcp-prometheus"]
    }
  }
}
```

---

## StreamDQ Architecture Summary

```
┌─────────────────────────────────────────────────────┐
│                  DATA SOURCES                        │
│  NYC Taxi (Parquet) → Kafka                         │
│  GTFS Malaysia → Kafka                              │
└──────────────────┬──────────────────────────────────┘
                   │ Kafka
                   ▼
┌─────────────────────────────────────────────────────┐
│              STREAMDQ ENGINE                         │
│  Syntactic → Semantic → Cross-Record                │
└──────────────────┬──────────────────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
   ┌─────────────┐   ┌──────────────┐
   │  SQLite/    │   │  Prometheus  │
   │  DuckDB     │   │  + Grafana   │
   │ (violations)│   │  (metrics)   │
   └─────────────┘   └──────────────┘
```

---

---

## Prerequisites

### Node.js (Required for npx-based MCPs)

Download from: https://nodejs.org/

```powershell
# After installing Node.js, verify:
node --version
npm --version
```

### Python Version Check

```bash
python --version  # Should show 3.11.x
```

---

## MCP Installation Commands

### DuckDB (pip)

```bash
pip install duckdb-mcp-server
```

Or more feature-rich (requires uv):
```bash
pip install uv
uvx mcp-server-motherduck
```

### Kafka (Python 3.11 compatible)

```bash
pip install mcp-kafka
mcp-kafka --help
```

### PostgreSQL (pip)

```bash
# Simple implementation (Python 3.10+)
pip install git+https://github.com/sajithdilshan/simple-postgres-mcp.git
```

Or clone and install:
```bash
git clone https://github.com/stuzero/pg-mcp-server.git
cd pg-mcp-server
pip install -e .
```

### Quick Install All (pip)

```bash
# Kafka
pip install mcp-kafka

# DuckDB
pip install duckdb-mcp-server

# PostgreSQL
pip install git+https://github.com/sajithdilshan/simple-postgres-mcp.git
```
