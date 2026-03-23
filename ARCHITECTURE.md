# 🏗️ Project Architecture & Design

This document details the architectural design of the **Security Monitor & Guardian Agent (WDK Edition)**. The system is designed as a **Cybernetic Organism** where traditional software logic (The Body) is enhanced by AI probabilistic reasoning (The Brain) and executes actions through secure cryptographic primitives (The Hands).

---

## 1. High-Level System Overview

The system operates in two distinct modes, sharing a common core infrastructure.

```ascii
+---------------------------------------------------------------+
|                      User / CLI Interface                     |
+------------------------------+--------------------------------+
                               |
                               v
+---------------------------------------------------------------+
|                        MAIN CONTROLLER                        |
|                  (Orchestrator & Mode Selector)               |
+--------------+-------------------------------+----------------+
               |                               |
      (Mode A: Monitor)               (Mode B: Guardian)
               |                               |
+--------------v---------------+    +----------v--------------------+
|   🛡️ SECURITY MONITOR AGENT  |    |    🤖 GUARDIAN AGENT (AI)     |
|   (Passive Auditor)          |    |    (Active WDK Executor)      |
+--------------+---------------+    +----------+----------+---------+
               |                               |          |
               v                               |          v
+--------------+---------------+    +----------v----------+---------+
|   🧠 AI RISK ANALYZER        |<---|   🔒 TETHER WDK CLIENT        |
|   (DeepSeek / Gemini)        |    |   (WalletManager & Account)   |
+--------------+---------------+    +----------+--------------------+
               |                               |
               v                               v
+---------------------------------------------------------------+
|                    BLOCKCHAIN NETWORK (EVM)                   |
|              (RPC / Smart Contracts / Mempool)                |
+---------------------------------------------------------------+
```

---

## 2. Component Breakdown

### 🧠 The Brain: AI & Logic Engine

Located in `agents/ai_analyzer.py` and `agents/allowance_monitor.py`.

- **Deterministic Logic**: Checks mathematical truths (e.g., "Is Allowance > Balance?", "Is Spender Contract Verified?").
- **Probabilistic AI**: Analyzes reputation, phishing patterns, and semantic context using LLMs.
- **Decision**: Fuses Logic + AI to produce a final `Risk Level` (LOW, MEDIUM, HIGH).

### ✋ The Hands: Tether WDK Integration

Located in `core/wdk_client.py`.

- **WalletManager**: The factory that manages keys and identities.
- **WalletAccount**: The actor that holds the private key (securely) and signs transactions.
- **Bridge Mode**: When `WDK_USE_TETHER_WDK=true`, Python calls `wdk_bridge/wdk_bridge.mjs`, which directly invokes official `@tetherto/wdk` and `@tetherto/wdk-wallet-evm`.
- **WDK Primitives**: Direct implementation of:
  - `create_wallet()`
  - `sign_message()`
  - `send_transaction()`

### 🤖 The Guardian: Agent Orchestrator

Located in `agents/guardian_agent.py`.

- **Responsibility**: Binds the "Brain" and "Hands" together.
- **Policy**: "Think before you Act".
- **Execution Modes**: Supports both single transfer (`run_transfer_task`) and autonomous batch planning (`run_autonomous_tasks`).
- **Workflow**:
  1. Receive high-level intent (e.g., "Transfer 50 USDT to Bob").
  2. Consult **The Brain** to validate Bob's address.
  3. If Risk > LOW, **ABORT**.
  4. If Risk == LOW, authorize **The Hands** to sign and broadcast.

### 🧭 Autonomous Planner: Safety-Constrained Batch Executor

Located in `agents/guardian_agent.py` (`run_autonomous_tasks`).

- **Input**: Candidate transfers (`to_address`, `amount`, `token_symbol`), plus optional `max_tasks` and `budget`.
- **Plan Strategy**: Valid candidates are sorted by amount (ascending) before execution.
- **Hard Constraints**:
  - **Execution Cap**: Stops successful execution after `max_tasks`.
  - **Budget Cap**: Blocks tasks that would push total executed amount over `budget`.
- **Safety Inheritance**: Each planned item still goes through the same transfer safety pipeline (`run_transfer_task`) before WDK execution.
- **Output Contract**: Returns structured summary (`planned_count`, `executed_count`, `blocked_count`, `error_count`, `executed_total`, `results`) for CLI/reporting and demos.

---

## 3. Sequence Diagram: Guardian Mode Execution

This flow demonstrates the **Safety-First** architecture required by the Hackathon.

```ascii
User                Guardian Agent           AI Brain              WDK Client           Blockchain
 |                        |                     |                      |                     |
 |---(Transfer 50 USDT)-->|                     |                      |                     |
 |                        |                     |                      |                     |
 |                        |---(Analyze Addr)--->|                      |                     |
 |                        |                     |                      |                     |
 |                        |<--(Risk: HIGH/LOW)--|                      |                     |
 |                        |                     |                      |                     |
 |           [Decision Point: Is Safe?]         |                      |                     |
 |                        |                     |                      |                     |
 |-------(If UNSAFE)----->X (BLOCK & REPORT)    |                      |                     |
 |                        |                     |                      |                     |
 |--------(If SAFE)--------------------------------------------------->|                     |
 |                        |                     |                      |----(Sign Tx)------->|
 |                        |                     |                      |                     |
 |                        |                     |                      |<---(Tx Hash)--------|
 |                        |<-------------------------------------------|                     |
 |                        |                     |                      |                     |
 |<----(Success Report)---|                     |                      |                     |
 v                        v                     v                      v                     v
```

---

## 4. Runtime Policy & CLI Control Surface

The main entry point (`main.py`) exposes runtime controls that directly influence Guardian behavior.

- **Action Routing**: `--action transfer|approve|autonomous`
- **Autonomous Candidate Input**: Repeatable `--candidate <to>:<amount>[:<asset>]`
- **Autonomous Safety Limits**:
  - `--max-autonomous-tasks`: Maximum successful transfers in one autonomous run
  - `--autonomous-budget`: Maximum cumulative transfer amount in one autonomous run
- **Policy Overrides**:
  - `--max-transfer-amount`
  - `--require-ai-approval` / `--no-require-ai-approval`
  - `--daily-total-limit`
  - `--daily-asset-limits`
  - `--allow-counterparty` (repeatable allowlist)

These controls let the same architecture operate in conservative production-style mode or permissive demo mode without changing source code.

---

## 5. Directory Structure & Key Files

```text
security_monitor/
├── agents/                 # AGENT LOGIC LAYER
│   ├── ai_analyzer.py      # AI Probabilistic Reasoning
│   ├── allowance_monitor.py# Deterministic Security Logic
│   └── guardian_agent.py   # [CORE] The Autonomous Agent Orchestrator
├── config/                 # CONFIGURATION LAYER
│   └── settings.py         # Environment & Constants
├── core/                   # INFRASTRUCTURE LAYER
│   ├── blockchain.py       # Web3.py / RPC Connection
│   └── wdk_client.py       # [CORE] Tether WDK Implementation (WalletManager)
├── wdk_bridge/             # OFFICIAL WDK BRIDGE LAYER
│   ├── package.json        # @tetherto SDK dependencies
│   └── wdk_bridge.mjs      # Node adapter for direct WDK calls
├── AGENTS.md               # [AI] Context for AI Coding Assistants
├── MCP_CONFIG.json         # [AI] MCP Server Configuration
├── main.py                 # CLI Entry Point
└── TEST_CASES.md           # Verification Scenarios
```

## 6. Security Design Principles

1.  **Least Privilege**: The WDK Client is only instantiated when `Guardian Mode` is explicitly activated.
2.  **Separation of Concerns**: The module that _decides_ (Guardian) is separate from the module that _signs_ (WDK Client).
3.  **Security Override (Safety-First)**: If **ANY** security module (Logic or AI) flags a risk, the transaction is **BLOCKED**. Logic Checks (Deterministic) take precedence over AI (Probabilistic).
    - _Example_: If the AI says "Safe" but the address is in a local hardcoded blacklist, the Logic module overrides the AI and BLOCKS the transaction.
4.  **Fail-Safe Defaults**: If the AI service is unreachable or returns an error, the Guardian defaults to **BLOCKING** the transaction (Conservative Security).
5.  **Ephemeral Keys**: By default, the system generates ephemeral keys for demo purposes unless a specific `WDK_PRIVATE_KEY` is injected via environment variables.
6.  **Artifact Hygiene**: Logs and generated runtime artifacts (`*.log`, `wdk_bridge/node_modules`, `wdk_bridge/package-lock.json`) are excluded from commit scope.
