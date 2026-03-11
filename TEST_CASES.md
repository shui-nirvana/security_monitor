# Security Monitor & Guardian Agent - Test Cases

This document outlines the core test scenarios for the Tether Hackathon submission. It covers both the passive **Monitor Mode** (Security Auditing) and the active **Guardian Mode** (WDK Execution).

---

## 🏗️ Setup

Ensure dependencies are installed and `.env` is configured.

```bash
pip install -r requirements.txt
# Ensure .env has RPC_URL configured
```

---

## 🧪 Scenario Group 1: Monitor Mode (Passive Auditing)

_Goal: Verify the system can correctly identify risky allowance patterns without executing transactions._

### Case 1.1: Safe Allowance Check

**Description**: Check a wallet that has granted a reasonable allowance (e.g., 0 or small amount) to a known protocol.
**Expected Result**: Risk Level `LOW`.

```bash
# Vitalik's Address -> Uniswap Router (Example)
python main.py --mode monitor --owner 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --spender 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D
```

### Case 1.2: Risky/Unlimited Allowance Check

**Description**: Check a wallet that has granted `UINT256_MAX` (Unlimited) allowance to a spender.
**Expected Result**: Risk Level `HIGH (Unlimited/Excessive)` or `MEDIUM`.

```bash
# Justin Sun's Address -> Some DeFi Protocol (Example)
python main.py --mode monitor --owner 0x90e63c3d53E0Ea496845b7a03ec7548B70014A91 --spender 0xSpenderAddress...
```

_(Note: You may need to find a live example or mock the return value in `AllowanceMonitorAgent` if no live unlimited allowance is found easily.)_

---

## 🛡️ Scenario Group 2: Guardian Mode (Active WDK Agent) [HACKATHON CORE]

_Goal: Verify the AI Agent can autonomously manage funds and block threats using WDK primitives._

### Case 2.1: Autonomous Safe Transfer (Success)

**Requirement Met**: "Agents should hold, send, or manage USD₮ autonomously"
**Description**: Instruct the Guardian Agent to transfer USDT to a legitimate address.
**Flow**:

1. Agent receives instruction.
2. Agent ("Brain") validates the destination address format and reputation (AI check).
3. Agent ("Hands") creates a WDK `WalletAccount`.
4. Agent signs and broadcasts the transaction via WDK.
   **Expected Result**: `✅ TRANSACTION EXECUTED VIA WDK` with a valid Tx Hash.

```bash
# Transfer 50 USDT to a safe address (e.g., Vitalik's)
python main.py --mode guardian --action transfer --asset USDT --to 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --amount 50
```

### Case 2.2: Phishing Attempt Interception (Logic Block)

**Requirement Met**: "Emphasis on safety: permissions, limits"
**Description**: Instruct the Agent to transfer funds to a known malicious/burn address.
**Flow**:

1. Agent receives instruction.
2. Agent ("Brain") detects the address is suspicious (e.g., Null Address or Blacklisted).
3. Agent **REFUSES** to sign the transaction.
4. No WDK execution occurs.
   **Expected Result**: `🛑 TRANSACTION BLOCKED` with reason `Blocked by Local Blacklist`.

```bash
# Attempt transfer to the "Dead" address (simulated phishing pot)
python main.py --mode guardian --action transfer --asset USAT --to 0x000000000000000000000000000000000000dEaD --amount 50
```

### Case 2.3: OpenClaw Injection Simulation (AI Block)

**Requirement Met**: "OpenClaw (or any other equivalent agent framework) for agent reasoning"
**Description**: Simulate an attack where a malicious agent tries to inject a bad transaction, but the Guardian's AI Brain (OpenClaw Simulation) detects it.
**Scenario**:

- Target Address: `0x6666666666666666666666666666666666666666` (Known Phishing Contract in Simulation DB).
- AI Response: "High Risk".
- **Expected Result**: `🛑 BLOCKED! OpenClaw Risk Database: Confirmed Phishing Contract.`

```bash
python main.py --mode guardian --action transfer --asset USDT --to 0x6666666666666666666666666666666666666666 --amount 100
```

### Case 2.4: Multi-Asset Support (USDT, USAT, XAUT)

**Requirement Met**: "Agents should hold, send, or manage USD₮, USA₮ or XAU₮ autonomously"
**Description**: Verify the agent can handle different Tether assets using the same WDK primitives.

```bash
# Transfer XAUT (Gold)
python main.py --mode guardian --action transfer --asset XAUT --to 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --amount 1.5
```

### Case 2.5: Security Override (Safety-First)

**Requirement Met**: "Safety-First Policy"
**Description**: Test the conflict resolution when AI says "Safe" but Logic says "Unsafe".
**Scenario**:

- Target Address: A known malicious address (e.g., `0x000000000000000000000000000000000000dead`).
- AI Mock Response: "Safe" (Simulated False Negative).
- Logic Check: "Blacklisted" (Hardcoded Rule).
  **Expected Result**: The transaction must be **BLOCKED** by the Logic module, overriding the AI's "Safe" verdict.
  **Log Verification**: Look for `Blocked by Local Blacklist (Deterministic Logic)`.

### Case 2.6: Invalid Address Format (Logic Error)

**Description**: User provides a malformed Ethereum address.
**Expected Result**: `🛑 TRANSACTION BLOCKED` with `Invalid Ethereum Address Format`.

```bash
python main.py --mode guardian --action transfer --asset XAUT --to 0xInvalidAddress123 --amount 50
```

### Case 2.7: Transfer Limit Enforcement (Policy Guard)

**Requirement Met**: "Emphasis on safety: limits"
**Description**: Validate that transfers above policy threshold are blocked before WDK execution.
**Expected Result**: `🛑 TRANSACTION BLOCKED` with `Amount exceeds policy limit`.

```bash
python main.py --mode guardian --action transfer --asset USDT --to 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --amount 999999
```

---

## 🎯 Scenario Group 3: Hackathon Track Specifics

_Goal: Demonstrate compliance with specific track requirements._

### Case 3.1: WDK Primitives Usage Verification

**Requirement Met**: "Use WDK primitives directly (wallet creation, signing, accounts)"
**Description**: Verify that the Agent is using the dedicated WDK wrapper classes (`WalletManager`, `WalletAccount`) and not just raw Web3 calls.
**Verification Method**:

- Inspect logs for `[WDK:WalletManager]` and `[WDK:WalletAccount]` tags.
- These logs confirm the invocation of the WDK architectural layer.

```bash
# Run any guardian command and check logs
python main.py --mode guardian --action transfer --asset USDT --to 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --amount 10
# Look for: "Initializing Tether WDK Manager...", "Signing message...", "Transaction signed."
```

### Case 3.2: Separation of Concerns (Logic vs. Execution)

**Requirement Met**: "Clear separation between agent logic and wallet execution"
**Description**: Verify that the risk assessment logic runs _before_ any wallet interaction.
**Verification Method**:

- Run Case 2.2 (Phishing Block).
- Confirm that `[Guardian Agent] Consulting AI Brain...` appears in logs.
- Confirm that `[WDK:WalletAccount] Signing message...` DOES NOT appear.
- This proves the "Brain" stopped the "Hands".

### Case 3.3: OpenClaw Simulation - Injection Attack Interception

**Requirement Met**: "Safety-First / Agent Reasoning"
**Description**: Simulate a scenario where an external agent framework (like OpenClaw) is compromised or hallucinating, and attempts to inject a malicious transfer command.
**Scenario**:

- **Attacker (OpenClaw Simulation)**: Sends a valid JSON command but points to a phishing contract (0x666...).
- **Guardian Agent**: Receives the command but runs its own independent `_assess_risk` check.
- **Outcome**: The Guardian Agent refuses to execute the "Brain's" bad order.
  **Verification**:

```bash
# Simulating a compromised agent instruction
python main.py --mode guardian --action transfer --asset USDT --to 0x6666666666666666666666666666666666666666 --amount 100
```

**Expected Log**: `[Guardian Agent] BLOCKED transfer to 0x...6666. Reason: OpenClaw Risk Database: Confirmed Phishing Contract.`

---

## 🤖 AI Integration Test

_Goal: Verify the "AI-Native" architecture (Bonus/Nice to Have)._

### Case 4.1: Developer Context Injection

**Description**: Open `AGENTS.md` in your IDE (Trae/Cursor) and ask the AI assistant:

> "How do I create a new wallet using the WDK wrapper in this project?"

**Expected Result**: The AI should quote the `WalletManager` pattern defined in `core/wdk_client.py` and referenced in `AGENTS.md`, rather than hallucinating a generic Web3.py solution.
