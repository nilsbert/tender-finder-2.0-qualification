from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class AIProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"

class AIProviderSettings(BaseModel):
    provider: AIProvider
    is_active: bool = False
    model: str
    api_version: Optional[str] = None

    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)

class AIConnectorConfig(BaseModel):
    provider: AIProvider
    is_active: bool = False
    api_key: str
    endpoint: Optional[str] = None
    model: str
    api_version: Optional[str] = None
    available_models: Optional[List] = None

    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)

class TestConnectionResponse(BaseModel):
    success: bool
    message: str

    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)
