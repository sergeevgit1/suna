from fastapi import APIRouter, HTTPException, Depends, Query
import httpx
from typing import Dict

from core.utils.config import config
from core.utils.logger import logger
from core.utils.auth_utils import verify_and_get_user_id_from_jwt

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/models")
async def list_openai_compatible_models(
    account_id: str = Depends(verify_and_get_user_id_from_jwt),
    api_base: str | None = Query(None),
    api_key: str | None = Query(None),
) -> Dict:
    """
    Прокси-эндпоинт для получения списка моделей от OpenAI-совместимого провайдера.
    Использует OPENAI_COMPATIBLE_API_BASE и OPENAI_COMPATIBLE_API_KEY из конфигурации.
    """
    # Позволяем переопределить базу и ключ через query-параметры, иначе используем конфиг
    config_api_base = getattr(config, "OPENAI_COMPATIBLE_API_BASE", None)
    config_api_key = getattr(config, "OPENAI_COMPATIBLE_API_KEY", None)

    api_base = api_base or config_api_base
    api_key = api_key or config_api_key

    if not api_base or not api_key:
        logger.warning("OPENAI_COMPATIBLE_API_BASE или OPENAI_COMPATIBLE_API_KEY не настроены")
        raise HTTPException(status_code=400, detail="OpenAI-compatible provider is not configured")

    url = api_base.rstrip("/") + "/models"

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 401:
                raise HTTPException(status_code=401, detail="Unauthorized to provider /models")
            if resp.status_code >= 500:
                logger.error(f"Provider /models error {resp.status_code}: {resp.text}")
                raise HTTPException(status_code=502, detail="Provider error fetching models")
            resp.raise_for_status()
            data = resp.json()

        # OpenAI совместимый формат обычно: {"data": [{"id": "...", "object": "model", ...}]}
        raw_models = data.get("data") if isinstance(data, dict) else None
        if not isinstance(raw_models, list):
            # Попробуем альтернативные поля
            raw_models = data.get("models") if isinstance(data, dict) else []
            if not isinstance(raw_models, list):
                raw_models = []

        model_info = []
        for idx, m in enumerate(raw_models):
            mid = m.get("id") or m.get("name") or "unknown"
            # Префикс для роутера и конфигурации openai-compatible
            full_id = f"openai-compatible/{mid}"

            metadata = m.get("metadata") or {}
            display_name = metadata.get("name") or m.get("name") or mid

            # Контекст/макс. токены
            context_window = (
                m.get("context_window")
                or m.get("context_length")
                or metadata.get("context_length")
                or 128000
            )
            max_tokens = (
                m.get("max_model_len")
                or metadata.get("max_model_len")
                or context_window
            )

            # Стоимость (если провайдер возвращает per million tokens)
            input_cost = metadata.get("prompt_tokens_cost")
            output_cost = metadata.get("generated_tokens_cost")

            # Способности
            capabilities = []
            endpoints = metadata.get("endpoints") or []
            # Chat/Completions по наличию эндпойнтов
            for ep in endpoints:
                path = (ep or {}).get("path") or ""
                if "/chat/completions" in path and "chat" not in capabilities:
                    capabilities.append("chat")
                if "/completions" in path and "completions" not in capabilities:
                    capabilities.append("completions")
            # Доп. флаги
            if m.get("function_calling"):
                capabilities.append("function_calling")
            if m.get("structure_output") or m.get("structured_output"):
                capabilities.append("structured_output")

            # Подписка/доступ
            is_billable = bool(metadata.get("is_billable"))
            requires_subscription = is_billable

            # Простая эвристика выбора рекомендуемой: первая или бесплатная с function_calling
            recommended = False
            if idx == 0:
                recommended = True
            elif not is_billable and ("function_calling" in capabilities):
                recommended = True

            model_info.append({
                "id": full_id,
                "display_name": display_name,
                "short_name": mid,
                "requires_subscription": requires_subscription,
                "is_available": True,
                "input_cost_per_million_tokens": input_cost,
                "output_cost_per_million_tokens": output_cost,
                "max_tokens": max_tokens,
                "context_window": context_window,
                "capabilities": capabilities or ["chat"],
                "recommended": recommended,
                "priority": 100 - idx,
            })

        return {
            "models": model_info,
            "subscription_tier": "OpenAI-Compatible",
            "total_models": len(model_info),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list OpenAI-compatible models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch models from provider")
