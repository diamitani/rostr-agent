"""
ROSTR Harness Client — invokes AgentCore Harnesses via InvokeHarness API.

Usage:
    from harness_client import HarnessClient
    
    client = HarnessClient(region='us-east-1')
    
    # Streaming invoke
    async for chunk in client.chat('rostr', 'Build me a REST API', user_id='pat'):
        print(chunk, end='')
    
    # Non-streaming
    response = client.chat_sync('artispreneur_master', 'I need an EPK', user_id='artist1')
"""

import json
import uuid
from typing import AsyncIterator, Optional

import boto3

# ── Harness Registry ──────────────────────────────────────────────────────────

HARNESS_REGISTRY = {
    # ROSTR Framework
    'rostr': {
        'harness_id': 'rostr_agent_harness-R0f36iLbHK',
        'arn': 'arn:aws:bedrock-agentcore:us-east-1:148761663702:harness/rostr_agent_harness-R0f36iLbHK',
        'runtime_arn': 'arn:aws:bedrock-agentcore:us-east-1:148761663702:runtime/harness_rostr_agent_harness-qg0TsgFjlL',
        'description': 'ROSTR Agent Harness — PAL/NPAO/RAG DAL/Hub',
    },
    # Artispreneur Platform
    'artispreneur_master': {
        'harness_id': 'artispreneur_master-4FgsFncXxK',
        'arn': 'arn:aws:bedrock-agentcore:us-east-1:148761663702:harness/artispreneur_master-4FgsFncXxK',
        'runtime_arn': 'arn:aws:bedrock-agentcore:us-east-1:148761663702:runtime/harness_artispreneur_master-2Wm3FMBTMG',
        'description': 'Artispreneur Chief of Staff — routes to EPK, Research, Campaign',
    },
    'artispreneur_epk': {
        'harness_id': 'artispreneur_epk-ijbNJ4Orqq',
        'arn': 'arn:aws:bedrock-agentcore:us-east-1:148761663702:harness/artispreneur_epk-ijbNJ4Orqq',
        'runtime_arn': 'arn:aws:bedrock-agentcore:us-east-1:148761663702:runtime/harness_artispreneur_epk-ZBGrLt5ocB',
        'description': 'Artispreneur EPK Builder — bios, press kits, budgets, contracts',
    },
    'artispreneur_research': {
        'harness_id': 'artispreneur_research-cVjA0xcK5J',
        'arn': 'arn:aws:bedrock-agentcore:us-east-1:148761663702:harness/artispreneur_research-cVjA0xcK5J',
        'runtime_arn': 'arn:aws:bedrock-agentcore:us-east-1:148761663702:runtime/harness_artispreneur_research-5NvzQn9BoT',
        'description': 'Artispreneur Music Biz Researcher — sync, venues, tours, markets',
    },
    'artispreneur_campaign': {
        'harness_id': 'artispreneur_campaign-TqCWTWfWda',
        'arn': 'arn:aws:bedrock-agentcore:us-east-1:148761663702:harness/artispreneur_campaign-TqCWTWfWda',
        'runtime_arn': 'arn:aws:bedrock-agentcore:us-east-1:148761663702:runtime/harness_artispreneur_campaign-zS5AcL7A2j',
        'description': 'Artispreneur Campaign Architect — A&R, social media, email, fans',
    },
}

MODEL_TO_HARNESS = {
    'rostr-agent': 'rostr',
    'rostr-agent-fast': 'rostr',
    'artispreneur': 'artispreneur_master',
    'artispreneur-epk': 'artispreneur_epk',
    'artispreneur-research': 'artispreneur_research',
    'artispreneur-campaign': 'artispreneur_campaign',
}

# ── Artispreneur Agent Skills ────────────────────────────────────────────────
# The seven Artispreneur agents authored as Hermes skills (see
# ~/.hermes/skills/artispreneur-agents/). These are attached to the
# ``artispreneur_master`` harness in Bedrock AgentCore and routed by the master
# (Day to Day Manager). Keep in sync with the AgentCore console "Skills" tab.

AGENT_SKILLS = [
    {
        'name': 'artispreneur-master',
        'agent': 'Day to Day Manager',
        'role': 'Master orchestration — onboarding, business plan, roadmap, calendar, email, CRM',
        'routes_to': ['publishing', 'finance', 'pr', 'booking', 'legal', 'brand'],
        'skill_path': 'artispreneur-agents/artispreneur-master',
    },
    {
        'name': 'artispreneur-publishing-manager',
        'agent': 'Publishing Manager',
        'role': 'PRO registration, royalty tracking, catalogue, split sheets',
        'skill_path': 'artispreneur-agents/artispreneur-publishing-manager',
    },
    {
        'name': 'artispreneur-finance-manager',
        'agent': 'Finance Manager',
        'role': 'Business banking, income/expense tracking, P&L',
        'skill_path': 'artispreneur-agents/artispreneur-finance-manager',
    },
    {
        'name': 'artispreneur-pr-manager',
        'agent': 'PR Manager',
        'role': 'Release campaigns, press, social media, ads, SEO',
        'skill_path': 'artispreneur-agents/artispreneur-pr-manager',
    },
    {
        'name': 'artispreneur-booking-manager',
        'agent': 'Booking Manager',
        'role': 'Gig discovery, outreach, booking calendar/CRM',
        'skill_path': 'artispreneur-agents/artispreneur-booking-manager',
    },
    {
        'name': 'artispreneur-legal-manager',
        'agent': 'Legal Manager',
        'role': 'Contracts, EIN/LLC/C-Corp formation, legal partners',
        'skill_path': 'artispreneur-agents/artispreneur-legal-manager',
    },
    {
        'name': 'artispreneur-brand-manager',
        'agent': 'Brand Manager',
        'role': 'Brand guidelines, logo, EPK, website, merch, social content',
        'skill_path': 'artispreneur-agents/artispreneur-brand-manager',
    },
]


class HarnessClient:
    """Client for invoking AgentCore Harnesses."""

    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client('bedrock-agentcore', region_name=self.region)
        return self._client

    def _resolve(self, model: str) -> dict:
        """Resolve a model name to harness config."""
        harness_name = MODEL_TO_HARNESS.get(model, model)
        config = HARNESS_REGISTRY.get(harness_name)
        if not config:
            raise ValueError(f"Unknown harness: {model}. Available: {list(HARNESS_REGISTRY.keys())}")
        return config

    def invoke(self, model: str, messages: list, *, user_id: str = 'default',
               session_id: Optional[str] = None, max_iterations: int = 50,
               timeout: int = 1800) -> dict:
        """Invoke a harness synchronously (streaming). Returns the response stream."""
        config = self._resolve(model)
        if session_id is None:
            session_id = str(uuid.uuid4())

        return self.client.invoke_harness(
            harnessArn=config['arn'],
            runtimeSessionId=session_id,
            actorId=user_id,
            messages=messages,
            maxIterations=max_iterations,
            timeoutSeconds=timeout,
        )

    def chat_sync(self, model: str, prompt: str, *, user_id: str = 'default',
                  session_id: Optional[str] = None) -> str:
        """Non-streaming chat — returns the full response text."""
        resp = self.invoke(
            model,
            [{'role': 'user', 'content': [{'text': prompt}]}],
            user_id=user_id,
            session_id=session_id,
        )
        text = ''
        stream = resp['stream']
        for event in stream:
            if 'contentBlockDelta' in event:
                text += event['contentBlockDelta']['delta'].get('text', '')
        return text

    def stream_chat(self, model: str, prompt: str, *, user_id: str = 'default',
                    session_id: Optional[str] = None):
        """Generator that yields text deltas from a streaming harness invocation."""
        resp = self.invoke(
            model,
            [{'role': 'user', 'content': [{'text': prompt}]}],
            user_id=user_id,
            session_id=session_id,
        )
        stream = resp['stream']
        for event in stream:
            if 'contentBlockDelta' in event:
                yield event['contentBlockDelta']['delta'].get('text', '')
            elif 'messageStop' in event:
                break
            elif 'metadata' in event:
                pass  # usage info, skip for now


# ── Convenience functions ─────────────────────────────────────────────────────

_client: Optional[HarnessClient] = None


def get_client() -> HarnessClient:
    global _client
    if _client is None:
        _client = HarnessClient()
    return _client


def chat(model: str, prompt: str, user_id: str = 'default') -> str:
    return get_client().chat_sync(model, prompt, user_id=user_id)


def list_harnesses() -> list:
    return [{'id': k, **{kk: vv for kk, vv in v.items() if kk != 'arn'}}
            for k, v in HARNESS_REGISTRY.items()]


def list_agent_skills() -> list:
    """Return the Artispreneur agent-skill manifest (master + 6 sub-agents)."""
    return AGENT_SKILLS
