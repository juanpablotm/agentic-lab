"""core/llm.py - el cliente que se reutiliza el resto del plan.

Un solo punto de entrada para hablar con cualquier proveedor, con timeout,
reintentos y trazas. A partir de aqui, nada en este repositorio llama a un SDK
directamente: todo pasa por `llamar()`.

    from core.llm import llamar
    r = llamar("Que es una ARS?", proveedor="anthropic")
    if r.ok:
        print(r.texto)

Decisiones de contrato (tomadas por Juan Pablo en D02):

  1. Al agotarse los reintentos NO se lanza excepcion: se devuelve una Respuesta
     con ok=False. Ver la nota de riesgo en la propia clase.
  2. Se registra TODO en el JSONL, incluidos los intentos que fallaron.
  3. Una respuesta truncada (stop_reason max_tokens / length) es un FALLO.
  4. Las trazas viven en py/trazas/ y NO se versionan. Razon en el README.
"""

from __future__ import annotations

import json
import os
import random
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import truststore

truststore.inject_into_ssl()  # antes de que ningun SDK cree su contexto TLS

from dotenv import load_dotenv  # noqa: E402

from precios import PRECIOS  # noqa: E402

load_dotenv()

RAIZ = Path(__file__).resolve().parents[1]
TRAZAS = RAIZ / "trazas" / "llamadas.jsonl"

MAX_INTENTOS = 4
BASE_ESPERA = 1.0
JITTER_MAX = 1.0
TIMEOUT = 30.0

# Motivos de parada que significan "esto llego cortado".
TRUNCADO = {"max_tokens", "length", "model_context_window_exceeded"}


# ---------------------------------------------------------------------------
# EL CONTRATO
# ---------------------------------------------------------------------------


@dataclass
class Respuesta:
    """Lo que devuelve `llamar()`, venga del proveedor que venga.

    Respecto a la version de D0.2 se le anadieron tres campos: stop_reason (sin
    el no se puede saber si la respuesta esta completa), ok y error.

    RIESGO DE LA DECISION 1: como un fallo se devuelve en vez de lanzarse, se
    puede ignorar por accidente. `r.texto` de una respuesta fallida es "" y no
    avisa de nada. Por eso `ok` es el primer campo que hay que mirar SIEMPRE:

        r = llamar(...)
        if not r.ok:
            ...   # decide que haces
    """

    proveedor: str
    modelo: str
    texto: str = ""
    tokens_entrada: int = 0
    tokens_salida: int = 0
    latencia_s: float = 0.0
    coste_usd: float = 0.0
    stop_reason: str = ""
    ok: bool = True
    error: str = ""
    intentos: int = 1


def coste(modelo: str, tokens_entrada: int, tokens_salida: int) -> float:
    """Coste en USD a partir de la tabla de PRECIOS.

    Un modelo desconocido lanza ValueError en vez de devolver 0.0: perder una
    fila es recuperable, creerse una fila falsa no. (Decision de D0.2.)
    """
    try:
        precio_entrada, precio_salida = PRECIOS[modelo]
    except KeyError:
        raise ValueError(f"No hay precio para el modelo '{modelo}'.") from None
    return (tokens_entrada / 1_000_000) * precio_entrada + (
        tokens_salida / 1_000_000
    ) * precio_salida


# ---------------------------------------------------------------------------
# QUE ES TRANSITORIO
# ---------------------------------------------------------------------------
# En el ejercicio 2 esto era una tupla de clases del SDK de OpenAI. Aqui no
# sirve: cada proveedor tiene SUS propias clases de excepcion. Asi que en vez de
# preguntar "de que clase eres" se pregunta "que te paso", que es lo que de
# verdad importa y funciona igual para los cinco.

CODIGOS_TRANSITORIOS = {408, 409, 425, 429, 500, 502, 503, 504, 529}
NOMBRES_TRANSITORIOS = {
    "APITimeoutError",
    "APIConnectionError",
    "ConnectTimeout",
    "ReadTimeout",
    "ConnectError",
    "RemoteProtocolError",
    "InternalServerError",
    "RateLimitError",
    "ServiceUnavailable",
    "ServerError",
}


def es_transitorio(exc: BaseException) -> bool:
    """True si vale la pena reintentar: el fallo es del servicio o de la red."""
    codigo = getattr(exc, "status_code", None)
    if isinstance(codigo, int):
        return codigo in CODIGOS_TRANSITORIOS
    return type(exc).__name__ in NOMBRES_TRANSITORIOS


# ---------------------------------------------------------------------------
# ADAPTADORES POR PROVEEDOR
# ---------------------------------------------------------------------------
# Cada uno devuelve la misma tupla: (texto, tokens_entrada, tokens_salida,
# stop_reason). Traducir las catorce formas distintas de decir lo mismo es TODO
# el trabajo de esta capa.
#
# Los imports de los SDK van dentro de cada funcion: asi importar este modulo no
# carga cinco librerias de las que a lo mejor solo usas una.


def _compatible_openai(prompt, modelo, max_tokens, base_url, api_key, extra):
    """Sirve para OpenAI, Groq y Ollama: los tres hablan el mismo protocolo.

    Es la leccion de D0.2 convertida en codigo: el proveedor no es una
    integracion distinta, es una base_url distinta.
    """
    from openai import OpenAI

    cliente = OpenAI(api_key=api_key, base_url=base_url)
    r = cliente.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=max_tokens,
        timeout=TIMEOUT,
        **extra,
    )
    eleccion = r.choices[0]
    return (
        eleccion.message.content or "",
        r.usage.prompt_tokens,
        r.usage.completion_tokens,
        eleccion.finish_reason or "",
    )


def _openai(prompt, modelo, max_tokens, extra):
    return _compatible_openai(
        prompt, modelo, max_tokens, None, os.getenv("OPENAI_API_KEY"), extra
    )


def _groq(prompt, modelo, max_tokens, extra):
    return _compatible_openai(
        prompt,
        modelo,
        max_tokens,
        "https://api.groq.com/openai/v1",
        os.getenv("GROQ_API_KEY"),
        extra,
    )


def _ollama(prompt, modelo, max_tokens, extra):
    return _compatible_openai(
        prompt,
        modelo,
        max_tokens,
        os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        "ollama",
        extra,
    )


def _anthropic(prompt, modelo, max_tokens, extra):
    from anthropic import Anthropic

    cliente = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), timeout=TIMEOUT)
    r = cliente.messages.create(
        model=modelo,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        **extra,
    )
    # content es una LISTA de bloques: hay que juntar los de tipo texto.
    texto = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    return texto, r.usage.input_tokens, r.usage.output_tokens, r.stop_reason or ""


def _gemini(prompt, modelo, max_tokens, extra):
    from google import genai
    from google.genai import types

    cliente = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    r = cliente.models.generate_content(
        model=modelo,
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=max_tokens, **extra),
    )
    u = r.usage_metadata
    razon = ""
    if r.candidates:
        razon = str(getattr(r.candidates[0], "finish_reason", "") or "")
    return (
        r.text or "",
        u.prompt_token_count or 0,
        u.candidates_token_count or 0,
        razon,
    )


ADAPTADORES = {
    "anthropic": (_anthropic, "ANTHROPIC_MODELO"),
    "openai": (_openai, "OPENAI_MODELO"),
    "groq": (_groq, "GROQ_MODELO"),
    "gemini": (_gemini, "GEMINI_MODELO"),
    "ollama": (_ollama, "OLLAMA_MODELO"),
}


# ---------------------------------------------------------------------------
# TRAZAS
# ---------------------------------------------------------------------------


def registrar(linea: dict, destino: Path = TRAZAS) -> None:
    """Anade una linea al JSONL. Decision 2: se registra todo, fallos incluidos.

    Modo "a": JSON Lines se escribe al final sin releer ni reescribir el archivo.
    Por eso es el formato de las trazas y no un JSON normal, que habria que
    cargar entero en memoria para anadirle un elemento.

    Nunca lanza: una traza que falla no puede tumbar la llamada que iba bien.
    """
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("a", encoding="utf-8") as f:
            f.write(json.dumps(linea, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# LA FUNCION
# ---------------------------------------------------------------------------


def llamar(
    prompt: str,
    proveedor: str = "anthropic",
    modelo: str | None = None,
    max_tokens: int = 400,
    **extra,
) -> Respuesta:
    """Llama a un proveedor con timeout, reintentos y traza. Devuelve Respuesta.

    `extra` pasa tal cual al SDK: reasoning_effort, thinking, temperature...
    Lo que cada proveedor admita es cosa suya; aqui no se filtra.
    """
    if proveedor not in ADAPTADORES:
        raise ValueError(f"Proveedor desconocido: {proveedor}. Hay: {list(ADAPTADORES)}")

    fn, var_modelo = ADAPTADORES[proveedor]
    modelo = modelo or os.getenv(var_modelo)
    if not modelo:
        # Falla aqui, con un mensaje claro, en vez de mandar "model": null y
        # recibir un error confuso del proveedor. (Leccion de D01.)
        raise ValueError(f"Falta {var_modelo} en el .env y no se paso modelo.")

    # Ollama es local: la categoria de precio no depende del modelo que corras.
    modelo_precio = "ollama" if proveedor == "ollama" else modelo
    ultimo_error = ""

    for intento in range(1, MAX_INTENTOS + 1):
        inicio = time.perf_counter()
        try:
            texto, entrada, salida, razon = fn(prompt, modelo, max_tokens, extra)

        except Exception as e:
            latencia = time.perf_counter() - inicio
            transitorio = es_transitorio(e)
            ultimo_error = f"{type(e).__name__}: {e}"
            registrar(
                {
                    "ts": _ahora(),
                    "evento": "intento_fallido",
                    "proveedor": proveedor,
                    "modelo": modelo,
                    "intento": intento,
                    "transitorio": transitorio,
                    "latencia_s": round(latencia, 3),
                    "error": ultimo_error,
                }
            )

            # Un fallo que NO es transitorio es culpa tuya: un 400 por un cuerpo
            # mal formado, un 401 por la clave. Reintentarlo solo repite el error
            # mas despacio, y silenciarlo haria que un bug de configuracion
            # pareciera un problema del servicio. Sube tal cual.
            if not transitorio:
                raise

            if intento == MAX_INTENTOS:
                break  # agotados: se sale a devolver la Respuesta fallida

            espera = BASE_ESPERA * (2 ** (intento - 1)) + random.uniform(0, JITTER_MAX)
            time.sleep(espera)
            continue

        # ---- el transporte fue bien. Ahora la otra capa: y el contenido? ----
        latencia = time.perf_counter() - inicio
        truncada = razon in TRUNCADO
        r = Respuesta(
            proveedor=proveedor,
            modelo=modelo,
            texto=texto,
            tokens_entrada=entrada,
            tokens_salida=salida,
            latencia_s=round(latencia, 3),
            coste_usd=coste(modelo_precio, entrada, salida),
            stop_reason=razon,
            # Decision 3: una respuesta cortada es un fallo. Y OJO: no se
            # reintenta. Repetir la misma llamada daria el mismo corte. Esto no
            # es un fallo de transporte, es un fallo de contenido, y se arregla
            # subiendo max_tokens o partiendo la tarea, no insistiendo.
            ok=not truncada,
            error="respuesta truncada" if truncada else "",
            intentos=intento,
        )
        registrar({"ts": _ahora(), "evento": "llamada", **asdict(r)})
        return r

    # Decision 1: agotados los reintentos se devuelve una Respuesta fallida.
    r = Respuesta(
        proveedor=proveedor,
        modelo=modelo,
        ok=False,
        error=ultimo_error,
        intentos=MAX_INTENTOS,
    )
    registrar({"ts": _ahora(), "evento": "llamada", **asdict(r)})
    return r
