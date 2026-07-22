#!/usr/bin/env python3
"""Configuration system — AWS Secrets Manager + local overrides"""
import os, json, logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    provider: str  # openai, anthropic, gemini, etc.
    api_key: str
    model: str = "default"
    temperature: float = 0.7
    max_tokens: int = 2048

@dataclass
class AppConfig:
    environment: str  # dev, staging, prod
    workspace_dir: str
    aws_region: str = "us-east-1"
    debug: bool = False

class ConfigManager:
    """Load config from AWS Secrets Manager or environment"""
    
    def __init__(self, env: str = "dev"):
        self.environment = env
        self.local_config_path = os.path.expanduser("~/.rostr/config.json")
        self._load_config()
    
    def _load_config(self):
        """Load from Secrets Manager (prod) or local (dev)"""
        if self.environment == "prod":
            self._load_from_aws()
        else:
            self._load_from_local()
    
    def _load_from_local(self):
        """Load from ~/.rostr/config.json"""
        if os.path.exists(self.local_config_path):
            with open(self.local_config_path) as f:
                self.config = json.load(f)
            logger.info(f"Loaded local config: {self.local_config_path}")
        else:
            logger.info("No local config found, using environment variables")
            self.config = {}
    
    def _load_from_aws(self):
        """Load from AWS Secrets Manager"""
        try:
            import boto3
            client = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "us-east-1"))
            response = client.get_secret_value(SecretId="rostr/config")
            self.config = json.loads(response["SecretString"])
            logger.info("Loaded config from AWS Secrets Manager")
        except Exception as e:
            logger.warning(f"Failed to load from AWS: {e}, using environment")
            self.config = {}
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM provider config"""
        provider = self.config.get("llm_provider") or os.getenv("LLM_PROVIDER", "anthropic")
        api_key = self.config.get(f"{provider}_key") or os.getenv(f"{provider.upper()}_API_KEY")
        
        if not api_key:
            raise ValueError(f"Missing API key for {provider}")
        
        return LLMConfig(
            provider=provider,
            api_key=api_key,
            model=self.config.get("llm_model", "default"),
            temperature=float(self.config.get("llm_temperature", 0.7)),
            max_tokens=int(self.config.get("llm_max_tokens", 2048))
        )
    
    def get_app_config(self) -> AppConfig:
        """Get app config"""
        return AppConfig(
            environment=self.environment,
            workspace_dir=self.config.get("workspace_dir", os.path.expanduser("~/.rostr")),
            aws_region=self.config.get("aws_region", "us-east-1"),
            debug=self.config.get("debug", self.environment == "dev")
        )
    
    def save_local_config(self, llm_config: LLMConfig):
        """Save config locally"""
        os.makedirs(os.path.dirname(self.local_config_path), exist_ok=True)
        config = {
            "llm_provider": llm_config.provider,
            f"{llm_config.provider}_key": llm_config.api_key,
            "llm_model": llm_config.model,
            "llm_temperature": llm_config.temperature,
            "llm_max_tokens": llm_config.max_tokens,
        }
        with open(self.local_config_path, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved config to {self.local_config_path}")
