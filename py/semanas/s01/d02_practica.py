"""D02 - Ejercicio 1: medir la variabilidad.

El ejercicio original pedia comparar temperature 0 contra temperature 1. Al
correrlo, el modelo rechazo el parametro: los modelos de razonamiento ya no lo
admiten. Eso no rompe el experimento, lo mejora. Ver NOTA DEL GIRO abajo.

Los cinco arreglos de la primera version siguen marcados con # FIX-n.

    cd ~/Desktop/Agentic-Lab/py
    uv run semanas/s01/d02_practica.py
"""

from __future__ import annotations

# FIX-4 (parte 1): truststore se inyecta ANTES de importar cualquier libreria que
# abra conexiones TLS. No es estilo, es orden de ejecucion.
import truststore
truststore.inject_into_ssl()

import os
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import BadRequestError, OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# FIX-2: Respuesta y coste viven en hello_llm.py. En el ejercicio 3, cuando
# existan en core/llm.py, esta linea pasa a ser:
#     from core.llm import coste
from hello_llm import coste  # noqa: E402

load_dotenv()

PROMPT = (
    "Clasifica en una palabra la urgencia de este caso: "
    "dolor abdominal persistente de tres dias, acudio a emergencias."
)
N = 10

# ---------------------------------------------------------------------------
# NOTA DEL GIRO
#
# temperature, top_p y top_k eran las perillas del MUESTREO: controlaban como se
# sorteaba el siguiente token. Los modelos de razonamiento las han ido quitando y
# en su lugar ofrecen reasoning_effort, que no controla el sorteo sino cuanto
# piensa el modelo antes de responder. Es otro nivel de abstraccion.
#
# Consecuencia incomoda y util: ya no existe un "temperature: 0" al que acudir
# para forzar reproducibilidad. La variabilidad deja de ser una perilla que puedes
# bajar y pasa a ser una propiedad del sistema con la que hay que convivir.
#
# Por eso la pregunta del experimento cambia, y a mejor:
#   antes -> cuanta variabilidad hay a temperature 0 contra temperature 1
#   ahora -> cuanta variabilidad hay, punto, y que efecto tiene el esfuerzo
#
# Si eso se confirma, toda la estrategia de calidad de la semana 8 deja de ser
# una recomendacion y pasa a ser la unica opcion disponible.
# ---------------------------------------------------------------------------

ESFUERZOS = ["minimal", "high"]


@dataclass
class Medicion:
    """Lo que necesito para ESTA medicion.

    Respuesta (la de D0.2) no trae stop_reason, y despues de D01 sabemos que sin
    ese campo no se puede saber si una respuesta esta completa. Es un hueco real
    del contrato: arreglalo en core/llm.py.
    """

    texto: str
    tokens_salida: int
    coste_usd: float
    finish_reason: str


def llamar(prompt: str, esfuerzo: str) -> Medicion:
    modelo = os.getenv("OPENAI_MODELO")
    cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    r = cliente.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=400,
        reasoning_effort=esfuerzo,
        timeout=30.0,  # FIX-4 (parte 2): explicito. El del SDK son minutos.
    )

    entrada = r.usage.prompt_tokens
    salida = r.usage.completion_tokens
    return Medicion(
        texto=(r.choices[0].message.content or "").strip(),
        tokens_salida=salida,
        coste_usd=coste(modelo, entrada, salida),
        # FIX-5: sin esto, veinte respuestas vacias parecen determinismo perfecto.
        finish_reason=r.choices[0].finish_reason,
    )


def tanda(esfuerzo: str, n: int = N) -> list[Medicion]:
    # FIX-1: la variable del bucle se usa en la MISMA iteracion y la lista se
    # construye y se devuelve aqui dentro. En la primera version se asignaba a
    # `esponse` y se leia `response`, que seguia viva del bucle anterior: Python
    # no se queja porque el nombre existe, y el resultado sale falso y creible.
    # Esta estructura hace que ese error no pueda ocurrir.
    salidas = []
    for i in range(n):
        m = llamar(PROMPT, esfuerzo)
        salidas.append(m)
        print(f"  {esfuerzo:>7}  [{i + 1}/{n}]  {m.finish_reason:>6}  {m.texto[:60]!r}")
        time.sleep(0.3)
    return salidas


def resumen(nombre: str, ms: list[Medicion]) -> dict:
    # FIX-3: medir, no mirar. Contar a ojo veinte respuestas no es reproducible.
    textos = [m.texto for m in ms]
    return {
        "tanda": nombre,
        "distintas": len(set(textos)),   # <- el numero del dia
        "vacias": sum(1 for t in textos if not t),
        "cortadas": sum(1 for m in ms if m.finish_reason == "length"),
        "tok_salida_media": round(statistics.mean(m.tokens_salida for m in ms), 1),
        "coste_total": round(sum(m.coste_usd for m in ms), 6),
    }


def imprimir(filas: list[dict]) -> None:
    cols = list(filas[0].keys())
    anchos = {c: max(len(c), *(len(str(f[c])) for f in filas)) for c in cols}
    print()
    print("  ".join(c.ljust(anchos[c]) for c in cols))
    print("-" * (sum(anchos.values()) + 2 * (len(cols) - 1)))
    for f in filas:
        print("  ".join(str(f[c]).ljust(anchos[c]) for c in cols))


def main() -> None:
    print(f"Prompt: {PROMPT}\n")
    tandas = {}
    try:
        for esfuerzo in ESFUERZOS:
            print(f"Tanda - reasoning_effort={esfuerzo}")
            tandas[esfuerzo] = tanda(esfuerzo)
            print()
    except BadRequestError as e:
        print(f"\n!! El modelo rechazo un parametro:\n   {e}")
        return

    imprimir([resumen(e, tandas[e]) for e in ESFUERZOS])

    for esfuerzo in ESFUERZOS:
        print(f"\nRespuestas distintas con esfuerzo {esfuerzo}:")
        for t in sorted(set(m.texto for m in tandas[esfuerzo])):
            print(f"  - {t!r}")

    print(
        "\nLa pregunta que tienes que contestar en el diario:\n"
        "  si en alguna de las dos tandas el numero de distintas es mayor que 1,\n"
        "  no existe ningun parametro que puedas tocar para bajarlo a 1.\n"
        "  Entonces, como pruebas que tu sistema funciona?"
    )


if __name__ == "__main__":
    main()
