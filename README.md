# Blockchain Security Monitor & Guardian Agent (WDK Edition)

**Tether Hackathon Galactica Submission**

A robust, production-grade Python framework that combines **AI Risk Analysis** with **Tether WDK** execution capabilities. This agent doesn't just watch; it **protects and acts**.

## Features

- **🛡️ AI Guardian Agent (NEW)**: Autonomous agent that holds funds and executes transactions via **Tether WDK**, but _only_ after passing rigorous AI & Logic security checks.
- **🔌 WDK Integration**: Direct implementation of Wallet Development Kit primitives for wallet creation, signing, and transaction management.
- **🧠 Dual-Engine Risk Control**:
  - **Deterministic**: Mathematical checks (e.g., Allowance > Balance).
  - **Probabilistic**: LLM-based analysis (DeepSeek/Gemini) to detect phishing patterns.
- **🚀 Production Ready**: Configurable via `.env`, type-safe settings, and modular architecture.
- **🤖 AI-Native Development**: Includes `AGENTS.md` and `MCP_CONFIG.json` for seamless integration with AI coding assistants (Trae, Cursor) via Tether's official WDK MCP Server.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set your API keys.

```bash
cp .env.example .env
```

### 3. Usage Modes

#### Mode A: Passive Monitor (Scanner)

Check a wallet's allowance for a specific spender.

```bash
python main.py --mode monitor --owner <WALLET_ADDRESS> --spender <SPENDER_ADDRESS>
```

#### Mode B: Active Guardian (WDK Agent) [HACKATHON TRACK]

Instruct the agent to securely transfer funds using **WDK primitives**. The agent will **refuse** to sign if the destination is suspicious.

```bash
# Example: Safe Transfer
python main.py --mode guardian --action transfer --to 0xSafeAddress... --amount 100

# Example: The Agent will BLOCK this if it detects a phishing address
python main.py --mode guardian --action transfer --to 0xPhishingAddress... --amount 100
```

## Architecture

- `core/wdk_client.py`: **[HACKATHON] Tether WDK Interface** (Wallet creation, Signing, Sending).
- `agents/guardian_agent.py`: **[HACKATHON] The Brain + Hands**. Integrates risk analysis with WDK execution.
- `agents/allowance_monitor.py`: Logic-based risk engine.
- `agents/ai_analyzer.py`: LLM-based security auditor.

## Hackathon Track Compliance: "Build Agents with Tether WDK"

This project fulfills the track requirements by:

1.  **Direct WDK Usage**: Implemented in `core/wdk_client.py`.
2.  **Autonomous Management**: `GuardianAgent` manages funds and makes transfer decisions independently.
3.  **Safety First**: The agent's primary directive is security, leveraging OpenClaw-style reasoning before any WDK action.
4.  **AI-Native Workflow**: Project structure optimized for AI pair programming with `AGENTS.md` (WDK Context) and `MCP_CONFIG.json` (Tether Documentation Server).

## Roadmap

- [ ] **Q2 2026**: Integration of Multi-chain Automated Scanning (Arbitrum, Base).
- [ ] **Q3 2026**: Autonomous "Revoke-on-Risk" action trigger.

## 📫 Contact

- **Discord**: guaguagua_59889
- **Email**: lsnirvana@gmail.com
- **DoraHacks BUIDL**: [View Project](https://dorahacks.io/buidl/40387)
