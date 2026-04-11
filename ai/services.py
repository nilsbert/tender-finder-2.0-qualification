import logging
import os
import json
import asyncio
from typing import Optional, Tuple
from .core.database import db
from .models import AIProvider, AIConnectorConfig, AIProviderSettings, TestConnectionResponse

logger = logging.getLogger(__name__)

class LLMService:
    """
    Refactored AI logic for the Qualification Microservice.
    Uses local database for settings and environment variables for secrets.
    """
    _client: Optional[any] = None
    _last_config_hash: Optional[int] = None

    def __init__(self):
        self._lock = asyncio.Lock()
    
    def _default_model_for(self, provider: AIProvider) -> str:
        if provider == AIProvider.OPENAI:
            return os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        return "unknown"

    def _env_credentials_for(self, provider: AIProvider) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Returns (api_key, endpoint, api_version, credential_source).
        """
        if provider == AIProvider.OPENAI:
            azure_key = os.getenv("AZURE_OPENAI_API_KEY")
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
            
            if azure_key and azure_endpoint:
                return azure_key, azure_endpoint, azure_api_version, "env:AZURE_OPENAI_*"
            
            logger.warning("Azure OpenAI credentials not found in environment.")
            return None, None, None, None

        return None, None, None, None

    async def get_settings(self, provider: AIProvider) -> AIProviderSettings:
        config_id = f"ai_config_{provider.value}"
        config_dict = await db.get_config(config_id)
        
        env_key, _, _, _ = self._env_credentials_for(provider)
        has_env_creds = bool(env_key)

        if isinstance(config_dict, dict) and config_dict:
            allowed = {k: config_dict.get(k) for k in ("provider", "is_active", "model", "api_version")}
            allowed["provider"] = provider
            allowed["is_active"] = bool(allowed.get("is_active", False))
            allowed["model"] = allowed.get("model") or self._default_model_for(provider)
            return AIProviderSettings(**allowed)

        return AIProviderSettings(
            provider=provider, 
            is_active=has_env_creds, 
            model=self._default_model_for(provider)
        )

    async def get_runtime_config(self, provider: AIProvider) -> Optional[AIConnectorConfig]:
        settings = await self.get_settings(provider)
        api_key, endpoint, api_version, _ = self._env_credentials_for(provider)
        
        if not api_key:
            return None

        return AIConnectorConfig(
            provider=provider,
            is_active=settings.is_active,
            api_key=api_key,
            endpoint=endpoint,
            model=settings.model,
            api_version=settings.api_version or api_version,
        )

    async def get_active_provider_config(self) -> Optional[AIConnectorConfig]:
        """Prioritizes OpenAI as the active provider."""
        return await self.get_runtime_config(AIProvider.OPENAI)

    async def generate_text(self, config: AIConnectorConfig, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """Isolated generate_text call using Azure OpenAI."""
        if config.provider != AIProvider.OPENAI:
            raise ValueError(f"Unsupported provider: {config.provider}")
            
        from openai import AsyncAzureOpenAI

        # Lazy initialize or re-initialize client if config changed
        config_hash = hash((config.endpoint, config.api_key, config.api_version, config.model))
        
        async with self._lock:
            if self._client is None or self._last_config_hash != config_hash:
                endpoint = config.endpoint.strip() if config.endpoint else None
                if endpoint:
                     if not endpoint.startswith('http'):
                        endpoint = f"https://{endpoint}.openai.azure.com"
                     else:
                        endpoint = endpoint.rstrip('/')
                
                self._client = AsyncAzureOpenAI(
                    api_key=config.api_key,
                    api_version=config.api_version or "2024-02-01",
                    azure_endpoint=endpoint,
                    timeout=120.0
                )
                self._last_config_hash = config_hash
                logger.info(f"Initialized new AsyncAzureOpenAI client for {config.endpoint}")

        payload = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = await self._client.chat.completions.create(**payload)
        return response.choices[0].message.content
