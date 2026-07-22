#!/usr/bin/env python3
"""ROSTR API Server — FastAPI backend for desktop + web"""
import asyncio, logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uvicorn

from rostr.orchestrator import RostrOrchestrator
from rostr.llm_provider import LLMFactory
from rostr.config import ConfigManager
from rostr.pal_skill import PALSkill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ROSTR API", version="0.1.0")

# CORS for desktop + web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
config_manager = ConfigManager()
orchestrator = None
llm_provider = None
pal_skill = None

# Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    workspace_id: str = "default"
    provider: str = "anthropic"
    model: Optional[str] = None
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    message: str
    workspace_id: str
    tokens_used: int
    success: bool
    timestamp: str

class PALEnhanceRequest(BaseModel):
    prompt: str

class PALEnhanceResponse(BaseModel):
    original: str
    enhanced: str
    intent: str
    domain: str

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    global orchestrator, llm_provider, pal_skill
    
    logger.info("🚀 ROSTR API starting...")
    
    # Load config
    llm_config = config_manager.get_llm_config()
    llm_provider = LLMFactory.create(
        llm_config.provider,
        api_key=llm_config.api_key
    )
    
    orchestrator = RostrOrchestrator()
    pal_skill = PALSkill(llm_provider)
    
    logger.info(f"✅ ROSTR API ready | Provider: {llm_config.provider}")

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "version": "0.1.0"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint — orchestrate user message through ROSTR"""
    logger.info(f"📨 Chat: {request.message[:60]}...")
    
    try:
        # Orchestrate through ROSTR
        result = orchestrator.orchestrate(request.message)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        return ChatResponse(
            message=result.output,
            workspace_id=request.workspace_id,
            tokens_used=result.tokens_used,
            success=True,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"❌ Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pal/enhance", response_model=PALEnhanceResponse)
async def pal_enhance(request: PALEnhanceRequest):
    """Enhance prompt with PAL"""
    logger.info(f"🧠 PAL enhance: {request.prompt[:60]}...")
    
    try:
        result = await pal_skill.enhance(request.prompt)
        
        return PALEnhanceResponse(
            original=request.prompt,
            enhanced=result.get("enhanced_prompt", request.prompt),
            intent=result.get("intent_type", "general"),
            domain=result.get("domain", "ops")
        )
    
    except Exception as e:
        logger.error(f"❌ PAL enhance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workspace/{workspace_id}/history")
async def get_workspace_history(workspace_id: str):
    """Get execution history for workspace"""
    history = [h for h in orchestrator.execution_history if h.get("workspace_id") == workspace_id]
    return {"workspace_id": workspace_id, "executions": history}

@app.get("/api/config/providers")
async def get_providers():
    """List available LLM providers"""
    return {
        "providers": [
            "openai",
            "anthropic",
            "gemini",
            "openrouter",
            "lm_studio",
            "ollama",
            "bedrock",
            "azure"
        ]
    }

@app.post("/api/config/llm")
async def set_llm_config(provider: str, api_key: str):
    """Set LLM provider config"""
    try:
        config_manager.config[f"{provider}_key"] = api_key
        config_manager.config["llm_provider"] = provider
        
        # Reload provider
        global llm_provider
        llm_provider = LLMFactory.create(provider, api_key=api_key)
        
        logger.info(f"✅ LLM provider set to: {provider}")
        return {"status": "ok", "provider": provider}
    
    except Exception as e:
        logger.error(f"❌ Failed to set provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/skills")
async def list_skills():
    """List available skills"""
    return {
        "skills": [
            {"id": "pal-compiler", "name": "PAL Compiler", "category": "core"},
            {"id": "rostr-agent-builder", "name": "ROSTR Agent Builder", "category": "dev"},
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
