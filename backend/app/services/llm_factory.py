def _import_openai():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI


def _import_groq():
    from langchain_groq import ChatGroq
    return ChatGroq


def _import_anthropic():
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic


def _import_google():
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI


def _import_mistral():
    from langchain_mistralai import ChatMistralAI
    return ChatMistralAI


def _import_cohere():
    from langchain_cohere import ChatCohere
    return ChatCohere


class LLMProviderFactory:
    """
    Factory for creating chat LLM clients across different AI providers.

    To support a new provider, register its LangChain chat model class
    with `register()` - no other code needs to change.
    """

    _PROVIDER_IMPORTERS = {
        "openai": _import_openai,
        "groq": _import_groq,
        "anthropic": _import_anthropic,
        "google": _import_google,
        "mistral": _import_mistral,
        "cohere": _import_cohere,
    }

    @classmethod
    def create(cls, provider: str, model: str, temperature: float = 0, **kwargs):
        print("[LLMProviderFactory.create] called")
        provider_key = provider.strip().lower()
        importer = cls._PROVIDER_IMPORTERS.get(provider_key)
        if importer is None:
            raise ValueError(
                f"Unsupported LLM provider '{provider}'. "
                f"Supported providers: {sorted(cls._PROVIDER_IMPORTERS)}"
            )
        try:
            provider_class = importer()
        except ImportError as e:
            raise ImportError(
                f"Provider '{provider}' requires its LangChain integration package "
                f"(pip install langchain-{provider_key}) to be installed."
            ) from e
        client = provider_class(model=model, temperature=temperature, **kwargs)
        print(f"[LLMProviderFactory.create] output: created {provider_class.__name__} client for provider={provider_key!r}")
        return client

    @classmethod
    def register(cls, name: str, importer) -> None:
        """Register a new provider. `importer` is a zero-arg callable returning its chat model class."""
        print(f"[LLMProviderFactory.register] called with name={name!r}")
        cls._PROVIDER_IMPORTERS[name.strip().lower()] = importer
