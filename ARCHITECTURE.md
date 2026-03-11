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
- **WDK Primitives**: Direct implementation of:
  - `create_wallet()`
  - `sign_message()`
  - `send_transaction()`

### 🤖 The Guardian: Agent Orchestrator
Located in `agents/guardian_agent.py`.
- **Responsibility**: Binds the "Brain" and "Hands" together.
- **Policy**: "Think before you Act".
- **Workflow**:
  1. Receive high-level intent (e.g., "Transfer 50 USDT to Bob").
  2. Consult **The Brain** to validate Bob's address.
  3. If Risk > LOW, **ABORT**.
  4. If Risk == LOW, authorize **The Hands** to sign and broadcast.

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

## 4. Directory Structure & Key Files

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
├── AGENTS.md               # [AI] Context for AI Coding Assistants
├── MCP_CONFIG.json         # [AI] MCP Server Configuration
├── main.py                 # CLI Entry Point
└── TEST_CASES.md           # Verification Scenarios
```

## 5. Security Design Principles

1.  **Least Privilege**: The WDK Client is only instantiated when `Guardian Mode` is explicitly activated.
2.  **Separation of Concerns**: The module that *decides* (Guardian) is separate from the module that *signs* (WDK Client).
3.  **Security Override (Safety-First)**: If **ANY** security module (Logic or AI) flags a risk, the transaction is **BLOCKED**. Logic Checks (Deterministic) take precedence over AI (Probabilistic).
    - *Example*: If the AI says "Safe" but the address is in a local hardcoded blacklist, the Logic module overrides the AI and BLOCKS the transaction.
4.  **Fail-Safe Defaults**: If the AI service is unreachable or returns an error, the Guardian defaults to **BLOCKING** the transaction (Conservative Security).
5.  **Ephemeral Keys**: By default, the system generates ephemeral keys for demo purposes unless a specific `WDK_PRIVATE_KEY` is injected via environment variables.
