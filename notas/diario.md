# Diario de aprendizaje

Regla 08: una línea por día. Qué hice, qué se rompió, qué aprendí.
En la semana 11 esto se convierte en el artículo técnico.

| Día | Qué hice | Qué se rompió | Qué aprendí |
|-----|----------|---------------|-------------|
| D0.1 (sáb 5 sep) | Monté el entorno y publiqué `agentic-lab` en GitHub con la estructura del laboratorio. | Todo: el `PATH` de Homebrew, `gh` que nunca se instaló, y `uv` rechazado por el proxy TLS del trabajo. | Que instalar no es lo mismo que estar disponible, y que la fricción de entorno corporativo es parte del trabajo, no un obstáculo para el trabajo. |
| D0.2 (7–8 sep) | Capa multiproveedor: una sola función y cuatro backends (Anthropic, OpenAI, Groq, Gemini) devolviendo texto, tokens, latencia y coste por llamada. | `coste()` usaba variables que no existían, así que las cuatro funciones reventaban; y `gpt-5-nano` devolvió texto vacío. | Que los tres modelos que sí respondieron sobre mi propio sector se equivocaron — y el más caro se equivocó con más seguridad. |
| D0.3 (10–17 sep) | Leí *Building Effective Agents* y las unidades 0 y 1 de Hugging Face, escribí mi línea base, resumí los patrones con ejemplos de seguros y cerré `llamar_ollama`. | Nada de código. Se rompió mi idea de que `uv` busca el proyecto hacia abajo, y tardé en encontrar un `.env` que llevaba media hora delante de mí. | Que ya tenía el bucle del agente en la cabeza sin saber su nombre: observar el resultado, decidir si sigo, y parar por objetivo cumplido o por límite alcanzado. |
| D01 (18–19 sep) | Llamé a Anthropic y OpenAI con `httpx`, sin SDK, y diseccioné el JSON de ida y el de vuelta. Medí el impuesto del idioma, provoqué cortes a propósito y estimé costes antes de pagarlos. | Filtré mi clave de Anthropic imprimiendo el cuerpo con las variables cruzadas. Y el proxy TLS otra vez, ahora contra `httpx`, que ignora `SSL_CERT_FILE`. | Que una respuesta puede llegar con código 200, JSON válido y texto dentro, y aun así ser basura. El único testigo es `stop_reason`. |

---

## D0.1 — sábado 5 de septiembre

**Lo que quedó hecho.** Repositorio público `juanpablotm/agentic-lab` con `py/`, `ts/`,
`notas/` y `datos/`. `.gitignore` que bloquea `.env` y cualquier clave, `.env.example`
con los cinco proveedores de D0.2, README con mi objetivo de once semanas y las nueve
reglas. Herramientas verificadas: git, Node 26.8.1, pnpm 11.25, gh 2.100, uv 0.12.10 y
Python 3.12.14.

**Lo que se rompió, en orden.**

1. `brew: command not found` justo después de instalar Homebrew. Dos causas
   encadenadas: pegué cuatro comandos de golpe y el instalador, que es interactivo, se
   tragó los otros tres como respuestas a sus propias preguntas — así que
   `brew install` nunca corrió. Y en Apple Silicon Homebrew vive en `/opt/homebrew`,
   que no está en el `PATH` por defecto.
2. `gh: command not found`. No era un problema nuevo, era consecuencia del anterior.
3. Escribí `config --global user.name` sin el `git` delante, así que mi nombre quedó
   con la configuración vieja y el primer commit salió firmado con un doble espacio.
4. Creí que el código de `gh auth login` se enviaba por correo. No: el *device flow*
   lo imprime en la terminal y uno lo pega en `github.com/login/device`.
5. `uv` falló con `invalid peer certificate: UnknownIssuer` al bajar Python. El único
   fallo que no fue error mío.

**El interesante: el proxy TLS.** La red del trabajo intercepta el tráfico HTTPS, lo
descifra y lo vuelve a firmar con un certificado raíz corporativo. Ese raíz está en el
llavero de macOS, así que Homebrew, `curl`, `git` y `gh` pasaron sin enterarse. `uv`
trae su propio almacén de certificados, no conoce ese raíz y cortó la conexión. Se
resuelve con `UV_SYSTEM_CERTS=1`. Detalle completo en `entorno.md`.

**Lo que me llevo.**

- El `PATH` es una lista de carpetas y nada más. La mitad de los `command not found`
  de mi vida van a ser esto: el programa está instalado, pero su carpeta no está en la
  lista.
- Nunca pegar un bloque de comandos si alguno es interactivo.
- Diagnosticar antes de reinstalar. Un `which brew; ls /opt/homebrew/bin/brew` me dijo
  en dos segundos que Homebrew estaba bien y que el problema era otro. Reinstalar
  habría costado veinte minutos sin arreglar nada.
- Leer la cadena de `Caused by` de abajo hacia arriba. La última línea era la
  verdadera; las de arriba solo decían "no pude descargar".
- `git` y `gh` son herramientas distintas: uno es control de versiones local, el otro
  es el cliente de GitHub. Por eso `git auth login` no existe.
- Esto va a volver a salir en D0.2 cuando `httpx` llame a las APIs de los proveedores.

**Calibración.** D0.1 estaba presupuestado en 2 h y se fue bastante más, casi todo en
fricción de entorno. Normal el primer día. No es deuda.


---

## D0.2 — 7 y 8 de septiembre

**Lo que quedó hecho.** `py/hello_llm.py`: un solo comando llama a cuatro proveedores
con tres SDK distintos y devuelve la misma estructura `Respuesta` para todos. Tabla
final con tokens de entrada y salida, latencia y coste en USD. Precios en `precios.py`,
verificados contra las páginas oficiales. Claves en `.env`, límites de gasto puestos en
cada consola antes de usar ninguna.

Primera ejecución completa, prompt "¿qué es una ARS?":

| proveedor | modelo | ent | sal | seg | USD |
|---|---|---|---|---|---|
| anthropic | claude-haiku-4-5 | 23 | 55 | 1.55 | 0.000298 |
| openai | gpt-5-nano | 19 | 200 | 4.08 | 0.000081 |
| groq | gpt-oss-20b | 84 | 194 | 1.84 | 0.000064 |
| gemini | gemini-3.5-flash-lite | 14 | 42 | 16.79 | 0.000109 |

**Lo que se rompió.**

1. Copié la fórmula del coste tal cual me la explicaron, con `precio_entrada` y
   `precio_salida`, sin darme cuenta de que eso era pseudocódigo y esas variables no
   existían. Faltaba el paso previo: buscar el modelo en `PRECIOS` y desempaquetar la
   tupla. Como las cuatro funciones llaman a `coste()` al final, las cuatro fallaban, y
   yo pensaba que el problema estaba en las APIs.
2. OpenAI rechazó `max_tokens` y pidió `max_completion_tokens`.
3. Con 200 tokens, `gpt-5-nano` devolvió texto vacío: se los gastó razonando por dentro
   antes de escribir nada. Pagué 200 tokens por cero palabras.

**Decisiones de diseño que tomé.**

- Un modelo que no está en la tabla de precios lanza `ValueError` en vez de devolver
  `0.0`. Razón: en la semana 1 voy a decidir qué modelo va a producción con esta misma
  función. Perder una fila es recuperable; creerme una fila falsa, no.
- "Local" es una **categoría** de precio, no un modelo. Cuando implemente Ollama, el
  proveedor será quien declare que es gratis, no `coste()` quien lo adivine por el
  nombre del modelo.

**El hallazgo del día.** Los tres modelos que respondieron dijeron cosas distintas y
ninguno acertó con mi país. Anthropic situó las ARS en Colombia y las describió como
salud y seguridad ocupacional, que es una ARL, no una ARS. Groq dijo que eran del
sistema chileno, donde no existen. Gemini dio una definición genérica sin mojarse: la
única que no mintió, y la que menos dice. Yo trabajo en una ARS dominicana y ninguno la
mencionó. Un modelo no sabe de mi negocio; sabe de estadística sobre texto. Esta es la
razón entera del copiloto con citas de la semana 6, y me la enseñó mi propio hola mundo.
Guardo esta salida como primer caso de evaluación para D07.

**Lo que me llevo.**

- `max_tokens` no es un presupuesto que el modelo administra, es una guillotina del
  servidor. El modelo genera sin saber cuánto le queda y el corte llega a mitad de
  frase. Por eso hay que mirar `finish_reason` / `stop_reason` en cada respuesta: una
  respuesta truncada llega con un 200 OK y parece válida.
- El mismo prompt cuesta tokens distintos en cada casa: 14 en Gemini, 84 en Groq. Cada
  proveedor tiene su tokenizador y algunos añaden preámbulos internos que también se
  cobran. El precio por millón de tokens no te dice lo que te va a costar un prompt.
- Gemini tardó 16,79 s contra 1,84 s de Groq, siendo un modelo *lite*. Probablemente
  arranque en frío de la capa gratuita, pero no lo sé: es una sola medición, y medir una
  vez no es medir.
- Cuatro de mis cinco backends son el cliente de OpenAI con otra `base_url`. El
  proveedor no es una integración, es un parámetro.
- Si `uv run` funciona y el editor subraya en amarillo, el problema es del editor.
- Probar una función aislada antes de enchufarla al resto ahorra horas.

**Calibración.** El día se fue en el código, no en las APIs. El error de `coste()` me
costó bastante rato justamente porque el síntoma aparecía en otro sitio.


## D0.2 — 7 y 8 de septiembre

Mi definicion de agente: Para mi un agente de IA es un sistema de inteligencia artificial que va mas allá de solo responder preguntas, es un sistema que sigue un flujo de trabajo completo, en base a un prompt se plantea un plan, razona en base a este y luego de esto busca herramientas para realizar su tarea si es necesario, todo esto con un objetivo final, hasta que el agente no cumpla su objetivo no se detiene.



---

## D0.3 — del 10 al 17 de septiembre

**Lo que quedó hecho.** `notas/00-linea-base.md` completa: mi definición de agente antes y
después de leer, workflow vs agente, cinco preguntas para once semanas, lo que creo que será
lo más difícil, la autoevaluación de las 24 competencias (19/72) y los siete patrones del
artículo de Anthropic con un ejemplo de mi sector cada uno. Además cerré `llamar_ollama` y
recalibré las fechas del plan.

**Lo que más me llamó la atención.** Escribí mi definición de agente antes de leer nada y
después la volví a escribir. Lo que gané no fueron palabras nuevas: fue el paso de
**observación** y las **condiciones de parada**. Antes decía que el agente planifica y busca
herramientas hasta cumplir el objetivo. Después escribí que ejecuta, observa el resultado,
concluye si es lo que necesitaba, decide si sigue o cambia de estrategia, y termina cuando
la tarea está hecha *o se alcanza algún límite*. Eso es el bucle del agente, y lo tenía en
la cabeza sin saber que se llamaba así.

**Decisión que apliqué.** En `llamar_ollama`, "local" es una **categoría de precio**, no un
modelo. El proveedor declara que es gratis; `coste()` no lo adivina por el nombre. Así puedo
cambiar de modelo local sin tocar la tabla de precios. Lo dejé escrito en el docstring.

**Sobre la autoevaluación.** Saqué 19 de 72. El número global me parece bien calibrado, pero
la escala no: entre "no sé ni qué significa la frase" y "entiendo el concepto" hay un abismo.
La volveré a usar en D77 con el mismo criterio, que es lo único que la hace comparable, pero
no me voy a apoyar en ella más de lo que aguanta.

**Cosas pequeñas que aprendí.** Los archivos que empiezan con punto están ocultos por
convención. `uv` busca el `pyproject.toml` hacia arriba, nunca hacia abajo. Los corchetes de
`pip install 'smolagents[litellm]'` se llaman *extras*. Y `litellm` es, en grande, lo mismo
que escribí a mano en D0.2 — haberlo escrito primero hace que la librería no me parezca magia.


---

## D01 — 18 y 19 de septiembre

**Lo que quedó hecho.** `py/semanas/s01/d01_anatomia.py`: exploración del tokenizador, dos
llamadas crudas con `httpx` —Anthropic y OpenAI, sin ningún SDK— y una función que estima el
coste antes de gastarlo. Los dos JSON, el de ida y el de vuelta, diseccionados campo por campo.

**El fallo grave: filtré una clave.** Se me cruzaron las variables y la clave de Anthropic
acabó impresa en el campo `model` del cuerpo del request. La pegué después en un chat. Tuve
que revocarla y generar otra. El repositorio estaba limpio — `.env` nunca se versionó — así
que el daño quedó en la terminal y en el chat.

La lección no es "no imprimas las cabeceras". Es que **cualquier `print` puede filtrar un
secreto si una variable se va donde no debe**. Imprimir el cuerpo era correcto y necesario;
lo que falló fue el cuerpo, no la decisión de imprimirlo.

**El proxy TLS, tercera aparición.** Esta vez contra `httpx`, que ignora `SSL_CERT_FILE` y
`REQUESTS_CA_BUNDLE` porque trae su propio paquete de certificados fijado por dentro. Por eso
`tiktoken` (que usa `requests`) pasó y `httpx` no. Se resolvió con `truststore`, que hace que
Python use el llavero de macOS para todo.

**Lo que medí.**

| Medición | Resultado |
|---|---|
| Impuesto del idioma (misma frase) | 14 tokens en español contra 11 en inglés — **+27 %** |
| Mayúsculas | `Autorizar` = 2 tokens, `RECLAMACION` = **4** |
| Identificadores | `2026-08841` = **5 tokens** |
| Razón car/token | prosa 4,6 · documento con datos estructurados **4,0** |
| `reasoning_effort: minimal` | coste **−64 %**, y además respondió |
| Haiku contra gpt-5-nano, misma pregunta | **13× más caro** |
| Error de mi estimación de coste | 2,54 % sobre el total |

**El hallazgo del día.** Con `max_tokens: 10` la respuesta llegó con código 200, JSON
perfectamente formado, y el texto `# Agente de IA` — un encabezado de markdown completo. No
está vacío: pasaría cualquier comprobación de tipo `if texto:`. Y no contiene una sola idea.
El único sitio del universo donde consta que eso es basura es `stop_reason: "max_tokens"`.
Es peor que el caso de OpenAI con el contenido vacío, porque el vacío se detecta solo.

**Lo que me llevo.**

- Una llamada a un LLM es un POST de HTTP con un JSON en el cuerpo. Nada más. Los SDK
  construyen ese JSON y desenvuelven la respuesta en objetos; eso es todo lo que hacen.
- `max_tokens` limita **solo la salida** y lo pongo yo. La **ventana de contexto** limita
  entrada más salida y la pone el modelo. Son dos cosas distintas y las confundía.
- Un corte no es un desbordamiento: la guillotina la pongo yo.
- Hay dos capas: el objeto de `httpx` (`status_code`, `headers`) y el JSON del cuerpo
  (`stop_reason`, `usage`). `response.stop_reason` no existe.
- `content` en Anthropic es una lista de **partes de una respuesta**; `choices` en OpenAI es
  una lista de **respuestas alternativas**. Los dos se indexan con `[0]` y no son lo mismo.
- El mismo prompt: 12 tokens para OpenAI, 15 para Anthropic. Por eso estimar Anthropic con
  `tiktoken` arrastra un error estructural.
- `count_tokens` de Anthropic cuenta sin cobrar. No usarlo fue un error mío de criterio.
- Un error agregado pequeño puede esconder dos errores grandes de signo contrario. Mi 2,54 %
  es la suma de una estimación de entrada con el tokenizador equivocado y una de salida que
  me inventé.

**Lo que hice mal en el código y corregí.** Reescribí `coste()` con números mágicos en vez de
llamar a la que ya tenía; puse la llamada real dentro de la función que debía predecir sin
gastar; y mezclé la URL de Chat Completions con el campo `input`, que es de la Responses API.
Las tres son la misma clase de error: no mirar lo que ya existe antes de escribir.

**Nota de proceso.** El diario de D0.3 se perdió porque no lo commiteé. La regla 01 dice que
cada día termina commiteado, y esto es por qué.
