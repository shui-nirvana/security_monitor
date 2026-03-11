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

- **Core Wrapper**: `core/wdk_client.py` (Mocks the official SDK for Hackathon demo).
- **Agent Logic**: `agents/guardian_agent.py` (Implements the "AI Guardian" pattern).
