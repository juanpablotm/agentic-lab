"""D01 - Anatomia de una llamada.

Objetivo: entender el JSON crudo que viaja, sin SDK de por medio.
Hecho cuando: puedes explicar cada campo del request y del response sin
mirar la documentacion.

    cd ~/Desktop/Agentic-Lab/py
    uv run semanas/s01/d01_anatomia.py

Hoy NO se usa `anthropic` ni `openai`. Solo `httpx`, que es un cliente HTTP
generico y no sabe nada de LLMs. Esa es toda la gracia: lo que los SDK te
esconden son unas 15 lineas de JSON.

Regla 03: primero a mano, despues el framework.
"""

from __future__ import annotations
import json
import sys
import truststore
truststore.inject_into_ssl()
from pathlib import Path

# precios.py vive dos carpetas mas arriba. Python busca modulos en sys.path,
# que NO incluye la carpeta desde la que lanzas el comando sino la del script.
# Es el mismo concepto que el PATH del shell, pero para modulos.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import os

import httpx
import tiktoken
from dotenv import load_dotenv

from precios import PRECIOS

load_dotenv()


# --------------------------------------------------------------------------
# Material del dia: tres textos de dominio, de longitudes muy distintas.
# --------------------------------------------------------------------------

TEXTOS = {
    "corto": "Autorizar consulta de medicina general para el afiliado 4471.",
    "medio": (
        "El afiliado reporta dolor abdominal persistente desde hace tres dias. "
        "Acudio a emergencias del centro afiliado el 14 de septiembre. Se solicita "
        "autorizacion para sonografia abdominal y analitica completa. El plan "
        "corresponde a Plan Familiar Plus con cobertura de 80% en estudios de "
        "imagen y 100% en laboratorio, sujeto a periodo de carencia cumplido."
    ),
    "largo": (
        "RECLAMACION No. 2026-08841. Tipo: reembolso por gastos medicos incurridos "
        "fuera de la red. Fecha del evento: 2 de septiembre de 2026. El afiliado, "
        "titular del Plan Familiar Plus desde marzo de 2023, acudio a un centro no "
        "afiliado en la provincia de Puerto Plata durante un viaje personal, por un "
        "cuadro de deshidratacion severa que requirio hidratacion intravenosa y "
        "observacion durante seis horas. Presenta factura por RD$ 18,450.00, "
        "desglosada en honorarios medicos, insumos y uso de sala de observacion. "
        "Adjunta informe medico firmado, copia de cedula y comprobante fiscal valido. "
        "La poliza contempla reembolso por atencion de urgencia fuera de red hasta un "
        "tope anual, con coaseguro del 30% a cargo del afiliado, siempre que el evento "
        "califique como urgencia medica documentada y se notifique dentro de los "
        "siguientes treinta dias calendario. El afiliado notifico el 9 de septiembre. "
        "Se requiere validar vigencia de la poliza, cumplimiento del plazo de "
        "notificacion, calificacion del evento como urgencia y calculo del monto "
        "reembolsable neto de coaseguro."
    ),
}

TEXTOS_INGLES= {
    
    "short": "Authorize a general medicine consultation for member 4471.",

    "medium": (

        "The member reports persistent abdominal pain for the past three days. "

        "They visited the emergency department of the affiliated medical center on September 14. "

        "Authorization is requested for an abdominal ultrasound and complete laboratory tests. "

        "The plan corresponds to Family Plus Plan, with 80% coverage for imaging studies and "

        "100% coverage for laboratory tests, subject to the waiting period having been fulfilled."

    ),

    "long": (

        "CLAIM No. 2026-08841. Type: reimbursement for medical expenses incurred "

        "outside the network. Date of event: September 2, 2026. The member, "

        "holder of the Family Plus Plan since March 2023, visited a non-network "

        "medical center in the province of Puerto Plata during a personal trip due to "

        "severe dehydration that required intravenous hydration and "

        "observation for six hours. A bill for RD$18,450.00 is submitted, "

        "itemized into medical fees, supplies, and use of the observation room. "

        "The member also provides a signed medical report, a copy of their ID, and a valid tax receipt. "

        "The policy provides reimbursement for emergency care received outside the network up to an "

        "annual limit, with 30% coinsurance payable by the member, provided that the event "

        "qualifies as a documented medical emergency and is reported within the "

        "following thirty calendar days. The member reported the event on September 9. "

        "It is necessary to verify the policy's validity, compliance with the "

        "notification deadline, qualification of the event as an emergency, and calculation of the "

        "net reimbursable amount after coinsurance."

    ),


}

# --------------------------------------------------------------------------
# BLOQUE 1 - El tokenizador
# --------------------------------------------------------------------------


def explorar_tokenizador(parametro: dict) -> None:
    enc = tiktoken.get_encoding("o200k_base")
    for nombre, texto in parametro.items():
        tokens = enc.encode(texto)
        print("Canitdad de tokens del texto " + nombre + ":" + str(len(tokens)) + " con una razon de: " + str(len(texto)/len(tokens)))
        print("decode de los primeros quince tokens del texto " + nombre + ":")
        for i in range(14):
            trozo = enc.decode([tokens[i]]) 
            print("trozo" + str(i+1) + ":" + trozo)
            
        
        
    
    """
    Preguntas que tienes que poder responder al terminar:
      - Cuantos caracteres tiene un token, en promedio, en tu espanol?
      - Que pasa con "autorizacion", "sonografia", "RD$ 18,450.00" y "2026-08841"?
      - Traduce el texto corto al ingles y cuentalo. Cual sale mas barato?
    """
    raise NotImplementedError("D01 - escribe esto")


# --------------------------------------------------------------------------
# BLOQUE 2 - La llamada cruda
# --------------------------------------------------------------------------


def llamada_cruda_anthropic(prompt: str) -> dict:
    """POST a la API de Anthropic con httpx. Sin SDK.

    Devuelve el JSON crudo, tal cual, sin tocarlo.

    Datos que necesitas (esto es referencia, no la solucion):
      URL      https://api.anthropic.com/v1/messages
      headers  x-api-key, anthropic-version: 2023-06-01, content-type: application/json
      body     model, max_tokens, messages[{role, content}]

    Imprime el JSON del REQUEST antes de enviarlo y el del RESPONSE despues.
    Mirar los dos lado a lado es el ejercicio.
    """

    modelo = os.getenv("ANTHROPIC_MODELO")
    api_key  = os.getenv("ANTHROPIC_API_KEY")

    url = "https://api.anthropic.com/v1/messages"

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    body = {
        "model": modelo,
        "max_tokens": 200,
        "messages": [{"role": "user", "content": prompt}]
    }

    print(json.dumps(body, indent=2, ensure_ascii=False))
    
    response = httpx.post(
        url,
        headers=headers,
        json=body,
        timeout=30.0
    )

    
    print(response.status_code)

    return response.json()



def llamada_cruda_openai(prompt: str) -> dict:
    """Lo mismo contra OpenAI.

      URL      https://api.openai.com/v1/chat/completions
      headers  Authorization: Bearer <clave>, content-type: application/json
      body     model, messages[{role, content}], max_completion_tokens

    Cuando tengas los dos JSON delante, contesta en el diario:
      - Donde esta el texto en cada uno? Por que uno es una lista de bloques
        y el otro una lista de "choices"?
      - Como se llama el campo que dice por que paro, en cada uno?
      - Como se llaman los tokens de entrada y de salida, en cada uno?
    """
    api_key=os.getenv("OPENAI_API_KEY")
    modelo = os.getenv("OPENAI_MODELO")
    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    body = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 200,
        "reasoning_effort": "minimal"
    }

    print(json.dumps(body, indent=2, ensure_ascii=False))

    response = httpx.post(
        url,
        headers=headers,
        json=body,
        timeout=30.0
    )

    print(response.status_code)
    return response.json()

    



# --------------------------------------------------------------------------
# BLOQUE 3 - Predecir antes de pagar
# --------------------------------------------------------------------------


def predecir_coste(texto: str) -> float:

    enc = tiktoken.get_encoding("o200k_base")
    tokens = enc.encode(texto)
   
    costoInput = len(tokens)/1000000
    costoOutput = 200 * 5/1000000
    prediccionDeCosto = costoInput + costoOutput

    llamada = llamada_cruda_anthropic(texto)
    costoLLamadaOutput = llamada["usage"]["output_tokens"] * 5/1000000
    costoLLamadaInput = llamada["usage"]["input_tokens"]/1000000
    costoReal = costoLLamadaInput + costoLLamadaOutput

    diferencia = costoReal - prediccionDeCosto

    print(costoReal)
    print(prediccionDeCosto)
    return round(diferencia,10)

    


# --------------------------------------------------------------------------

if __name__ == "__main__":
   
    resultado = predecir_coste(TEXTOS["medio"])
    print(resultado)
    
    



