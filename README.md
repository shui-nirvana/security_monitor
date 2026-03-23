# 🛡️ Guardian Agent: WDK-Powered Autonomous Security Framework

> **Tether Hackathon Galactica Submission**  
> _Track: Build Agents with Tether WDK_

An autonomous financial agent that combines **AI Risk Analysis (The Brain)** with **Tether WDK Execution (The Hands)**. It features a "Safety-First" architecture where deterministic logic overrides AI probability, ensuring secure autonomous fund management.

---

## 🌟 Key Features

### 1. 🧠 Dual-Engine Risk Control (Safety First)

- **The Brain (AI)**: Uses LLMs (DeepSeek/Gemini) to analyze transaction intent and detect complex phishing patterns. **Includes a built-in Simulation Mode** for demo purposes if no API key is provided.
- **The Logic (Deterministic)**: Hardcoded safety rules (e.g., Blacklists, Allowance limits).
- **Security Override Protocol**: **Logic > AI**. If the AI says "Safe" but the Logic says "Risky", the transaction is **BLOCKED**.

### 2. 🔌 Native Tether WDK Integration

- **WalletManager**: Full lifecycle management (Creation, Restoration, Signing) with runtime switch between local Web3 and official WDK bridge mode.
- **NonceManager**: **[Bonus Feature]** Implements asynchronous state synchronization to handle high-concurrency Nonce conflicts during rapid agent actions.
- **Official SDK Bridge**: `wdk_bridge/wdk_bridge.mjs` calls `@tetherto/wdk` + `@tetherto/wdk-wallet-evm` directly for address derivation, signing, and transfer execution.
- **Primitives**: Direct use of WDK primitives for signing and broadcasting transactions for **USDT**, **USAT**, and **XAUT**.

### 3. 🖥️ Matrix-Style Visual Dashboard

- **Real-Time Visualization**: A `rich`-based immersive console UI that displays the agent's "thinking process" and WDK execution status in real-time.
- **Live Status**: Spinner animations for AI analysis and Blockchain broadcasting.
- **Try it now**: Run `python security_monitor/tests/visual_demo.py` to see the UI in action without configuration.

### 4. 🤖 OpenClaw / Agent Framework Ready

- Designed to work as the "Execution Layer" for agent frameworks like OpenClaw.
- Separates **Reasoning** (Agent) from **Execution** (WDK).
- **Simulation Mode**: Built-in OpenClaw simulation scenarios (e.g., injection attacks) for testing.

---

## 🚀 Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
cd security_monitor/wdk_bridge && npm install
```

### 2. Configuration

Copy `.env.example` to `.env` and configure your keys.

```bash
cp .env.example .env
# Edit .env:
# - WDK_PRIVATE_KEY (Optional, for restoring wallet)
# - WDK_USE_TETHER_WDK (Set True to force official @tetherto WDK path)
# - WDK_SEED_PHRASE (Required when WDK_USE_TETHER_WDK=True)
# - WDK_ACCOUNT_INDEX (Optional, default 0)
# - WDK_NODE_CMD (Optional, default node)
# - WDK_BRIDGE_SCRIPT (Optional, bridge script path)
# - RPC_URL (Required)
# - LLM_API_KEY (Optional - System defaults to Simulation Mode if missing)
# - GUARDIAN_MAX_TRANSFER_AMOUNT (Optional transfer policy limit)
# - GUARDIAN_SUPPORTED_ASSETS (Optional asset allowlist)
```

### 3. Run: Visual Demo (No Setup Required)

Experience the Matrix-style UI and Guardian workflow immediately:

```bash
python security_monitor/tests/visual_demo.py
```

### 4. Run: Guardian Mode (Active Agent)

In this mode, the agent autonomously holds funds and executes transfers **only if** they pass safety checks.

```bash
# 🟢 Safe Transfer Scenario (USD₮)
python main.py --mode guardian --action transfer --asset USDT --to 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --amount 50

# 🟢 Safe Transfer Scenario (USA₮ / XAU₮)
python main.py --mode guardian --action transfer --asset USAT --to 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --amount 20
python main.py --mode guardian --action transfer --asset XAUT --to 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --amount 1

# 🔴 Phishing Simulation (Security Override)
# Target is the 'dead' address, which triggers a Logic Block
python main.py --mode guardian --action transfer --asset USDT --to 0x000000000000000000000000000000000000dEaD --amount 50

# 🔴 OpenClaw Injection Simulation (AI Block)
# Target is a known malicious contract in the simulation database
python main.py --mode guardian --action transfer --asset USDT --to 0x6666666666666666666666666666666666666666 --amount 100

# 🧪 Policy Override Demo (CLI)
# Use runtime policy overrides for live hackathon demos
python main.py --mode guardian --action transfer --asset USDT --to 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --amount 30 --daily-total-limit 100 --daily-asset-limits USDT:50,USAT:20 --allow-counterparty 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --max-transfer-amount 40 --no-require-ai-approval
```

### 4. Run: Monitor Mode (Passive Scanner)

Standard ERC20 allowance auditing.

```bash
python main.py --mode monitor --owner <ADDRESS> --spender <ADDRESS>
```

### 5. 30-Second Live Demo Sequence

Use these three commands in order during a live pitch:

```bash
# Step 1: PASS (safe + policy-compliant)
python main.py --mode guardian --action transfer --asset USDT --to 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --amount 30 --allow-counterparty 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --max-transfer-amount 40 --no-require-ai-approval

# Step 2: BLOCK (policy limit)
python main.py --mode guardian --action transfer --asset USDT --to 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --amount 60 --allow-counterparty 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --max-transfer-amount 40 --no-require-ai-approval

# Step 3: BLOCK (blacklist/security override)
python main.py --mode guardian --action transfer --asset USDT --to 0x000000000000000000000000000000000000dEaD --amount 10 --max-transfer-amount 40 --no-require-ai-approval
```

Expected highlights:

- Step 1 shows `✅ TRANSACTION EXECUTED VIA WDK`
- Step 2 shows `🛑 TRANSACTION BLOCKED` with `Amount exceeds policy limit`
- Step 3 shows `🛑 TRANSACTION BLOCKED` with blacklist/security reason

---

## 🏗️ Architecture

| Component             | File                                                           | Responsibility                                                                   |
| --------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **Guardian Agent**    | [`agents/guardian_agent.py`](./agents/guardian_agent.py)       | **The Orchestrator**. Coordinates Brain & Hands. Implements "Security Override". |
| **WDK Client**        | [`core/wdk_client.py`](./core/wdk_client.py)                   | **The Hands**. WDK primitives, `WalletAccount`, `NonceManager`.                  |
| **WDK Bridge (Node)** | [`wdk_bridge/wdk_bridge.mjs`](./wdk_bridge/wdk_bridge.mjs)     | Direct adapter to official `@tetherto/wdk` and `@tetherto/wdk-wallet-evm`.       |
| **Allowance Monitor** | [`agents/allowance_monitor.py`](./agents/allowance_monitor.py) | **The Logic**. Deterministic safety checks.                                      |
| **AI Analyzer**       | [`agents/ai_analyzer.py`](./agents/ai_analyzer.py)             | **The Brain**. Probabilistic risk assessment.                                    |
| **Visualizer**        | [`utils/matrix_ui.py`](./utils/matrix_ui.py)                   | **The UI**. Matrix-style console rendering.                                      |

> 📚 See [ARCHITECTURE.md](./ARCHITECTURE.md) for a detailed system design.

---

## 🧪 Test Cases & Verification

We have designed specific scenarios to verify Hackathon compliance, including:

1.  **Autonomous Safe Transfer**: Agent manages WDK wallet and signs valid tx.
2.  **Phishing Interception**: Agent refuses to sign for malicious addresses.
3.  **OpenClaw Injection Sim**: Simulating a compromised AI brain being overridden by Guardian's safety logic.

> 🧪 See [TEST_CASES.md](./TEST_CASES.md) for full execution logs and scenarios.

---

## ✅ Hackathon Track Compliance

This project fulfills the **"Build Agents with Tether WDK"** track requirements:

- [x] **Integrate Tether WDK**: Uses official `@tetherto/wdk` + `@tetherto/wdk-wallet-evm` through a direct bridge and WDK-compatible Python primitives.
- [x] **Autonomous Fund Management**: Agent policy layer supports USD₮ / USA₮ / XAU₮ asset routing.
- [x] **Emphasis on Safety**: Implements "Security Override" (Logic > AI) and strict permission checks.
- [x] **Agent Reasoning**: Uses LLM for context analysis (OpenClaw equivalent).
- [x] **Bonus**: Implemented `NonceManager` for async state sync.

---

## 📫 Contact

- **Discord**: guaguagua_59889
- **Email**: lsnirvana@gmail.com
- **DoraHacks BUIDL**: [View Project](https://dorahacks.io/buidl/40387)
