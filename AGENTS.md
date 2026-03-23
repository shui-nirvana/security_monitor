# WDK Development Rules & AI Context

This file provides AI agents (Cursor, Trae, Copilot, etc.) with persistent context about WDK conventions, package naming, and common patterns, as recommended by the official Tether WDK documentation.

## 📦 Package Structure

- **Core module**: `@tetherto/wdk` (The orchestrator)
- **Wallet modules pattern**: `@tetherto/wdk-wallet-<chain>`
  - Examples:
    - `@tetherto/wdk-wallet-evm` (Ethereum/EVM)
    - `@tetherto/wdk-wallet-btc` (Bitcoin)
    - `@tetherto/wdk-wallet-solana` (Solana)
    - `@tetherto/wdk-wallet-ton` (TON)
    - `@tetherto/wdk-wallet-tron` (TRON)

## 🏗️ Architecture Patterns

1. **Modularity**: WDK is modular - each blockchain and protocol is a separate package.
2. **Wallet Classes**:
   - `WalletManager`: Manages multiple wallets.
   - `WalletAccount`: Full access (Sign, Send).
   - `WalletAccountReadOnly`: View-only access (Balance, History).
3. **Lifecycle**: Configuration → Initialization → Usage.

## 🤖 AI Integration Guidelines

- **Context Awareness**: When generating code for WDK, always prefer the official `@tetherto` scoped packages over generic libraries.
- **Safety First**: Ensure all wallet operations (signing/sending) are wrapped in try-catch blocks and preceded by risk checks (as implemented in `GuardianAgent`).
- **Official Docs**: Refer to `https://docs.wallet.tether.io` for API specifics.

## 🛠️ Project Implementation Status

- **Core Wrapper**: `core/wdk_client.py` (WDK-compatible Python primitives with direct bridge support).
- **Agent Logic**: `agents/guardian_agent.py` (Implements the "AI Guardian" pattern).
- **Official SDK Bridge**: `wdk_bridge/wdk_bridge.mjs` (Directly calls `@tetherto/wdk` and `@tetherto/wdk-wallet-evm`).

## 🧾 WDK Audit Notes (For Organizer Review)

- **Gap recorded**: previous runtime path needed stronger proof of direct official SDK invocation.
- **Fix applied**: execution path now explicitly routes Python WDK primitives to `wdk_bridge/wdk_bridge.mjs`, which imports official `@tetherto/*` packages.
- **Primitive mapping**:
  - `create_wallet` -> `get_address`
  - `sign_message` -> `sign`
  - `send_transaction` -> `transfer`
  - `get_balance` -> `get_balance`
- **Performance upgrade**:
  - Old: per-call `subprocess.run` (cold boot each request).
  - New: persistent `subprocess.Popen` + line-based JSON IPC + in-process context cache.
  - Operational impact: warm calls skip repeated Node + WDK bootstrap and return faster.

## 🧹 Commit Hygiene

- Do not commit generated/runtime files.
- Keep logs untracked (`*.log`, `security_monitor.log`).
- Keep Node runtime artifacts untracked (`wdk_bridge/node_modules`, `wdk_bridge/package-lock.json`).
