# agentic-lab

Este repositorio es mi laboratorio de once semanas para convertirme en desarrollador
agentico. Empiezo el 4 de septiembre de 2026 y termino el 22 de noviembre de 2026.

## Por que existe

Estoy de pasante en Grupo Humano (Humano Seguros y ARS Primera). La vacante que hay
abierta es de desarrollador agentico, asi que en estas once semanas quiero pasar de
"se programar y he tocado un par de frameworks de agentes" a poder sostener una
entrevista tecnica de agent engineer y llevarle a mi supervisor una propuesta real
con evidencia en la mano.

Cuando termine quiero poder decir "soy desarrollador agentico" y senalar codigo,
mediciones y proyectos, no intenciones.

## Como trabajo aqui

1. **Codigo todos los dias.** Leer no cuenta. Cada dia termina con algo que corre y
   esta commiteado.
2. **Un solo repositorio.** Este. Con carpetas por semana, no un cementerio de
   carpetas sueltas.
3. **Primero a mano, despues el framework.** Nunca uso una abstraccion antes de haber
   escrito su version fea.
4. **Presupuesto duro.** Limite de gasto en cada consola, `max_steps` y contador de
   tokens en todo bucle.
5. **Todo se mide.** Coste, latencia y aciertos por cada cambio. "Se siente mejor" no
   es un resultado.
6. **Dominio de seguros siempre.** Reclamaciones, autorizaciones, coberturas y
   afiliados. Aprendo agentes y el vocabulario del negocio a la vez.
7. **Datos sinteticos, sin excepcion.** Jamas datos reales de afiliados. En una ARS
   esto no es negociable.
8. **Diario de una linea.** Cada dia en `notas/diario.md`.
9. **Enseno lo que aprendo.** Cada viernes, una cosa que pueda explicarle a mi
   supervisor en tres minutos.

## Estructura

```
py/          Codigo Python (el eje principal)
  core/      Piezas reutilizables: cliente LLM, trazas, guardas
  semanas/   Ejercicios y proyectos por semana (s00, s01, ...)
ts/          Track TypeScript: interfaces, despliegue, servidores MCP remotos
notas/       Diario, linea base, decisiones de arquitectura
datos/       Datos SINTETICOS de dominio asegurador
```

## Los nueve proyectos

| # | Semana | Proyecto |
|---|--------|----------|
| 1 | S1 | Extractor documental con contrato |
| 2 | S2 | `microagent`, mi propio framework |
| 3 | S3 | Tres arquitecturas, una tarea |
| 4 | S4 | Agente de autorizaciones con aprobacion humana |
| 5 | S5 | Chat agentico full-stack desplegado |
| 6 | S6 | Copiloto de conocimiento con citas |
| 7 | S7 | Servidor MCP de sistemas internos |
| 8 | S8 | Suite de evaluacion con regresion en CI |
| 9 | S9 | Informe de red team de mis propios agentes |
| - | S10-S11 | Capstone: sistema agentico de dominio asegurador |

## Secretos

Las claves viven en `.env`, que esta en `.gitignore`. `.env.example` documenta que
variables hacen falta. Ninguna clave entra a este repositorio, nunca.

---

Juan Pablo Tavares Minervino
