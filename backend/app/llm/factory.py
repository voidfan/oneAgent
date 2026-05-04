"""LLM provider factory - supports 30+ providers via unified configuration."""
import json
import logging
from pathlib import Path
from typing import Optional
import uuid

from app.config import settings
from app.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

# Settings file path
SETTINGS_FILE = Path("/app/data/settings.json")


def _load_llm_config(tenant_id: Optional[uuid.UUID] = None) -> dict:
    """Load LLM configuration from tenant settings, settings.json, or environment variables.
    
    Priority:
    1. Tenant-specific settings (if tenant_id provided)
    2. Global settings.json
    3. Environment variables
    """
    # 1. Try tenant-specific settings first
    if tenant_id:
        try:
            from app.middleware.tenant import get_tenant_llm_config
            import asyncio
            
            # Run async function synchronously
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, get_tenant_llm_config(tenant_id))
                    tenant_config = future.result()
            else:
                tenant_config = asyncio.run(get_tenant_llm_config(tenant_id))
            
            if tenant_config and tenant_config.get("provider"):
                config = {
                    "provider": tenant_config.get("provider", "openai"),
                    "base_url": tenant_config.get("base_url", ""),
                    "api_key": tenant_config.get("api_key", ""),
                    "model": tenant_config.get("model", "gpt-4o"),
                }
                logger.info(f"Using tenant LLM config: tenant={tenant_id}, provider={config['provider']}, model={config['model']}")
                return config
        except Exception as e:
            logger.warning(f"Failed to load tenant LLM config: {e}")
    
    # 2. Try to load from settings.json
    logger.debug(f"Checking settings file: {SETTINGS_FILE}, exists: {SETTINGS_FILE.exists()}")
    
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                llm_config = data.get("llm", {})
                logger.debug(f"Loaded LLM config from file: provider={llm_config.get('provider')}, base_url={llm_config.get('base_url')}, model={llm_config.get('model')}")
                if llm_config.get("provider"):
                    config = {
                        "provider": llm_config.get("provider", "openai"),
                        "base_url": llm_config.get("base_url", ""),
                        "api_key": llm_config.get("api_key", ""),
                        "model": llm_config.get("model", "gpt-4o"),
                    }
                    logger.info(f"Using config from settings.json: {config['provider']}, {config['base_url']}, {config['model']}")
                    return config
        except Exception as e:
            logger.error(f"Error loading settings.json: {e}")
    
    # 3. Fall back to environment variables
    config = {
        "provider": settings.LLM_PROVIDER,
        "base_url": settings.LLM_BASE_URL or "",
        "api_key": settings.LLM_API_KEY or "",
        "model": settings.LLM_MODEL,
    }
    logger.info(f"Using config from env: {config['provider']}, {config['base_url']}, {config['model']}")
    return config


# Providers that use Anthropic API format
ANTHROPIC_PROVIDERS = {"anthropic"}

# Providers that use OpenAI-compatible API format (most providers)
OPENAI_COMPATIBLE_PROVIDERS = {
    "openai", "azure-openai", "deepseek", "moonshot", "zhipu", "baichuan",
    "minimax", "01ai", "stepfun", "groq", "together", "fireworks", "anyscale",
    "perplexity", "mistral", "cohere", "openrouter", "siliconflow", "volcengine",
    "aliyun-bailian", "tencent-hunyuan", "xunfei-spark", "nvidia-nim",
    "cloudflare-ai", "replicate", "lepton", "novita", "infini-ai",
    "ollama", "lmstudio", "localai", "vllm", "llamacpp",
}


def get_llm_provider(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    tenant_id: Optional[uuid.UUID] = None,
    **kwargs,
) -> BaseLLMProvider:
    """Create an LLM provider instance.

    Args:
        provider: Provider name. Defaults to settings.
        model: Model name override.
        api_key: API key override.
        base_url: Base URL override.
        tenant_id: Tenant ID for tenant-specific configuration.
        **kwargs: Additional provider-specific arguments.

    Returns:
        BaseLLMProvider instance.

    Raises:
        ValueError: If provider is not supported.
    """
    # Load config: tenant settings > settings.json > env
    # Auto-detect tenant from context if not provided
    if not tenant_id:
        from app.middleware.tenant import get_current_tenant_id
        tenant_id = get_current_tenant_id()
    
    config = _load_llm_config(tenant_id)
    
    # Use provided values or fall back to config
    provider = provider or config["provider"]
    model = model or config["model"]
    api_key = api_key or config["api_key"]
    base_url = base_url or config["base_url"]

    # Determine which provider class to use
    if provider in ANTHROPIC_PROVIDERS:
        from app.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider(
            model=model,
            api_key=api_key,
            base_url=base_url if base_url else None,
            **kwargs
        )
    elif provider == "local" or provider in {"ollama", "lmstudio", "localai", "vllm", "llamacpp"}:
        from app.llm.local_provider import LocalLLMProvider
        return LocalLLMProvider(
            model=model,
            base_url=base_url,
            **kwargs
        )
    else:
        # Default: OpenAI-compatible provider (covers most providers)
        from app.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(
            model=model,
            api_key=api_key,
            base_url=base_url if base_url else None,
            **kwargs
        )
