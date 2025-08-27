# Agentic SAS → Risk (CLI, Ubuntu, no localhost/UI)
See README in previous message for usage. This repository contains:
- `agents/sas_agent.py` → uses **Ollama CLI** to generate SAS-like ECL inputs
- `agents/risk_agent.py` → consumes those inputs and computes IFRS-9 ECL
- `providers/ollama_cli.py` → minimal wrapper around `ollama generate --json`
- `prompts/sas_prompt.txt` → prompt template for structured JSON output
- `main.py` → CLI orchestrator
- `config.yaml` → default configuration
