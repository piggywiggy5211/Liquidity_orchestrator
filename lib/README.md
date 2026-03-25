# Shared Library

Common utilities and shared code for the Liquidity Orchestrator monorepo.

This package contains reusable components used across multiple applications in the workspace, including:

- Liquidity Orchestrator (main application for onramp/offramp operations)
- Mock Providers (testing infrastructure)

## Usage

Add as a workspace dependency in your `pyproject.toml`:

```toml
[project]
dependencies = [
    "lib",
]

[tool.uv.sources]
lib = { workspace = true }
```
