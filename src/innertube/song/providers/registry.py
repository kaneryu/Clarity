from . import ProviderInterface
from .youtube import YoutubeProvider

PROVIDERS: dict[str, type[ProviderInterface]] = {
    YoutubeProvider.NAME: YoutubeProvider,
}


def get_provider(name: str):
    return PROVIDERS.get(name)


def list_providers():
    return list(PROVIDERS.keys())


def add_provider(name: str, provider_class: type[ProviderInterface]):
    if name in PROVIDERS:
        raise ValueError(f"Provider '{name}' is already registered.")
    if not isinstance(
        provider_class, ProviderInterface
    ):  # ProviderInterface is runtime_checkable
        raise TypeError("Provider class must inherit from ProviderInterface.")
    PROVIDERS[name] = provider_class
