# Blockchain Security Monitor Framework

A robust, production-grade Python framework for monitoring ERC-20 allowances and analyzing security risks using LLMs (DeepSeek/Gemini/OpenAI).

## Features

- **Allowance Monitoring**: Detects high-risk approvals (e.g., unlimited allowance).
- **AI Risk Analysis**: Integrates with LLMs to provide natural language risk assessments and recommendations.
- **Robust Architecture**: Automatic RPC retries, checksum address handling, and comprehensive logging.
- **Production Ready**: Configurable via `.env`, type-safe settings, and modular agent design.

## Quick Start (Out-of-the-Box)

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Copy `.env.example` to `.env` and set your API keys (optional for basic checks).

   ```bash
   cp .env.example .env
   ```

   _Example `.env`:_

   ```ini
   RPC_URL=https://eth-mainnet.public.blastapi.io
   ENABLE_AI_ANALYSIS=True
   LLM_API_KEY=sk-your-key
   LLM_MODEL=deepseek-chat
   ```

3. **Run Security Scan**
   Check a wallet's allowance for a specific spender:
   ```bash
   python main.py --owner <WALLET_ADDRESS> --spender <SPENDER_ADDRESS>
   ```

## Directory Structure

- `core/`: Blockchain client and base infrastructure.
- `agents/`: specialized security agents (AllowanceMonitor, AIAnalyzer).
- `config/`: Configuration management.

## Roadmap

- [ ] **Q2 2026**: Integration of Multi-chain Automated Scanning (Arbitrum, Base).
- [ ] **Q3 2026**: Autonomous "Revoke-on-Risk" action trigger.
- [ ] **Q4 2026**: Voice-activated security status reports via AI interface.

## 📫 Contact

I am a Senior Full-Stack Architect (10+ years exp) pivoting to AI Agent & Web3 Infrastructure.

- **Discord**: guaguagua_59889
- **Email**: lsnirvana@gmail.com
- **DoraHacks BUIDL**: [View Project](https://dorahacks.io/buidl/40387)
