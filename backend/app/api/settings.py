"""
Settings API - 系统配置管理接口
支持通过 UI 界面配置所有系统参数
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import json
import os

router = APIRouter(prefix="/api/settings", tags=["settings"])

# ==================== LLM 提供商定义 ====================

# 所有支持的 API 提供商及其配置元数据
LLM_PROVIDERS = {
    "amazon_bedrock": {
        "label": "Amazon Bedrock",
        "default_base_url": "https://bedrock-runtime.us-east-1.amazonaws.com",
        "requires_api_key": True,
        "requires_base_url": True,
        "models": [
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-opus-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
            "meta.llama3-70b-instruct-v1:0",
            "mistral.mixtral-8x7b-instruct-v0:1",
            "amazon.titan-text-express-v1",
        ],
        "default_model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "description": "AWS 托管的多模型服务",
    },
    "anthropic": {
        "label": "Anthropic",
        "default_base_url": "https://api.anthropic.com",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ],
        "default_model": "claude-sonnet-4-20250514",
        "description": "Claude 系列模型",
    },
    "baseten": {
        "label": "Baseten",
        "default_base_url": "https://app.baseten.co",
        "requires_api_key": True,
        "requires_base_url": True,
        "models": [],
        "default_model": "",
        "description": "自定义模型部署平台",
    },
    "claude_code": {
        "label": "Claude Code",
        "default_base_url": "https://api.anthropic.com",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
        ],
        "default_model": "claude-sonnet-4-20250514",
        "description": "Anthropic Claude Code 专用",
    },
    "deepseek": {
        "label": "DeepSeek",
        "default_base_url": "https://api.deepseek.com",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "deepseek-chat",
            "deepseek-coder",
            "deepseek-reasoner",
        ],
        "default_model": "deepseek-chat",
        "description": "DeepSeek 系列模型",
    },
    "fireworks": {
        "label": "Fireworks AI",
        "default_base_url": "https://api.fireworks.ai/inference/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "accounts/fireworks/models/llama-v3p1-405b-instruct",
            "accounts/fireworks/models/llama-v3p1-70b-instruct",
            "accounts/fireworks/models/mixtral-8x22b-instruct",
            "accounts/fireworks/models/qwen2-72b-instruct",
        ],
        "default_model": "accounts/fireworks/models/llama-v3p1-70b-instruct",
        "description": "高性能推理平台",
    },
    "gcp_vertex": {
        "label": "GCP Vertex AI",
        "default_base_url": "https://us-central1-aiplatform.googleapis.com",
        "requires_api_key": True,
        "requires_base_url": True,
        "models": [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
            "claude-3-5-sonnet@20241022",
            "claude-3-opus@20240229",
        ],
        "default_model": "gemini-1.5-pro",
        "description": "Google Cloud AI 平台",
    },
    "gemini_cli": {
        "label": "Gemini CLI",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
        ],
        "default_model": "gemini-1.5-pro",
        "description": "Google Gemini CLI 接口",
    },
    "google_gemini": {
        "label": "Google Gemini",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-1.0-pro",
        ],
        "default_model": "gemini-2.0-flash",
        "description": "Google Gemini API",
    },
    "human_relay": {
        "label": "Human Relay",
        "default_base_url": "",
        "requires_api_key": False,
        "requires_base_url": False,
        "models": ["human"],
        "default_model": "human",
        "description": "人工中继模式",
    },
    "litellm": {
        "label": "LiteLLM",
        "default_base_url": "http://localhost:4000",
        "requires_api_key": True,
        "requires_base_url": True,
        "models": [],
        "default_model": "",
        "description": "LLM 代理网关，支持 100+ 模型",
    },
    "lm_studio": {
        "label": "LM Studio",
        "default_base_url": "http://localhost:1234/v1",
        "requires_api_key": False,
        "requires_base_url": True,
        "models": [],
        "default_model": "",
        "description": "本地模型运行工具",
    },
    "minimax": {
        "label": "MiniMax",
        "default_base_url": "https://api.minimax.chat/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "abab6.5s-chat",
            "abab6.5-chat",
            "abab5.5-chat",
        ],
        "default_model": "abab6.5s-chat",
        "description": "MiniMax 系列模型",
    },
    "mistral": {
        "label": "Mistral",
        "default_base_url": "https://api.mistral.ai/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "open-mixtral-8x22b",
            "open-mixtral-8x7b",
            "codestral-latest",
        ],
        "default_model": "mistral-large-latest",
        "description": "Mistral AI 系列模型",
    },
    "moonshot": {
        "label": "Moonshot",
        "default_base_url": "https://api.moonshot.cn/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "moonshot-v1-128k",
            "moonshot-v1-32k",
            "moonshot-v1-8k",
        ],
        "default_model": "moonshot-v1-128k",
        "description": "月之暗面 Kimi 系列模型",
    },
    "ollama": {
        "label": "Ollama",
        "default_base_url": "http://localhost:11434",
        "requires_api_key": False,
        "requires_base_url": True,
        "models": [
            "llama3.1",
            "llama3.1:70b",
            "llama3",
            "mistral",
            "mixtral",
            "codellama",
            "qwen2",
            "qwen2.5",
            "phi3",
            "gemma2",
            "deepseek-coder-v2",
        ],
        "default_model": "llama3.1",
        "description": "本地运行开源模型",
    },
    "openai": {
        "label": "OpenAI",
        "default_base_url": "https://api.openai.com/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini",
        ],
        "default_model": "gpt-4o",
        "description": "OpenAI GPT 系列模型",
    },
    "openai_chatgpt": {
        "label": "OpenAI - ChatGPT Plus/Pro",
        "default_base_url": "https://api.openai.com/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "o1-preview",
            "o1-mini",
        ],
        "default_model": "gpt-4o",
        "description": "ChatGPT Plus/Pro 订阅用户",
    },
    "openai_compatible": {
        "label": "OpenAI Compatible",
        "default_base_url": "",
        "requires_api_key": True,
        "requires_base_url": True,
        "models": [],
        "default_model": "",
        "description": "兼容 OpenAI API 格式的第三方服务",
    },
    "openrouter": {
        "label": "OpenRouter",
        "default_base_url": "https://openrouter.ai/api/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "google/gemini-pro-1.5",
            "meta-llama/llama-3.1-405b-instruct",
            "mistralai/mixtral-8x22b-instruct",
            "deepseek/deepseek-chat",
        ],
        "default_model": "anthropic/claude-3.5-sonnet",
        "description": "多模型聚合路由",
    },
    "qwen_code": {
        "label": "Qwen Code",
        "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "qwen-max",
            "qwen-plus",
            "qwen-turbo",
            "qwen-long",
            "qwen-coder-plus",
            "qwen2.5-coder-32b-instruct",
        ],
        "default_model": "qwen-max",
        "description": "阿里通义千问系列模型",
    },
    "requesty": {
        "label": "Requesty",
        "default_base_url": "https://router.requesty.ai/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [],
        "default_model": "",
        "description": "AI 请求路由服务",
    },
    "sambanova": {
        "label": "SambaNova",
        "default_base_url": "https://api.sambanova.ai/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "Meta-Llama-3.1-405B-Instruct",
            "Meta-Llama-3.1-70B-Instruct",
            "Meta-Llama-3.1-8B-Instruct",
        ],
        "default_model": "Meta-Llama-3.1-70B-Instruct",
        "description": "SambaNova 高性能推理",
    },
    "unbound": {
        "label": "Unbound",
        "default_base_url": "https://api.getunbound.ai/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [],
        "default_model": "",
        "description": "Unbound AI 服务",
    },
    "vercel_ai_gateway": {
        "label": "Vercel AI Gateway",
        "default_base_url": "",
        "requires_api_key": True,
        "requires_base_url": True,
        "models": [],
        "default_model": "",
        "description": "Vercel AI SDK 网关",
    },
    "vscode_lm_api": {
        "label": "VS Code LM API",
        "default_base_url": "",
        "requires_api_key": False,
        "requires_base_url": False,
        "models": ["copilot-gpt-4o", "copilot-gpt-3.5-turbo"],
        "default_model": "copilot-gpt-4o",
        "description": "VS Code 内置语言模型 API",
    },
    "xai": {
        "label": "xAI (Grok)",
        "default_base_url": "https://api.x.ai/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [
            "grok-2",
            "grok-2-mini",
            "grok-beta",
        ],
        "default_model": "grok-2",
        "description": "xAI Grok 系列模型",
    },
    "zai": {
        "label": "Z.ai",
        "default_base_url": "https://api.z.ai/v1",
        "requires_api_key": True,
        "requires_base_url": False,
        "models": [],
        "default_model": "",
        "description": "Z.ai 服务",
    },
}


# ==================== Schemas ====================

class LLMProviderConfig(BaseModel):
    """LLM 提供商配置 - 4 个核心配置项"""
    provider: str = Field(..., description="API 提供商标识")
    base_url: Optional[str] = Field(None, description="API Base URL")
    api_key: Optional[str] = Field(None, description="API 密钥 (显示时脱敏)")
    model: str = Field("", description="使用的模型")
    enabled: bool = Field(True, description="是否启用")

class AgentDefaultConfig(BaseModel):
    max_iterations: int = Field(10, ge=1, le=100)
    default_provider: str = Field("openai")
    default_model: str = Field("gpt-4o")
    default_temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(4096, ge=1, le=128000)
    enable_reflection: bool = Field(True)
    reflection_interval: int = Field(3, ge=1, le=20)
    enable_planning: bool = Field(True)

class ToolConfig(BaseModel):
    name: str
    enabled: bool = True
    requires_approval: bool = False
    timeout: int = Field(30, ge=1, le=300)
    config: Dict[str, Any] = Field(default_factory=dict)

class MemoryConfig(BaseModel):
    short_term_max_tokens: int = Field(4000, ge=500, le=128000)
    long_term_enabled: bool = Field(True)
    long_term_collection: str = Field("xagent_memory")
    long_term_top_k: int = Field(5, ge=1, le=50)
    working_memory_enabled: bool = Field(True)

class ObservabilityConfig(BaseModel):
    log_level: str = Field("INFO", description="日志级别: DEBUG, INFO, WARNING, ERROR")
    enable_tracing: bool = Field(True)
    enable_metrics: bool = Field(True)
    trace_retention_hours: int = Field(24, ge=1, le=720)

class SecurityConfig(BaseModel):
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    enable_auth: bool = Field(False)
    api_rate_limit: int = Field(100, ge=1, le=10000, description="每分钟请求限制")

class SystemSettings(BaseModel):
    llm: LLMProviderConfig = Field(default_factory=lambda: LLMProviderConfig(provider="openai"))
    agent_defaults: AgentDefaultConfig = Field(default_factory=AgentDefaultConfig)
    tools: List[ToolConfig] = Field(default_factory=list)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

class SettingUpdateRequest(BaseModel):
    section: str = Field(..., description="配置区域: llm, agent_defaults, tools, memory, observability, security")
    data: Any = Field(..., description="配置数据")


# ==================== In-memory settings store ====================

SETTINGS_DIR = "/app/data"
SETTINGS_FILE = f"{SETTINGS_DIR}/settings.json"

# Ensure settings directory exists
os.makedirs(SETTINGS_DIR, exist_ok=True)


def _get_default_settings() -> dict:
    """Generate default settings from environment variables"""
    provider = os.getenv("LLM_PROVIDER", "openai")
    provider_meta = LLM_PROVIDERS.get(provider, LLM_PROVIDERS["openai"])

    return SystemSettings(
        llm=LLMProviderConfig(
            provider=provider,
            base_url=os.getenv("LLM_BASE_URL", provider_meta["default_base_url"]) or provider_meta["default_base_url"],
            api_key=os.getenv("LLM_API_KEY", ""),
            model=os.getenv("LLM_MODEL", provider_meta["default_model"]) or provider_meta["default_model"],
            enabled=True,
        ),
        agent_defaults=AgentDefaultConfig(
            default_provider=provider,
            default_model=os.getenv("LLM_MODEL", provider_meta["default_model"]) or provider_meta["default_model"],
        ),
        tools=[
            ToolConfig(name="web_search", enabled=True, requires_approval=False, timeout=30),
            ToolConfig(name="calculator", enabled=True, requires_approval=False, timeout=10),
            ToolConfig(name="code_executor", enabled=True, requires_approval=True, timeout=60),
            ToolConfig(name="file_reader", enabled=True, requires_approval=False, timeout=15),
        ],
        memory=MemoryConfig(),
        observability=ObservabilityConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        ),
        security=SecurityConfig(),
    ).model_dump()


def _mask_key(key: str) -> str:
    """Mask API key for display"""
    if not key or len(key) < 8:
        return ""
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


_settings_cache: dict = {}


def _load_settings() -> dict:
    global _settings_cache
    if _settings_cache:
        return _settings_cache

    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                _settings_cache = json.load(f)
                return _settings_cache
    except Exception:
        pass

    _settings_cache = _get_default_settings()
    return _settings_cache


def _save_settings(settings: dict):
    global _settings_cache
    _settings_cache = settings
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save settings to file: {e}")


# ==================== Routes ====================

@router.get("", response_model=dict)
async def get_all_settings():
    """获取所有系统配置"""
    return _load_settings()


@router.get("/providers", response_model=dict)
async def get_llm_providers():
    """获取所有支持的 LLM 提供商及其元数据"""
    return {"providers": LLM_PROVIDERS}


@router.get("/providers/{provider_id}")
async def get_provider_info(provider_id: str):
    """获取指定提供商的详细信息"""
    if provider_id not in LLM_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"提供商 '{provider_id}' 不存在")
    return {"provider_id": provider_id, **LLM_PROVIDERS[provider_id]}


@router.get("/providers/{provider_id}/models")
async def get_provider_models(provider_id: str):
    """获取指定提供商的可用模型列表"""
    if provider_id not in LLM_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"提供商 '{provider_id}' 不存在")
    meta = LLM_PROVIDERS[provider_id]
    return {
        "provider_id": provider_id,
        "models": meta["models"],
        "default_model": meta["default_model"],
    }


@router.get("/{section}")
async def get_settings_section(section: str):
    """获取指定配置区域"""
    settings = _load_settings()
    if section not in settings:
        raise HTTPException(status_code=404, detail=f"配置区域 '{section}' 不存在")
    return {section: settings[section]}


@router.put("/{section}")
async def update_settings_section(section: str, data: dict):
    """更新指定配置区域"""
    settings = _load_settings()
    if section not in settings:
        raise HTTPException(status_code=404, detail=f"配置区域 '{section}' 不存在")

    # Handle API key updates - if masked, keep original
    if section == "llm":
        llm_data = data.get("llm", data)
        if isinstance(llm_data, dict):
            api_key = llm_data.get("api_key", "")
            if api_key and "****" in str(api_key):
                # Keep original key
                llm_data["api_key"] = settings.get("llm", {}).get("api_key", "")

    settings[section] = data.get(section, data)
    _save_settings(settings)

    # Apply runtime changes
    await _apply_settings(section, settings[section])

    return {"status": "ok", "message": f"配置区域 '{section}' 已更新"}


@router.post("/reset")
async def reset_settings():
    """重置所有配置为默认值"""
    global _settings_cache
    _settings_cache = _get_default_settings()
    _save_settings(_settings_cache)
    return {"status": "ok", "message": "配置已重置为默认值"}


@router.post("/test-llm")
async def test_llm_connection(
    provider: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
):
    """测试 LLM 连接"""
    try:
        # 获取提供商元数据
        provider_meta = LLM_PROVIDERS.get(provider)
        if not provider_meta:
            return {
                "status": "error",
                "message": f"不支持的提供商: {provider}",
            }

        # 获取当前保存的配置
        settings = _load_settings()
        llm_config = settings.get("llm", {})

        # 使用传入参数或已保存的配置
        actual_api_key = api_key or llm_config.get("api_key", "")
        actual_base_url = base_url or llm_config.get("base_url", "") or provider_meta["default_base_url"]
        actual_model = model or llm_config.get("model", "") or provider_meta["default_model"]

        # 对于需要 API Key 的提供商，检查是否已配置
        if provider_meta["requires_api_key"] and not actual_api_key:
            return {
                "status": "error",
                "message": "未配置 API 密钥",
            }

        # 尝试使用 OpenAI 兼容接口测试（大多数提供商兼容）
        import httpx

        headers = {
            "Content-Type": "application/json",
        }

        # 根据提供商设置认证头
        if actual_api_key:
            if provider in ("anthropic", "claude_code"):
                headers["x-api-key"] = actual_api_key
                headers["anthropic-version"] = "2023-06-01"
                # Anthropic 使用不同的 API 格式
                test_url = f"{actual_base_url}/v1/messages"
                test_body = {
                    "model": actual_model,
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Say hello in one word."}],
                }
            else:
                headers["Authorization"] = f"Bearer {actual_api_key}"
                test_url = f"{actual_base_url}/chat/completions"
                test_body = {
                    "model": actual_model,
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Say hello in one word."}],
                }
        else:
            # 无需 API Key 的提供商（如 Ollama, LM Studio）
            test_url = f"{actual_base_url}/v1/chat/completions"
            test_body = {
                "model": actual_model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Say hello in one word."}],
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(test_url, json=test_body, headers=headers)

            if response.status_code == 200:
                result = response.json()
                # 提取响应内容
                content = ""
                if "content" in result:
                    # Anthropic 格式
                    content = result["content"][0]["text"] if result["content"] else ""
                elif "choices" in result:
                    # OpenAI 格式
                    content = result["choices"][0]["message"]["content"] if result["choices"] else ""

                return {
                    "status": "success",
                    "message": "连接成功",
                    "response": content[:100],
                    "model": actual_model,
                }
            else:
                error_text = response.text[:200]
                return {
                    "status": "error",
                    "message": f"连接失败 (HTTP {response.status_code}): {error_text}",
                }

    except httpx.ConnectError:
        return {
            "status": "error",
            "message": f"无法连接到 {actual_base_url}，请检查 Base URL 是否正确",
        }
    except httpx.TimeoutException:
        return {
            "status": "error",
            "message": "连接超时，请检查网络或 Base URL",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"连接失败: {str(e)}",
        }


# 保留旧路由兼容性
@router.get("/llm/models/{provider}")
async def get_available_models(provider: str):
    """获取指定提供商的可用模型列表（兼容旧接口）"""
    if provider in LLM_PROVIDERS:
        meta = LLM_PROVIDERS[provider]
        return {"provider": provider, "models": meta["models"]}
    return {"provider": provider, "models": []}


async def _apply_settings(section: str, data: Any):
    """Apply settings changes at runtime"""
    if section == "observability":
        import logging
        level = getattr(logging, data.get("log_level", "INFO"), logging.INFO)
        logging.getLogger().setLevel(level)
    # Other runtime changes can be applied here
