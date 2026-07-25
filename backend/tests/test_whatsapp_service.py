from unittest.mock import Mock, patch

from app.services.whatsapp_service import WhatsAppService


def test_normalize_phone_strips_non_digits():
    service = WhatsAppService()

    assert service._normalize_phone("+1 (555) 123-4567") == "15551234567"
    assert service._normalize_phone("0044 7700 900123") == "00447700900123"
    assert service._normalize_phone("12345") is None


def test_send_message_sync_returns_true_for_valid_response():
    service = WhatsAppService()
    fake_response = Mock(status_code=200)
    expected_headers = service._build_headers()

    with patch.object(service, "_request_with_retries", return_value=fake_response) as mocked_request:
        result = service.send_message_sync("test-instance", "+1 555 123 4567", "Hello")

    assert result is True
    mocked_request.assert_called_once()
    mocked_request.assert_called_with(
        "POST",
        f"{service.base_url}/message/sendText/test-instance",
        json={
            "number": "15551234567",
            "text": "Hello",
            "delay": 1200,
        },
        headers=expected_headers,
        timeout=15.0,
    )


def test_create_instance_sync_returns_json_response():
    service = WhatsAppService()
    fake_response = Mock()
    fake_response.json.return_value = {"success": True}
    expected_headers = service._build_headers()

    with patch.object(service, "_request_with_retries", return_value=fake_response) as mocked_request:
        result = service.create_instance_sync("test-instance")

    assert result == {"success": True}
    mocked_request.assert_called_once()
    mocked_request.assert_called_with(
        "POST",
        f"{service.base_url}/instance/create",
        json={"instanceName": "test-instance", "token": service.api_key, "qrcode": True},
        headers=expected_headers,
        timeout=10.0,
    )
