"""D0.2 - Una sola funcion, varios backends.

Objetivo del dia: un solo comando responde desde 4 proveedores y dice cuanto
costo cada uno.

    uv run hello_llm.py --prompt "Explica que es una ARS en una frase"

Lo que YA esta hecho (andamiaje): el contrato de datos, la carga del .env, el
registro de proveedores y la impresion de la tabla.

Lo que escribes TU: la funcion `coste()` y el cuerpo de cada `llamar_*()`.
Cada una recibe un prompt y devuelve una `Respuesta`. Nada mas.
"""

from __future__ import annotations
from openai import OpenAI
import argparse
import os
import time
from dataclasses import dataclass
from google import genai
from dotenv import load_dotenv
from anthropic import Anthropic

from precios import PRECIOS

load_dotenv()


@dataclass
class Respuesta:
    """El contrato. Todos los proveedores devuelven exactamente esto."""

    proveedor: str
    modelo: str
    texto: str
    tokens_entrada: int
    tokens_salida: int
    latencia_s: float
    coste_usd: float


# --------------------------------------------------------------------------
# TU CODIGO EMPIEZA AQUI
# --------------------------------------------------------------------------


def coste(modelo: str, tokens_entrada: int, tokens_salida: int) -> float:
    try:
        precio_entrada, precio_salida = PRECIOS[modelo]
    except KeyError:
        raise ValueError(
            f"No se encontró información de precios para el modelo '{modelo}'."
        )

    return (
        (tokens_entrada / 1_000_000) * precio_entrada
        + (tokens_salida / 1_000_000) * precio_salida
    )

def llamar_anthropic(prompt: str) -> Respuesta:
    modelo = os.getenv("ANTHROPIC_MODELO")

    cliente = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    r = cliente.messages.create(
        model=modelo,
        max_tokens=200,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    entrada = r.usage.input_tokens
    salida = r.usage.output_tokens

    return Respuesta(
        proveedor="anthropic",
        modelo=modelo,
        texto=r.content[0].text,
        tokens_entrada=entrada,
        tokens_salida=salida,
        latencia_s=0.0,
        coste_usd=coste(modelo, entrada, salida),
    )



def llamar_openai(prompt: str) -> Respuesta:
    modelo = os.getenv("OPENAI_MODELO")

    cliente = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    r = cliente.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=200,
    )

    entrada = r.usage.prompt_tokens
    salida = r.usage.completion_tokens

    return Respuesta(
        proveedor="openai",
        modelo=modelo,
        texto=r.choices[0].message.content,
        tokens_entrada=entrada,
        tokens_salida=salida,
        latencia_s=0.0,
        coste_usd=coste(modelo, entrada, salida),
    )

def llamar_groq(prompt: str) -> Respuesta:
    modelo = os.getenv("GROQ_MODELO")
    cliente = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )
    r = cliente.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    entrada = r.usage.prompt_tokens
    salida = r.usage.completion_tokens
    return Respuesta(
        proveedor="groq",
        modelo=modelo,
        texto=r.choices[0].message.content,
        tokens_entrada=entrada,
        tokens_salida=salida,
        latencia_s=0.0,
        coste_usd=coste(modelo, entrada, salida),
    )


def llamar_gemini(prompt: str) -> Respuesta:
    modelo = os.getenv("GEMINI_MODELO")

    cliente = genai.Client(
        api_key=os.getenv("GOOGLE_API_KEY")
    )

    r = cliente.models.generate_content(
        model=modelo,
        contents=prompt,
    )

    entrada = r.usage_metadata.prompt_token_count
    salida = r.usage_metadata.candidates_token_count

    return Respuesta(
        proveedor="gemini",
        modelo=modelo,
        texto=r.text,
        tokens_entrada=entrada,
        tokens_salida=salida,
        latencia_s=0.0,
        coste_usd=coste(modelo, entrada, salida),
    )


def llamar_ollama(prompt: str) -> Respuesta:
    """Modelo local. Mismo truco que Groq: http://localhost:11434/v1

    Coste 0. Sirve para experimentar sin mirar la factura.
    """
    raise NotImplementedError("D0.2 - escribe esto")


# --------------------------------------------------------------------------
# TU CODIGO TERMINA AQUI. Lo de abajo ya funciona.
# --------------------------------------------------------------------------

PROVEEDORES = {
    "anthropic": llamar_anthropic,
    "openai": llamar_openai,
    "groq": llamar_groq,
    "gemini": llamar_gemini,
    "ollama": llamar_ollama,
}


def cronometrar(fn, prompt: str) -> Respuesta:
    """Envuelve la llamada para medir latencia real de punta a punta."""
    inicio = time.perf_counter()
    r = fn(prompt)
    r.latencia_s = time.perf_counter() - inicio
    return r


def main() -> None:
    p = argparse.ArgumentParser(description="Hola mundo multiproveedor")
    p.add_argument("--prompt", default="Responde en una sola frase: que es una ARS?")
    p.add_argument(
        "--proveedores",
        default="anthropic,openai,groq,gemini",
        help="lista separada por comas: " + ", ".join(PROVEEDORES),
    )
    args = p.parse_args()

    resultados: list[Respuesta] = []
    for nombre in [x.strip() for x in args.proveedores.split(",") if x.strip()]:
        fn = PROVEEDORES.get(nombre)
        if fn is None:
            print(f"  ! proveedor desconocido: {nombre}")
            continue
        try:
            resultados.append(cronometrar(fn, args.prompt))
        except NotImplementedError as e:
            print(f"  · {nombre}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  ! {nombre} fallo: {type(e).__name__}: {e}")

    if not resultados:
        return

    print()
    for r in resultados:
        print(f"── {r.proveedor} · {r.modelo}")
        print(f"   {r.texto.strip()}")
        print()

    ancho = max(len(r.proveedor) for r in resultados)
    print(f"{'proveedor':<{ancho}}  {'ent':>6} {'sal':>6} {'seg':>7} {'USD':>10}")
    print("─" * (ancho + 33))
    for r in resultados:
        print(
            f"{r.proveedor:<{ancho}}  {r.tokens_entrada:>6} {r.tokens_salida:>6} "
            f"{r.latencia_s:>7.2f} {r.coste_usd:>10.6f}"
        )
    print("─" * (ancho + 33))
    print(f"{'total':<{ancho}}  {'':>6} {'':>6} {'':>7} {sum(r.coste_usd for r in resultados):>10.6f}")


if __name__ == "__main__":
    main()
