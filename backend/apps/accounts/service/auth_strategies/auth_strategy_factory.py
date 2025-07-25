
from typing import Type, Optional
from django.conf import settings
from apps.accounts.service.auth_strategies.cookie_token_strategy import CookieTokenAuthStrategy
from apps.accounts.service.auth_strategies.auth_strategy_interface import AuthStrategy
import logging

logger = logging.getLogger(__name__)

class AuthStrategyFactory:
    """Factory for creating authentication strategy instances.

    This factory resolves the appropriate authentication strategy based on configuration,
    enabling dependency injection for AuthService.
    """

    _strategies: dict[str, Type[AuthStrategy]] = {
        'cookie_token': CookieTokenAuthStrategy
    }

    @classmethod
    def register_strategy(cls, name: str, strategy_class: Type[AuthStrategy]) -> None:
        """Register a new authentication strategy.

        Args:
            name: The name of the strategy (e.g., 'cookie_token').
            strategy_class: The strategy class implementing AuthStrategy.

        Example:
            AuthStrategyFactory.register_strategy('jwt', JWTAuthStrategy)
        """
        cls._strategies[name] = strategy_class
        logger.debug("Registered authentication strategy: %s", name)

    @classmethod
    def get_strategy(cls) -> AuthStrategy:
        """Retrieve the authentication strategy based on configuration.

        Uses the AUTH_STRATEGY setting or defaults to 'cookie_token'.

        Returns:
            An instance of the configured authentication strategy.

        Raises:
            ValueError: If the configured strategy is not registered.
        """
        strategy_name = getattr(settings, 'AUTH_STRATEGY', 'cookie_token')
        strategy_class = cls._strategies.get(strategy_name)
        if not strategy_class:
            logger.error("Unknown authentication strategy: %s", strategy_name)
            raise ValueError(f"Unknown authentication strategy: {strategy_name}")
        logger.debug("Resolved authentication strategy: %s", strategy_name)
        return strategy_class()