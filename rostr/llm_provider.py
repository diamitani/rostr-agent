#!/usr/bin/env python3
"""LLM Provider Abstraction — BYOK (Bring Your Own Keys)"""
import os, json, logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncIterator
from enum import Enum

logger = logging.getLogger(__name__)

class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    LM_STUDIO = "lm_studio"
    NOUS_RESEARCH = "nous"
    AWS_BEDROCK = "bedrock"
    AZURE = "azure"
    OLLAMA = "ollama"

class LLMProvider(ABC):
    """Base provider interface"""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def complete(self, prompt: str, model: str, **kwargs) -> str:
        """Get completion from provider"""
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, model: str, **kwargs) -> AsyncIterator[str]:
        """Stream completion"""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4, GPT-3.5, etc"""
    async def complete(self, prompt: str, model: str = "gpt-4", **kwargs) -> str:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise
    
    async def stream(self, prompt: str, model: str = "gpt-4", **kwargs):
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        async with await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs
        ) as stream:
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

class AnthropicProvider(LLMProvider):
    """Anthropic Claude"""
    async def complete(self, prompt: str, model: str = "claude-opus-4-1", **kwargs) -> str:
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            response = await client.messages.create(
                model=model,
                max_tokens=kwargs.get("max_tokens", 2048),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            raise
    
    async def stream(self, prompt: str, model: str = "claude-opus-4-1", **kwargs):
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=self.api_key)
        async with client.messages.stream(
            model=model,
            max_tokens=kwargs.get("max_tokens", 2048),
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            async for text in stream.text_stream:
                yield text

class GoogleGeminiProvider(LLMProvider):
    """Google Gemini"""
    async def complete(self, prompt: str, model: str = "gemini-pro", **kwargs) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            gen_model = genai.GenerativeModel(model)
            response = await gen_model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise
    
    async def stream(self, prompt: str, model: str = "gemini-pro", **kwargs):
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        gen_model = genai.GenerativeModel(model)
        async for chunk in await gen_model.generate_content_async(prompt, stream=True):
            yield chunk.text

class OpenRouterProvider(LLMProvider):
    """OpenRouter — 100+ models"""
    async def complete(self, prompt: str, model: str = "openai/gpt-4", **kwargs) -> str:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.io/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        **kwargs
                    }
                )
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            raise
    
    async def stream(self, prompt: str, model: str = "openai/gpt-4", **kwargs):
        import httpx
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://openrouter.io/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": True, **kwargs}
            ) as response:
                async for line in response.aiter_lines():
                    if "content" in line:
                        yield json.loads(line.split("data: ")[1])["choices"][0]["delta"]["content"]

class AWSSageMakerProvider(LLMProvider):
    """AWS Bedrock"""
    async def complete(self, prompt: str, model: str = "anthropic.claude-v2", **kwargs) -> str:
        try:
            import boto3
            client = boto3.client("bedrock-runtime", region_name=self.config.get("region", "us-east-1"))
            response = client.invoke_model(
                modelId=model,
                body=json.dumps({"prompt": prompt, **kwargs})
            )
            return json.loads(response["body"].read())["completion"]
        except Exception as e:
            logger.error(f"Bedrock error: {e}")
            raise
    
    async def stream(self, prompt: str, model: str = "anthropic.claude-v2", **kwargs):
        import boto3
        client = boto3.client("bedrock-runtime")
        response = client.invoke_model_with_response_stream(
            modelId=model,
            body=json.dumps({"prompt": prompt, **kwargs})
        )
        for event in response["body"]:
            yield event.get("contentBlockDelta", {}).get("delta", {}).get("text", "")

class LMStudioProvider(LLMProvider):
    """Local LM Studio"""
    async def complete(self, prompt: str, model: str = "local", **kwargs) -> str:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://localhost:{self.config.get('port', 1234)}/v1/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        **kwargs
                    }
                )
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LM Studio error: {e}")
            raise
    
    async def stream(self, prompt: str, model: str = "local", **kwargs):
        import httpx
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"http://localhost:{self.config.get('port', 1234)}/v1/chat/completions",
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": True, **kwargs}
            ) as response:
                async for line in response.aiter_lines():
                    if "content" in line:
                        yield json.loads(line.split("data: ")[1])["choices"][0]["delta"]["content"]

class OllamaProvider(LLMProvider):
    """Local Ollama"""
    async def complete(self, prompt: str, model: str = "llama2", **kwargs) -> str:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://localhost:{self.config.get('port', 11434)}/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False, **kwargs}
                )
                return response.json()["response"]
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise
    
    async def stream(self, prompt: str, model: str = "llama2", **kwargs):
        import httpx
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"http://localhost:{self.config.get('port', 11434)}/api/generate",
                json={"model": model, "prompt": prompt, "stream": True, **kwargs}
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        yield json.loads(line).get("response", "")

class LLMFactory:
    """Create provider from config"""
    
    providers = {
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.ANTHROPIC: AnthropicProvider,
        ProviderType.GEMINI: GoogleGeminiProvider,
        ProviderType.OPENROUTER: OpenRouterProvider,
        ProviderType.AWS_BEDROCK: AWSSageMakerProvider,
        ProviderType.LM_STUDIO: LMStudioProvider,
        ProviderType.OLLAMA: OllamaProvider,
    }
    
    @staticmethod
    def create(provider_type: str, **kwargs) -> LLMProvider:
        """Create LLM provider from type and config"""
        provider_class = LLMFactory.providers.get(ProviderType(provider_type))
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_type}")
        return provider_class(**kwargs)
    
    @staticmethod
    def from_env() -> LLMProvider:
        """Load from environment variables"""
        provider = os.getenv("LLM_PROVIDER", "anthropic")
        api_key = os.getenv(f"{provider.upper()}_API_KEY")
        if not api_key:
            raise ValueError(f"Missing API key for {provider}")
        return LLMFactory.create(provider, api_key=api_key)
