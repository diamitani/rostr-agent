#!/usr/bin/env python3
"""PAL Skill — Enhance prompts via PAL compilation"""
import json, logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PALSkill:
    """PAL as a skill — enhance any prompt"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
        self.name = "pal-compiler"
    
    async def enhance(self, user_prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhance prompt using PAL 5-stage pipeline"""
        logger.info(f"PAL Skill: enhancing '{user_prompt[:50]}...'")
        
        enhancement_prompt = f"""
You are PAL (Prompt Abstraction Layer). Enhance this user prompt:

Original: "{user_prompt}"

Analyze and return JSON with:
1. intent_type: what they actually want
2. domain: code|content|gtm|ops|analytics
3. constraints: tone, length, audience
4. missing_info: what's unclear?
5. enhanced_prompt: precise, actionable rewrite

Return ONLY valid JSON.
"""
        
        response = await self.llm.complete(enhancement_prompt)
        
        try:
            result = json.loads(response)
            result["original"] = user_prompt
            return result
        except json.JSONDecodeError:
            logger.warning(f"PAL returned non-JSON: {response[:100]}")
            return {
                "original": user_prompt,
                "intent_type": "general",
                "domain": "ops",
                "enhanced_prompt": user_prompt,
                "error": "Parse failed"
            }
    
    async def reprompt(self, original: str, response: str, feedback: str) -> str:
        """Use feedback to reprompt"""
        reprompt_text = f"""
Original request: {original}
First response: {response}

User feedback: {feedback}

Generate improved response addressing the feedback:
"""
        return await self.llm.complete(reprompt_text)
