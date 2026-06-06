import httpx
from core.config import settings
from loguru import logger

async def send_slack_alert(message: str) -> None:
    """
    Sends an alert message to the configured Slack Webhook URL.
    Fails silently (logged) to ensure alerts don't disrupt the application flow.
    """
    if not settings.SLACK_WEBHOOK_URL:
        return
        
    try:
        async with httpx.AsyncClient() as client:
            payload = {"text": message}
            response = await client.post(
                settings.SLACK_WEBHOOK_URL,
                json=payload,
                timeout=5.0
            )
            if response.status_code != 200:
                logger.error(f"Failed to send Slack alert. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Slack alert: {e}")
