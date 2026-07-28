import httpx
import time
import asyncio
from typing import Optional, Dict, Any, List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class WhatsAppService:
    MAX_RETRIES = 3
    RETRY_BACKOFF_SECONDS = 1.5

    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL.rstrip('/')
        self.api_key = settings.EVOLUTION_API_KEY

    def _build_headers(self, instance_token: Optional[str] = None) -> Dict[str, str]:
        token = instance_token or self.api_key
        return {
            "apikey": token,
            # Some Evolution deployments and proxies inspect Authorization even
            # though v2.3.7 primarily authenticates via the `apikey` header.
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _normalize_phone(self, phone: str) -> Optional[str]:
        if not phone:
            return None
        digits = "".join(ch for ch in phone if ch.isdigit())
        if len(digits) < 10:
            return None
        return digits

    def _request_with_retries(self, method: str, url: str, **kwargs) -> httpx.Response:
        last_exception = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                with httpx.Client(timeout=kwargs.pop("timeout", 15.0)) as client:
                    response = client.request(method, url, **kwargs)
                    if response.status_code in {400, 428} and "Connection Closed" in response.text:
                        if attempt < self.MAX_RETRIES:
                            logger.warning(f"Connection Closed on {url}, attempting to restart instance (attempt {attempt})...")
                            self._attempt_restart_from_url(url)
                            time.sleep(5)  # wait for connection to establish
                            continue
                    response.raise_for_status()
                    return response
            except httpx.HTTPStatusError as exc:
                last_exception = exc
                status_code = exc.response.status_code
                if status_code in {429, 428, 500, 502, 503, 504} and attempt < self.MAX_RETRIES:
                    backoff = self.RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
                    logger.warning(
                        f"WhatsApp request failed with status {status_code}. Retrying in {backoff:.1f}s (attempt {attempt})"
                    )
                    time.sleep(backoff)
                    continue
                raise
            except Exception as exc:
                last_exception = exc
                if attempt < self.MAX_RETRIES:
                    backoff = self.RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
                    logger.warning(
                        f"WhatsApp request error: {exc}. Retrying in {backoff:.1f}s (attempt {attempt})"
                    )
                    time.sleep(backoff)
                    continue
                raise

        raise last_exception

    def _attempt_restart_from_url(self, url: str):
        try:
            instance_name = url.rstrip("/").split("/")[-1]
            restart_url = f"{self.base_url}/instance/restart/{instance_name}"
            with httpx.Client() as client:
                res = client.put(restart_url, headers=self._build_headers(), timeout=10.0)
                if res.status_code in {404, 405}: # Method Not Allowed or Not Found
                    client.post(restart_url, headers=self._build_headers(), timeout=10.0)
        except Exception as e:
            logger.error(f"Failed to auto-restart instance: {e}")

    def ensure_instance_sync(self, instance_name: str) -> bool:
        """Create the instance only when it does not already exist."""
        state_url = f"{self.base_url}/instance/connectionState/{instance_name}"
        try:
            response = self._request_with_retries(
                "GET",
                state_url,
                headers=self._build_headers(),
                timeout=5.0,
            )
            return response.status_code == 200
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 404:
                logger.error(
                    "Failed to verify Evolution instance %s: %s - %s",
                    instance_name,
                    exc,
                    exc.response.text,
                )
                return False
        except Exception as exc:
            logger.error(f"Failed to verify Evolution instance {instance_name}: {exc}")
            return False

        created = self.create_instance_sync(instance_name)
        return created is not None

    def create_instance_sync(self, instance_name: str) -> Optional[Dict[str, Any]]:
        """Create a new WhatsApp instance synchronously."""
        url = f"{self.base_url}/instance/create"
        payload = {
            "instanceName": instance_name,
            "token": self.api_key,
            "integration": "WHATSAPP-BAILEYS",
            "qrcode": True
        }
        try:
            response = self._request_with_retries(
                "POST",
                url,
                json=payload,
                headers=self._build_headers(),
                timeout=10.0,
            )
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to create Evolution instance %s: %s - %s",
                instance_name,
                e,
                e.response.text,
            )
            return None
        except Exception as e:
            logger.error(f"Failed to create Evolution instance {instance_name}: {e}")
            return None

    async def create_instance(self, instance_name: str) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self.create_instance_sync, instance_name)

    async def get_instance_state(self, instance_name: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/instance/connectionState/{instance_name}"
        try:
            response = await asyncio.to_thread(
                self._request_with_retries,
                "GET",
                url,
                headers=self._build_headers(),
                timeout=5.0,
            )
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get state for {instance_name}: {e}")
            return None

    def check_whatsapp_numbers_sync(self, instance_name: str, numbers: List[str]) -> Dict[str, bool]:
        normalized_numbers = [self._normalize_phone(number) for number in numbers]
        valid_numbers = [number for number in normalized_numbers if number]
        if not valid_numbers:
            return {}

        url = f"{self.base_url}/chat/whatsappNumbers/{instance_name}"
        payload = {"numbers": valid_numbers}

        try:
            response = self._request_with_retries(
                "POST",
                url,
                json=payload,
                headers=self._build_headers(),
                timeout=10.0,
            )
            data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "Error checking WhatsApp numbers on instance %s: %s - %s",
                instance_name,
                e,
                e.response.text,
            )
            return {}
        except Exception as e:
            logger.error(f"Error checking WhatsApp numbers on instance {instance_name}: {e}")
            return {}

        results: Dict[str, bool] = {}
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                number = self._normalize_phone(str(item.get("number", "")))
                exists = bool(
                    item.get("exists")
                    or item.get("isWhatsapp")
                    or item.get("isBusiness")
                    or item.get("jid")
                )
                if number:
                    results[number] = exists

        return results

    def is_whatsapp_number_sync(self, instance_name: str, phone: str) -> Optional[bool]:
        normalized_phone = self._normalize_phone(phone)
        if not normalized_phone:
            return False

        results = self.check_whatsapp_numbers_sync(instance_name, [normalized_phone])
        if normalized_phone not in results:
            return None
        return results[normalized_phone]

    def send_message_sync(self, instance_name: str, phone: str, message: str) -> bool:
        """Send a text message via WhatsApp synchronously."""
        formatted_phone = self._normalize_phone(phone)
        if not formatted_phone:
            logger.error(f"Invalid WhatsApp phone number: {phone}")
            return False

        url = f"{self.base_url}/message/sendText/{instance_name}"
        payload = {
            "number": formatted_phone,
            "text": message,
            "delay": 1200,
        }

        try:
            response = self._request_with_retries(
                "POST",
                url,
                json=payload,
                headers=self._build_headers(),
                timeout=15.0,
            )
            return response.status_code in {200, 201}
        except httpx.HTTPStatusError as e:
            logger.error(
                "Error sending WhatsApp message to %s: %s - %s",
                phone,
                e,
                e.response.text,
            )
            return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp message to {phone}: {e}")
            return False

    async def send_message(self, instance_name: str, phone: str, message: str) -> bool:
        return await asyncio.to_thread(self.send_message_sync, instance_name, phone, message)

    def send_media_sync(self, instance_name: str, phone: str, media: str, mediatype: str, mimetype: str, caption: Optional[str] = None) -> bool:
        """Send a media message via WhatsApp synchronously."""
        formatted_phone = self._normalize_phone(phone)
        if not formatted_phone:
            logger.error(f"Invalid WhatsApp phone number: {phone}")
            return False

        url = f"{self.base_url}/message/sendMedia/{instance_name}"
        payload = {
            "number": formatted_phone,
            "mediatype": mediatype,
            "mimetype": mimetype,
            "media": media,
        }
        if caption:
            payload["caption"] = caption

        try:
            response = self._request_with_retries(
                "POST",
                url,
                json=payload,
                headers=self._build_headers(),
                timeout=30.0,
            )
            return response.status_code in {200, 201}
        except httpx.HTTPStatusError as e:
            logger.error(
                "Error sending WhatsApp media to %s: %s - %s",
                phone,
                e,
                e.response.text,
            )
            return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp media to {phone}: {e}")
            return False

    async def send_media(self, instance_name: str, phone: str, media: str, mediatype: str, mimetype: str, caption: Optional[str] = None) -> bool:
        return await asyncio.to_thread(self.send_media_sync, instance_name, phone, media, mediatype, mimetype, caption)

    def send_poll_sync(self, instance_name: str, phone: str, name: str, values: List[str], selectable_count: int = 1) -> bool:
        """Send a poll message via WhatsApp synchronously."""
        formatted_phone = self._normalize_phone(phone)
        if not formatted_phone:
            logger.error(f"Invalid WhatsApp phone number: {phone}")
            return False

        url = f"{self.base_url}/message/sendPoll/{instance_name}"
        payload = {
            "number": formatted_phone,
            "name": name,
            "values": values,
            "selectableCount": selectable_count,
        }

        try:
            response = self._request_with_retries(
                "POST",
                url,
                json=payload,
                headers=self._build_headers(),
                timeout=15.0,
            )
            return response.status_code in {200, 201}
        except httpx.HTTPStatusError as e:
            logger.error(
                "Error sending WhatsApp poll to %s: %s - %s",
                phone,
                e,
                e.response.text,
            )
            return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp poll to {phone}: {e}")
            return False

    async def send_poll(self, instance_name: str, phone: str, name: str, values: List[str], selectable_count: int = 1) -> bool:
        return await asyncio.to_thread(self.send_poll_sync, instance_name, phone, name, values, selectable_count)

whatsapp_service = WhatsAppService()
