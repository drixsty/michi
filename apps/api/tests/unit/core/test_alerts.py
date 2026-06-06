import pytest
from unittest.mock import patch, AsyncMock
from core.security.alerts import send_slack_alert
from core.config.settings import settings

@pytest.mark.asyncio
async def test_send_slack_alert_no_webhook():
    # Force settings.SLACK_WEBHOOK_URL to empty
    with patch.object(settings, "SLACK_WEBHOOK_URL", ""):
        with patch("httpx.AsyncClient.post") as mock_post:
            await send_slack_alert("test message")
            # Should return immediately and not call httpx
            mock_post.assert_not_called()

@pytest.mark.asyncio
async def test_send_slack_alert_with_webhook():
    test_webhook = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
    with patch.object(settings, "SLACK_WEBHOOK_URL", test_webhook):
        # Mock the async client post method
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        
        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            await send_slack_alert("hello slack")
            
            # Assertions
            mock_post.assert_called_once_with(
                test_webhook,
                json={"text": "hello slack"},
                timeout=5.0
            )
