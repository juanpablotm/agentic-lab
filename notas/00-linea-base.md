# Línea base — D0.3

Escrito el 10 de septiembre de 2026, antes de saber casi nada.

En D77 (22 de noviembre) voy a releer este archivo y responder lo mismo otra vez.
La diferencia entre las dos versiones es la única prueba real de que estas once
semanas sirvieron para algo. Por eso conviene ser honesto aquí, no quedar bien.

---

## 1. Qué creo que es un agente

*(Escribe esto ANTES de leer nada. Con tus palabras, sin buscar. Si te sale flojo,
mejor: eso es exactamente lo que queremos medir.)*

*Para mi un agente de IA es un sistema de inteligencia artificial que va mas allá de solo responder preguntas, es un sistema que sigue un flujo de trabajo completo, en base a un prompt se plantea un plan, razona en base a este y luego de esto busca herramientas para realizar su tarea si es necesario, todo esto con un objetivo final, hasta que el agente no cumpla su objetivo no se detiene.*




**Después de leer *Building Effective Agents* y la unidad 1 de Hugging Face, ¿qué
cambió?**

*Mi idea se acercaba bastante a lo que realmente entiendo ahora por agente, lo sigo definiendo de una manera muy parecida, para mi un agente es un sistema de inteligencia artificail actualmetne manejado principalmente por un LLM el cual sigue un proceso de pensamiento sobre un "problema", tiene la capacidad de dividir este problema en secciones y completa cada una de estas secciones realizando acciones, que son estas acciones? pueden ser simples acciones tomadas por el LLM en base a su conocimiento crudo o lo mas comun que es que tenga que ejecutar tools dadas en su harnes, luego de ejecutar la tool el agente tiene la capacidad de observar el resultado y generar una conlusion de si el resultado es lo que necesitaba o no, si hubo un error o algo no salio como esperaba, en base a esto puede decidir si seguir con la siguiente accion o tomar otra estrategia, todo esto se repite hasta que un momento en el cual este observando el resultado de una accion y entrando en proceso de pensamiento y analisis, el agente se percate de que ya ha finalizado la tarea dada, algun limite se ha alcanzado, necesita mas informacion del usuario o cualquier otra razon por la que debe terminar el proceso.*



---

## 2. Workflow vs agente

*Un workflow tiene definidos de antemano los pasos necesarios para completar un objetivo, mientras que un agente recibe un problema u objetivo y tiene la capacidad de decidir de manera flexible qué acciones realizar para resolverlo según el contexto y los resultados que va obteniendo.*

*El workflow conviene cuando nuestro flujo esta muy definido y poco supuesto a cambios, mientras que el agente nos sirve para cuando queremos mas flexibilidad y no sabemos exactamente cuantas ni cuales acciones son necesarias para realizar una tarea.

---

## 3. Cinco preguntas que quiero responder en once semanas

*(Preguntas de verdad, no temario. "¿Cómo sé si mi agente mejoró?" es una pregunta.
"Aprender LangGraph" no lo es.)*

1. Como evaluo de manera correcta si una implementacion en la arnes de mi modelo fue o no una mejora para los procesos?
2. Como puedo usar subagentes y orquestadores de manera eficiente, correcta y cuando es realmente necesario?
3. Como puedo mejorar realmente a mi equipo con el conocimiento adquirido en estos meses?
4. Como puedo automatizar procesos de trabajo de programacion de manera eficiente y con un manejo de errores correspondiente?
5. Cuales son las habilidades realmente necesarias para ser un desarrollador agentico profesional?

---

## 4. Qué creo que va a ser lo más difícil

*Saber cuando un cambio realmente sumo valor y no solo entorpecio y complico el proceso sin necesidad alguna.*



---

## 5. De dónde parto

*Se manejar herramientas comom claude code, se que es un agente y tengo conceptos de IA como machine learnign y deep learning*



---

## 6. Autoevaluación de las 24 competencias

Puntúa cada una del 0 al 3, hoy, sin generosidad:

- **0** — no sé ni qué significa la frase
- **1** — entiendo el concepto, no lo he hecho
- **2** — lo he hecho una vez, con ayuda
- **3** — lo sé hacer solo y lo puedo explicar

| # | Competencia | Hoy | D77 |
|---|---|---|---|
| 1 | Explicar el bucle de un agente y escribirlo desde cero sin framework | 1 | |
| 2 | Forzar salidas estructuradas con validación y bucle de reparación | 1 | |
| 3 | Diseñar herramientas con esquemas y descripciones que el modelo use bien | 1| |
| 4 | Elegir entre reglas, workflow, agente y multiagente, y justificarlo con datos | 1| |
| 5 | Implementar los cinco patrones: cadena, enrutamiento, paralelo, orquestador, evaluador | 1| |
| 6 | Construir un grafo con estado persistente y reanudación tras caída |0| |
| 7 | Implementar aprobación humana con edición de estado y auditoría |1| |
| 8 | Comparar SDKs con criterios y recomendar uno para un contexto dado |1| |
| 9 | Montar un RAG híbrido y medir recall@k antes de tocar el prompt |2| |
| 10 | Diseñar memoria de corto y largo plazo con segmentación por usuario |1| |
| 11 | Reducir el coste de un agente con context engineering sin perder calidad |1| |
| 12 | Construir un servidor MCP con autenticación y permisos por rol |1| |
| 13 | Escribir un cliente MCP y explicar el protocolo a dos audiencias |1| |
| 14 | Instrumentar trazas y leer un panel de coste, latencia y errores |1| |
| 15 | Construir un dataset de evaluación con casos límite y ground truth |0| |
| 16 | Calibrar un juez con IA contra etiquetas humanas y medir el acuerdo |0| |
| 17 | Evaluar trayectorias, no solo respuestas finales |1| |
| 18 | Montar regresión de calidad en CI con umbrales que bloquean el merge |1| |
| 19 | Identificar y mitigar los diez riesgos de OWASP para aplicaciones agénticas |1| |
| 20 | Ejecutar un red team contra mi propio agente y documentar los hallazgos |1| |
| 21 | Aplicar minimización y tokenización de datos personales de salud |1| |
| 22 | Desplegar un agente con ejecución duradera, límites de gasto y runbook |1| |
| 23 | Integrar un agente con sistemas heredados de forma idempotente |0| |
| 24 | Presentar un caso de uso con métricas de negocio y plan piloto | 1| |

**Total hoy: ___ / 72**

---

## 7. El compromiso

*Completare todo el contenido de la ruta y me volvere un desarrollador agentico*

## 8. Ejemplos articulo antrhopic

*The augmented LLM: Un LLM clasico con la suma de herramientas y memoria, un ejemplo en base a mi carrera: No entiendo un tema sobre el desarrollo de agentes y le pregunto a claude mediante un chat normal, este va a buscar en internet, hacer calculos si es necesario, guardar lo necesario en memoria y luego responderme, si justo despues de eso le hago otra pregunta el podra acceder a su memoria para consultar.

*Prompt chaining: Encadena prompts sacrificando un poco de latencia por una mejor presicion a la hora de completar varias tareas consecuentes, un ejemplo con mi carrera seria: primera prompt -> documentar un proceso el resultado de esto lo recibe el siguiente prompt con la indicacion de indicar que otros documentos estan relacionados y pasarlo luego a otro 3er prompt que haga una traduccion de los documentos a varios idiomas que se necesiten.*

*Routing: Es util para tareas complejas y con clasificaciones bien claras, un ejemplo podemos tener un sistema con un LLM router y que divida resolucion de tikets dependiendo de la clasificacion, si le llega un ticket de qa o de diseño etc.*

*Parallelization: Realiza multiples llamadas simultaneas para resolver una tarea, en el caso de que sea para mejorar velocidad y la tarea es bien dividible se puede utilizar para generar un reporte evaluando diferentes partes de un proceso, cada parte la evalua un LLM CALL, la otra opcion es si se quiere que el sistema dividido haga un tipo de "votacion", cuando esto es asi un ejemplo bueno seria la generacion de ideas para mejorar la app, cada CALL al LLM generaria diferentes ideas y estos votarian por las que mejor les parecen.*

*Orchestrator-workers: Sirve para cuando tenemos muchas subtareas pero no sabemos exactamente como se tienen que ejecutar ni cuantas son: No sirve por ejemplo para escribir funcionalidades que tienen tareas en backend , frontend, y testing, en estos casos el orquestador puede identificar  cuantas subtareas son y un plan para resolverlas, luego de esto pasarla a los workers.*

*Evaluator-optimizer: El nombre lo explica solo, tenemos un LLM que resuelve una tarea y otro que la evalua y no la da por terminada hata que entienda que cumplio con todos los requerimiento, mientras la tarea no sea cumplida se la devuelve al prmiero con anotacion para que la siga puliendo, un ejemplo sencillo de un caso de uso seria para mejora la seguridad de un app en base a ciertas directices.*