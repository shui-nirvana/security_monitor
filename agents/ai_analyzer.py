import logging
import requests
from typing import Dict, Any, Optional
from config.settings import get_settings

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """
    AI Agent for Natural Language Risk Assessment.
    Uses LLM (DeepSeek/Gemini/OpenAI) to analyze raw blockchain data.
    """
    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.ENABLE_AI_ANALYSIS
        
        if self.enabled and not self.settings.LLM_API_KEY:
            logger.warning("AI Analysis enabled but no API Key provided. Disabling.")
            self.enabled = False

    def analyze_risk(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Sends the allowance data to the LLM for a second opinion.
        """
        if not self.enabled:
            return None

        prompt = self._construct_prompt(data)
        logger.info(f"Sending data to AI Analyzer ({self.settings.LLM_MODEL})...")
        
        try:
            # Generic OpenAI-compatible API call
            headers = {
                "Authorization": f"Bearer {self.settings.LLM_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a Blockchain Security Auditor. Analyze the following ERC-20 Allowance data for potential security risks. Be concise."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }

            response = requests.post(
                f"{self.settings.LLM_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result['choices'][0]['message']['content']
                logger.info("AI Analysis received successfully.")
                return analysis
            else:
                logger.error(f"AI API Error: {response.status_code} - {response.text}")
                return f"AI Analysis Failed (API Error {response.status_code})"

        except Exception as e:
            logger.error(f"AI Analysis Exception: {str(e)}")
            return f"AI Analysis Failed ({str(e)})"

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
