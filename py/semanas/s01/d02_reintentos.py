"""D02 - Ejercicio 2: reintentos con backoff y jitter, sin tocar la red.

Objetivo: escribir la logica de reintentos de `core/llm.py` y probarla contra
funciones falsas, en vez de contra la API real.

    cd ~/Desktop/Agentic-Lab/py
    uv run semanas/s01/d02_reintentos.py

Por que con funciones falsas:
  - es instantaneo (no hay red de por medio)
  - es gratis (ni un token)
  - es determinista (provocas EXACTAMENTE el fallo que quieres ver)
  - puedes probar casos que en la vida real casi no ocurren

Provocar un 429 de verdad seria lento, caro e impredecible. Esta misma tecnica,
cambiando el error falso por un LLM falso, es el proyecto 2 de la semana 2.
"""

from __future__ import annotations

import random
import time
from typing import Callable

import httpx
from openai import (
    APIConnectionError,
    APITimeoutError,
    BadRequestError,
    InternalServerError,
    RateLimitError,
)

# ---------------------------------------------------------------------------
# 1. QUE SE REINTENTA Y QUE NO
# ---------------------------------------------------------------------------
# El SDK expone tipos de excepcion que mapean uno a uno contra la tabla de la
# seccion 05 del manual. Esto NO es un `except Exception`: es una lista cerrada
# de fallos transitorios. Un 400 reintentado cuatro veces son cuatro veces el
# mismo error, cuatro veces mas lento.

TRANSITORIOS = (
    RateLimitError,       # 429 - demasiadas peticiones
    InternalServerError,  # 5xx - problema del proveedor
    APITimeoutError,      # se acabo el tiempo
    APIConnectionError,   # no se pudo conectar
)


# ---------------------------------------------------------------------------
# 2. LA LOGICA DE REINTENTOS
# ---------------------------------------------------------------------------


def con_reintentos(
    fn: Callable[[], object],
    max_intentos: int = 4,
    base: float = 1.0,
    jitter_max: float = 1.0,
    dormir: Callable[[float], None] = time.sleep,
    log: Callable[[str], None] = print,
) -> object:
    """Ejecuta `fn` reintentando solo los fallos transitorios.

    `dormir` se recibe como parametro en vez de llamar a time.sleep directamente.
    Eso se llama inyeccion de dependencias y aqui compra dos cosas concretas:
    los tests corren en cero segundos, y puedes COMPROBAR cuanto habria esperado
    en vez de solo creertelo. Sin esto, probar un backoff de 1+2+4 segundos
    tardaria siete segundos cada vez.
    """
    for intento in range(max_intentos):
        try:
            return fn()
        except TRANSITORIOS as e:
            ultimo = e
            # El ultimo intento NO duerme: no tiene sentido esperar ocho
            # segundos para despues rendirse igual. Una linea que casi todo el
            # mundo deja mal.
            if intento == max_intentos - 1:
                log(f"  intento {intento + 1}/{max_intentos}: {type(e).__name__} - sin mas intentos")
                break
            espera = base * (2 ** intento) + random.uniform(0, jitter_max)
            log(f"  intento {intento + 1}/{max_intentos}: {type(e).__name__} - espero {espera:.2f}s")
            dormir(espera)
        # Nota: cualquier otra excepcion NO se atrapa y sube tal cual. Es
        # deliberado: un error de tu codigo tiene que explotar, no reintentarse.

    # Decision de diseno: al agotarse, relanzo la ultima excepcion en vez de
    # devolver un valor. Razon: quien llama (el bucle del agente en D09) tiene
    # que poder distinguir "fallo la llamada" de "el modelo respondio algo raro",
    # y una excepcion es imposible de ignorar por accidente. Un valor de retorno
    # se ignora solo.
    raise ultimo


# ---------------------------------------------------------------------------
# 3. LAS FUNCIONES FALSAS
# ---------------------------------------------------------------------------

_PETICION = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")


def _error(clase, codigo: int):
    """Construye una excepcion real del SDK sin que haya habido ninguna llamada."""
    if clase in (APITimeoutError, APIConnectionError):
        return clase(request=_PETICION)
    return clase("simulado", response=httpx.Response(codigo, request=_PETICION), body=None)


class FallaNVeces:
    """Falla las primeras `n` llamadas y despues funciona.

    Es una clase y no una funcion porque necesita recordar cuantas veces la han
    llamado. `self.llamadas` tambien sirve para comprobar en el test que se
    llamo el numero exacto de veces que esperabas.
    """

    def __init__(self, n: int, error=RateLimitError, codigo: int = 429, resultado: str = "ok"):
        self.n = n
        self.error = error
        self.codigo = codigo
        self.resultado = resultado
        self.llamadas = 0

    def __call__(self):
        self.llamadas += 1
        if self.llamadas <= self.n:
            raise _error(self.error, self.codigo)
        return self.resultado


class Esperas:
    """Sustituto de time.sleep que apunta las esperas en vez de dormirlas."""

    def __init__(self):
        self.registradas: list[float] = []

    def __call__(self, segundos: float) -> None:
        self.registradas.append(segundos)


# ---------------------------------------------------------------------------
# 4. LAS TRES PRUEBAS
# ---------------------------------------------------------------------------


def prueba_1_se_recupera():
    print("Prueba 1 - falla dos veces (429) y funciona a la tercera")
    fn = FallaNVeces(2)
    esperas = Esperas()
    resultado = con_reintentos(fn, dormir=esperas)

    assert resultado == "ok"
    assert fn.llamadas == 3, fn.llamadas
    assert len(esperas.registradas) == 2
    # El backoff se duplica: el segundo intento espera mas que el primero.
    assert esperas.registradas[1] > esperas.registradas[0]
    print(f"  -> resultado={resultado!r}  llamadas={fn.llamadas}")
    print(f"  -> esperas={[round(e, 2) for e in esperas.registradas]}  (duplicandose + jitter)\n")


def prueba_2_se_rinde():
    print("Prueba 2 - falla siempre: tiene que rendirse, no quedarse en bucle")
    fn = FallaNVeces(99)
    esperas = Esperas()
    try:
        con_reintentos(fn, max_intentos=4, dormir=esperas)
    except RateLimitError:
        pass
    else:
        raise AssertionError("tenia que relanzar la excepcion")

    assert fn.llamadas == 4, fn.llamadas
    # Cuatro intentos, TRES esperas: el ultimo no duerme antes de rendirse.
    assert len(esperas.registradas) == 3, esperas.registradas
    print(f"  -> llamadas={fn.llamadas}  esperas={len(esperas.registradas)}  (la ultima no duerme)\n")


def prueba_3_no_reintenta_400():
    print("Prueba 3 - un 400 no se reintenta: el error es mio, no del servicio")
    fn = FallaNVeces(99, error=BadRequestError, codigo=400)
    esperas = Esperas()
    try:
        con_reintentos(fn, dormir=esperas)
    except BadRequestError:
        pass
    else:
        raise AssertionError("tenia que salir a la primera")

    assert fn.llamadas == 1, fn.llamadas
    assert esperas.registradas == []
    print(f"  -> llamadas={fn.llamadas}  esperas={len(esperas.registradas)}  (sale a la primera)\n")


def demo_con_esperas_reales():
    print("Demo - el mismo caso pero durmiendo de verdad, para verlo pasar")
    fn = FallaNVeces(2, error=InternalServerError, codigo=503)
    inicio = time.perf_counter()
    resultado = con_reintentos(fn, base=0.5, jitter_max=0.3)
    print(f"  -> {resultado!r} en {time.perf_counter() - inicio:.2f}s reales\n")


if __name__ == "__main__":
    random.seed(7)  # jitter reproducible mientras estudias esta salida
    prueba_1_se_recupera()
    prueba_2_se_rinde()
    prueba_3_no_reintenta_400()
    demo_con_esperas_reales()
    print("Las tres pruebas pasaron. Cero llamadas a la red, cero tokens.")
