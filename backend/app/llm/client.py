from langchain_core.language_models.chat_models import BaseChatModel

from app.config import Settings, get_settings


def create_llm(settings: Settings | None = None) -> BaseChatModel:
    """Build a chat model for the configured provider.

    Providers:
      - groq               -> Groq free tier (LLaMA / Mixtral class)
      - google             -> Gemini free tier
      - openai             -> OpenAI
      - openai_compatible  -> any OpenAI-compatible endpoint (Ollama, OpenRouter...)
    """
    s = settings or get_settings()
    provider = s.llm_provider.lower().strip()
    common = {"model": s.llm_model, "temperature": s.llm_temperature}

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(groq_api_key=s.groq_api_key, **common)

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(google_api_key=s.google_api_key, **common)

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(openai_api_key=s.openai_api_key, **common)

    if provider == "openai_compatible":
        from langchain_openai import ChatOpenAI

        if not s.llm_base_url:
            raise ValueError("LLM_BASE_URL is required for openai_compatible provider")
        return ChatOpenAI(
            openai_api_key=s.openai_api_key or "not-needed",
            openai_api_base=s.llm_base_url,
            **common,
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER {s.llm_provider!r}. "
        "Use one of: groq, google, openai, openai_compatible."
    )