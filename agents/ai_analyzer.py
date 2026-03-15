import logging
from typing import Any, Dict, Optional

import requests
from security_monitor.config.settings import get_settings

logger = logging.getLogger(__name__)


class AIAnalyzer:
    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.ENABLE_AI_ANALYSIS
        self.simulation_mode = False

        if self.enabled and not self.settings.LLM_API_KEY:
            logger.warning("AI Analysis enabled but no API Key provided. Switching to SIMULATION MODE.")
            self.simulation_mode = True

    def _chat_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> Optional[str]:
        if not self.enabled:
            return None

        if self.simulation_mode:
            # Simulate network latency for realism
            import time
            time.sleep(1.5)
            return "SIMULATION_RESPONSE"

        headers = {
            "Authorization": f"Bearer {self.settings.LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.settings.LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }
        try:
            response = requests.post(
                f"{self.settings.LLM_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            logger.error(f"AI API Error: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"AI API Exception: {str(e)}")
            return None

    def analyze_risk(self, data: Dict[str, Any]) -> Optional[str]:
        if not self.enabled:
            return None
        prompt = self._construct_prompt(data)
        content = self._chat_completion(
            "You are a Blockchain Security Auditor. Analyze ERC-20 allowance data for risks. Be concise.",
            prompt
        )
        if content is None:
            return "AI Analysis Failed (Service Unavailable)"
        return content

    def analyze_transfer_target(self, to_address: str, amount: float, token_symbol: str) -> Dict[str, Any]:
        if not self.enabled:
            return {"safe": True, "reason": "AI analysis disabled"}

        if self.simulation_mode:
            import time
            time.sleep(1.5) # Simulate AI thinking

            # Simulation Logic for Demo
            normalized_addr = to_address.lower()

            # Case 1: Suspicious Pattern (e.g., ends in 'dead')
            if normalized_addr.endswith("dead"):
                return {"safe": False, "reason": "AI Model (Simulated) detected 'dead' address pattern associated with burn addresses."}

            # Case 2: High Amount Check
            if amount > 5000:
                return {"safe": False, "reason": "AI Model (Simulated) flagged unusually high transfer volume for this profile."}

            # Case 3: Known Malicious (OpenClaw Simulation)
            if normalized_addr == "0x6666666666666666666666666666666666666666":
                return {"safe": False, "reason": "OpenClaw Risk Database: Confirmed Phishing Contract."}

            return {"safe": True, "reason": "AI Model (Simulated) assessment: Low Risk. Pattern matches normal user behavior."}

        prompt = (
            f"Target Address: {to_address}\n"
            f"Asset: {token_symbol}\n"
            f"Amount: {amount}\n\n"
            "Respond with one risk level word first: LOW, MEDIUM, or HIGH.\n"
            "Then provide one short reason."
        )
        content = self._chat_completion(
            "You are a strict blockchain transaction risk engine.",
            prompt,
            temperature=0.1
        )
        if content is None:
            return {"safe": False, "reason": "AI service unavailable (Fail-Safe Block)"}
        normalized = content.upper()
        if "HIGH" in normalized or "MEDIUM" in normalized:
            return {"safe": False, "reason": f"AI flagged risk: {content}"}
        return {"safe": True, "reason": content}

    def _construct_prompt(self, data: Dict[str, Any]) -> str:
        return f"""
        Risk Assessment Request:
        - Token: {data.get('token')}
        - Owner: {data.get('owner')}
        - Spender: {data.get('spender')}
        - Allowance: {data.get('allowance_formatted')} (Raw: {data.get('allowance_raw')})
        - Owner Balance: {data.get('owner_balance')}
        - Initial Risk Assessment: {data.get('risk_level')}

        Please evaluate:
        1. Is this allowance suspicious given the balance?
        2. What are the potential implications if the spender is compromised?
        3. Recommend an action for the user.
        """
