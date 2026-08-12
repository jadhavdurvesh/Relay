from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class FailureDecision:
    """Describes how RELAY should respond to a provider failure."""

    retryable: bool
    reason: str


class FailoverManager:
    """
    Determines whether a provider failure should trigger failover.

    The manager intentionally keeps routing policy separate from the
    actual provider implementations.
    """

    RETRYABLE_STATUS_CODES = frozenset(
        {
            408,  # Request Timeout
            425,  # Too Early
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        }
    )

    NON_RETRYABLE_STATUS_CODES = frozenset(
        {
            400,  # Bad Request
            401,  # Unauthorized
            403,  # Forbidden
            404,  # Not Found
            405,  # Method Not Allowed
            409,  # Conflict
            422,  # Unprocessable Entity
        }
    )

    def classify(self, error: Exception) -> FailureDecision:
        """
        Classify a provider exception.

        Returns:
            FailureDecision indicating whether another provider
            should be attempted.
        """

        if isinstance(error, httpx.TimeoutException):
            return FailureDecision(
                retryable=True,
                reason="provider_timeout",
            )

        if isinstance(error, httpx.NetworkError):
            return FailureDecision(
                retryable=True,
                reason="provider_network_error",
            )

        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code

            if status_code in self.RETRYABLE_STATUS_CODES:
                return FailureDecision(
                    retryable=True,
                    reason=f"retryable_http_{status_code}",
                )

            if status_code in self.NON_RETRYABLE_STATUS_CODES:
                return FailureDecision(
                    retryable=False,
                    reason=f"non_retryable_http_{status_code}",
                )

            # Unknown 4xx errors should normally not be retried.
            if 400 <= status_code < 500:
                return FailureDecision(
                    retryable=False,
                    reason=f"client_error_{status_code}",
                )

            # Unknown 5xx errors are treated as temporary failures.
            if 500 <= status_code < 600:
                return FailureDecision(
                    retryable=True,
                    reason=f"server_error_{status_code}",
                )

        # Connection-related exceptions from other libraries or
        # provider adapters are treated conservatively as retryable.
        if isinstance(error, ConnectionError):
            return FailureDecision(
                retryable=True,
                reason="connection_error",
            )

        return FailureDecision(
            retryable=False,
            reason="unknown_error",
        )

    def should_failover(self, error: Exception) -> bool:
        """Return True when the request should be attempted elsewhere."""
        return self.classify(error).retryable