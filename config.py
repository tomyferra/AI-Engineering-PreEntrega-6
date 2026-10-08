"""Punto único de configuración: rutas, límites del orquestador y settings del LLM leídos desde .env."""
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, SecretStr

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "data" / "docs"
TRACES_DIR = BASE_DIR / "traces"
DIAGRAMS_DIR = BASE_DIR / "docs"

# --- Orquestador ---
# Condición de parada dura contra el "supervisor infinito": cantidad máxima de delegaciones a especialistas.
# Al alcanzarla, el supervisor deja de delegar y pasa directo a la síntesis con lo que haya.
MAX_DELEGATIONS = 6
# Máximo de veces que se puede delegar en un mismo especialista (1 intento + refinamientos).
MAX_CALLS_PER_AGENT = 3
# Techo de seguridad de LangGraph (super-steps por invocación). Es un respaldo: el corte normal lo da
# MAX_DELEGATIONS; cada delegación consume 2 pasos (supervisor + especialista).
RECURSION_LIMIT = 2 * MAX_DELEGATIONS + 6
# Techo de pasos del loop ReAct interno de cada especialista (modelo <-> tools).
SPECIALIST_RECURSION_LIMIT = 12
# Largo máximo del resultado de cada tool call que se guarda en el estado como evidencia.
TOOL_RESULT_MAX_CHARS = 300

# --- Búsqueda en la base de conocimiento (BM25 sobre data/docs) ---
TOP_K = 4
CHUNK_MAX_CHARS = 1200


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"


DEFAULT_MODEL_POR_PROVIDER = {
    LLMProvider.OPENAI: "gpt-4o-mini",
    LLMProvider.ANTHROPIC: "claude-haiku-4-5",
    LLMProvider.GEMINI: "gemini-2.5-flash",
    LLMProvider.OPENROUTER: "openai/gpt-4o-mini",
}

ENV_VAR_POR_LLM_PROVIDER = {
    LLMProvider.OPENAI: "OPENAI_API_KEY",
    LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
    LLMProvider.GEMINI: "GEMINI_API_KEY",
    LLMProvider.OPENROUTER: "OPENROUTER_API_KEY",
}

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _require_env(nombre: str) -> str:
    valor = os.getenv(nombre)
    if not valor:
        raise ValueError(f"Falta la variable de entorno {nombre} (ver .env.example)")
    return valor


class LLMSettings(BaseModel):
    provider: LLMProvider
    model: str
    api_key: SecretStr
    temperature: float = Field(default=0.0, ge=0, le=2)
    max_tokens: int = Field(default=2048, gt=0)

    @property
    def label(self) -> str:
        return f"{self.provider.value}:{self.model}"


def get_llm_settings(provider: Optional[str] = None) -> LLMSettings:
    """Settings del LLM (llamar después de load_dotenv). LLM_MODEL pisa el modelo por defecto del provider."""
    proveedor = LLMProvider((provider or os.getenv("LLM_PROVIDER", "openai")).lower())
    return LLMSettings(
        provider=proveedor,
        model=os.getenv("LLM_MODEL") or DEFAULT_MODEL_POR_PROVIDER[proveedor],
        api_key=SecretStr(_require_env(ENV_VAR_POR_LLM_PROVIDER[proveedor])),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS") or 2048),
    )


def get_tavily_api_key() -> Optional[str]:
    """La búsqueda web es opcional: sin TAVILY_API_KEY el investigador usa solo la base de conocimiento local."""
    return os.getenv("TAVILY_API_KEY") or None
