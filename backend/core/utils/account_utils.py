from core.utils.logger import logger


async def ensure_personal_account(client, user_id: str) -> None:
    """
    Гарантирует наличие личного аккаунта (basejump.accounts) для пользователя.

    Если записи нет, создаёт:
    - запись в basejump.accounts с id = user_id и personal_account = true
    - запись в basejump.account_user с ролью 'owner'
    """
    try:
        # Проверяем наличие аккаунта по первичному ключу (id == user_id)
        existing = (
            await client.schema("basejump")
            .table("accounts")
            .select("id")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        if existing.data:
            return

        # Создаём личный аккаунт; slug остаётся NULL при personal_account=true
        await client.schema("basejump").table("accounts").insert({
            "id": user_id,
            "primary_owner_user_id": user_id,
            "personal_account": True,
            # name необязателен, можно оставить NULL
        }).execute()

        # Добавляем владельца в account_user
        await client.schema("basejump").table("account_user").insert({
            "account_id": user_id,
            "user_id": user_id,
            "account_role": "owner",
        }).execute()

        logger.info(f"Auto-created personal account for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to ensure personal account for {user_id}: {e}")
        # Не прерываем выполнение — пусть вызывающий код обработает возможные ошибки вставки позже

