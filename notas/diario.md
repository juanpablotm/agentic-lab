# Diario de aprendizaje

Regla 08: una línea por día. Qué hice, qué se rompió, qué aprendí.
En la semana 11 esto se convierte en el artículo técnico.

| Día | Qué hice | Qué se rompió | Qué aprendí |
|-----|----------|---------------|-------------|
| D0.1 (sáb 5 sep) | Monté el entorno y publiqué `agentic-lab` en GitHub con la estructura del laboratorio. | Todo: el `PATH` de Homebrew, `gh` que nunca se instaló, y `uv` rechazado por el proxy TLS del trabajo. | Que instalar no es lo mismo que estar disponible, y que la fricción de entorno corporativo es parte del trabajo, no un obstáculo para el trabajo. |
| D0.2 (7–8 sep) | Capa multiproveedor: una sola función y cuatro backends (Anthropic, OpenAI, Groq, Gemini) devolviendo texto, tokens, latencia y coste por llamada. | `coste()` usaba variables que no existían, así que las cuatro funciones reventaban; y `gpt-5-nano` devolvió texto vacío. | Que los tres modelos que sí respondieron sobre mi propio sector se equivocaron — y el más caro se equivocó con más seguridad. |

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
