"""Main client for RoboKassa API."""

import gc
import logging
from typing import Optional

import aiohttp

from aiorobokassa.api.base import BaseAPIClient
from aiorobokassa.api.invoice import InvoiceMixin
from aiorobokassa.api.payment import PaymentMixin
from aiorobokassa.api.refund import RefundMixin
from aiorobokassa.constants import (
    MIN_PASSWORD_LENGTH,
    PRODUCTION_BASE_URL as PROD_URL,
    TEST_BASE_URL as TEST_URL,
)
from aiorobokassa.exceptions import ConfigurationError
from aiorobokassa.utils.xml import XMLMixin

logger = logging.getLogger(__name__)


class RoboKassaClient(BaseAPIClient, PaymentMixin, InvoiceMixin, RefundMixin, XMLMixin):
    """
    Async client for RoboKassa payment gateway.

    Supports payment link generation, notification handling, invoice creation,
    and refunds.
    """

    PRODUCTION_BASE_URL: str = PROD_URL
    TEST_BASE_URL: str = TEST_URL

    def __init__(
        self,
        merchant_login: str,
        password1: str,
        password2: str,
        password3: Optional[str] = None,
        test_mode: bool = False,
        session: Optional[aiohttp.ClientSession] = None,
        timeout: Optional[aiohttp.ClientTimeout] = None,
        base_url_override: Optional[str] = None,
    ):
        """
        Initialize RoboKassa client.

        Args:
            merchant_login: Merchant login from RoboKassa
            password1: Password #1 for signature calculation
            password2: Password #2 for ResultURL verification
            password3: Password #3 for refund API (optional, required for refunds)
            test_mode: Enable test mode
            session: Optional aiohttp session (will be created if not provided)
            timeout: Optional timeout for requests
            base_url_override: Override base URL (for testing)

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self._validate_merchant_config(merchant_login, password1, password2, password3)

        base_url = base_url_override or (
            self.TEST_BASE_URL if test_mode else self.PRODUCTION_BASE_URL
        )
        super().__init__(base_url=base_url, test_mode=test_mode, session=session, timeout=timeout)

        self.merchant_login = merchant_login
        self.password1 = password1
        self.password2 = password2
        self.password3 = password3

    @staticmethod
    def _validate_merchant_config(
        merchant_login: str, password1: str, password2: str, password3: Optional[str] = None
    ) -> None:
        """Validate merchant configuration."""
        if not merchant_login or not merchant_login.strip():
            raise ConfigurationError("merchant_login cannot be empty")
        if not password1:
            raise ConfigurationError("password1 is required")
        if len(password1) < MIN_PASSWORD_LENGTH:
            raise ConfigurationError(
                f"password1 is too short (minimum {MIN_PASSWORD_LENGTH} characters)"
            )
        if not password2:
            raise ConfigurationError("password2 is required")
        if len(password2) < MIN_PASSWORD_LENGTH:
            raise ConfigurationError(
                f"password2 is too short (minimum {MIN_PASSWORD_LENGTH} characters)"
            )
        if password3 is not None and len(password3) < MIN_PASSWORD_LENGTH:
            raise ConfigurationError(
                f"password3 is too short (minimum {MIN_PASSWORD_LENGTH} characters)"
            )

    def clear_sensitive_data(self) -> None:
        """Clear sensitive data from memory."""
        self.password1 = ""
        self.password2 = ""
        if self.password3:
            self.password3 = ""
        gc.collect()
        logger.debug("Cleared sensitive data from memory")
