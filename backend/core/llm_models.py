from fastapi import APIRouter, HTTPException, Depends
import httpx
from typing import Dict

from core.utils.config import config
from core.utils.logger import logger
from core.utils.auth_utils import verify_and_get_user_id_from_jwt

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/models")
async def list_openai_compatible_models(
    account_id: str = Depends(verify_and_get_user_id_from_jwt)
) -> Dict:
    """
    Прокси-эндпоинт для получения списка моделей от OpenAI-совместимого провайдера.
    Использует OPENAI_COMPATIBLE_API_BASE и OPENAI_COMPATIBLE_API_KEY из конфигурации.
    """
    api_base = getattr(config, "OPENAI_COMPATIBLE_API_BASE", None)
    api_key = getattr(config, "OPENAI_COMPATIBLE_API_KEY", None)

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
            # Важно: префикс для роутера и конфигурации openai-compatible
            full_id = f"openai-compatible/{mid}"

            display_name = m.get("name") or mid
            context_window = m.get("context_window") or m.get("context_length") or 128000

            model_info.append({
                "id": full_id,
                "display_name": display_name,
                "short_name": mid,
                "requires_subscription": False,
                "input_cost_per_million_tokens": None,
                "output_cost_per_million_tokens": None,
                "context_window": context_window,
                "capabilities": ["chat"],
                "recommended": idx == 0,  # первую модель считаем рекомендуемой
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

