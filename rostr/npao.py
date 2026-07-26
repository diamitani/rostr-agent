#!/usr/bin/env python3
"""NPAO Router — Necessity, Priority, Anxiety, Opportunity"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NPAOScore:
    necessity: float  # 0-1: how critical is this?
    priority: float   # 0-1: how urgent?
    anxiety: float    # 0-1: risk/consequence if not done?
    opportunity: float # 0-1: upside if done well?
    composite: float   # weighted score

class NPAORouter:
    """Score tasks on NPAO dimensions"""
    
    def __init__(self):
        self.weights = {
            "necessity": 0.35,
            "priority": 0.25,
            "anxiety": 0.25,
            "opportunity": 0.15
        }
    
    def score(self, user_message: str, context: dict) -> NPAOScore:
        """Calculate NPAO score"""
        necessity = self._calculate_necessity(user_message)
        priority = self._calculate_priority(user_message)
        anxiety = self._calculate_anxiety(user_message, context)
        opportunity = self._calculate_opportunity(user_message)
        
        composite = (
            necessity * self.weights["necessity"] +
            priority * self.weights["priority"] +
            anxiety * self.weights["anxiety"] +
            opportunity * self.weights["opportunity"]
        )
        
        return NPAOScore(
            necessity=necessity,
            priority=priority,
            anxiety=anxiety,
            opportunity=opportunity,
            composite=composite
        )
    
    def _calculate_necessity(self, msg: str) -> float:
        """Critical? Must-have?"""
        necessity_words = ["must", "require", "critical", "essential", "vital"]
        return 0.9 if any(w in msg.lower() for w in necessity_words) else 0.5
    
    def _calculate_priority(self, msg: str) -> float:
        """How urgent?"""
        urgent_words = ["urgent", "asap", "now", "today", "immediately"]
        return 0.95 if any(w in msg.lower() for w in urgent_words) else 0.4
    
    def _calculate_anxiety(self, msg: str, context: dict) -> float:
        """Risk if not done?"""
        risk_words = ["risk", "danger", "fail", "break", "loss"]
        base = 0.8 if any(w in msg.lower() for w in risk_words) else 0.3
        deadline = context.get("deadline_urgency", 0.0)
        return min(1.0, base + deadline)
    
    def _calculate_opportunity(self, msg: str) -> float:
        """Upside potential?"""
        opportunity_words = ["improve", "increase", "grow", "scale", "optimize"]
        return 0.8 if any(w in msg.lower() for w in opportunity_words) else 0.4
    
    def rank_by_npao(self, tasks: list) -> list:
        """Sort tasks by NPAO composite score"""
        scored = [(task, self.score(task.get("message", ""), task.get("context", {}))) for task in tasks]
        return sorted(scored, key=lambda x: x[1].composite, reverse=True)

if __name__ == "__main__":
    router = NPAORouter()
    score = router.score("Critical bug in production - fix immediately", {})
    print(f"Necessity: {score.necessity:.2f}, Priority: {score.priority:.2f}, Anxiety: {score.anxiety:.2f}, Opportunity: {score.opportunity:.2f}")
    print(f"Composite Score: {score.composite:.2f}")
