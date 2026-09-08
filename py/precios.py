"""Tabla de precios por millon de tokens, en USD.

Verificado el 5 de septiembre de 2026 contra las paginas oficiales de cada
proveedor. ESTO CADUCA. Antes de empezar cada fase del plan, vuelve a mirarlo:

  Anthropic  https://platform.claude.com/docs/en/about-claude/pricing
  OpenAI     https://developers.openai.com/api/docs/pricing
  Google     https://ai.google.dev/gemini-api/docs/pricing
  Groq       https://console.groq.com/docs/models

Regla 05: si no sabes lo que cuesta, no lo has medido.
"""

# modelo -> (usd por 1M tokens de entrada, usd por 1M tokens de salida)
PRECIOS: dict[str, tuple[float, float]] = {
    # Anthropic
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-opus-5": (5.00, 25.00),
    # OpenAI
    "gpt-5-nano": (0.05, 0.40),
    "gpt-5-mini": (0.25, 2.00),
    # Google (hay capa gratuita con limite de peticiones; el precio es el de pago)
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.8-flash": (0.75, 3.75),
    # Groq
    "openai/gpt-oss-20b": (0.075, 0.30),
    "openai/gpt-oss-120b": (0.15, 0.60),
    # Local: no cuesta dinero, cuesta bateria
    "ollama": (0.0, 0.0),
}
