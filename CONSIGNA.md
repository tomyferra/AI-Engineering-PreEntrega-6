# Pre-entrega 6: Orquestador multi-agente especializado

## ¿Qué debes construir?

Un **prototipo funcional de un Orquestador Multi-Agente de Análisis e Investigación**. El sistema debe ser capaz
de procesar una solicitud de usuario que requiera **al menos dos dominios de especialización distintos** y una
**fase de síntesis final**.

## Requerimientos técnicos

1. **Topología jerárquica:** un nodo **Supervisor** que actúa como router inteligente y controlador de flujo.
2. **Mínimo de 2 agentes especialistas:**
   - **Agente de Búsqueda/Investigación:** con herramientas para consultar fuentes externas (puede usarse
     Tavily o una búsqueda simulada sobre la Vector DB de pre-entregas anteriores).
   - **Agente de Análisis/Cómputo:** especializado en procesar los datos obtenidos (análisis de sentimiento,
     cálculos matemáticos o validación de esquemas).
3. **Estado compartido estructurado:** un esquema de `State` en LangGraph que permita rastrear qué agente
   contribuyó con qué información, evitando la pérdida de contexto en la comunicación asíncrona.
4. **Flujo de supervisión:** el supervisor decide si la tarea está completa o si algún especialista debe
   refinar su output antes de dar la respuesta final.

## Pasos sugeridos

1. **Definir el estado:** una clase `TypedDict` que herede de `MessagesState`. Evaluar campos extra como
   `next_agent` o `task_completed`.
2. **Crear los agentes especialistas:** funciones que usen `create_react_agent` de LangGraph (o prompts
   específicos para cada rol). Cada uno debe tener **herramientas acotadas**.
3. **Implementar el supervisor (el cerebro):** su prompt debe ser claro: *"Dada la conversación actual,
   ¿quién debe intervenir ahora o es momento de finalizar?"*. Debe mapear sus respuestas a los nombres de los
   nodos del grafo.
4. **Construir el grafo:** usar `add_node` para cada agente y para el supervisor, y definir las
   **Conditional Edges** que conectan al supervisor con los especialistas.
5. **Probar la interacción:** lanzar una consulta que obligue al supervisor a enviar la tarea al
   Investigador, recibir el dato, enviarlo al Analista y finalmente cerrar la conversación.

## Errores comunes a evitar

| Error | Descripción | Cómo evitarlo |
|---|---|---|
| **"Supervisor infinito"** | No definir una condición de parada clara: supervisor y agentes entran en un bucle de correcciones eternas. | Contador de pasos o criterio de "suficiencia" estricto. |
| **Contaminación de contexto** | Pasar todo el historial a todos los agentes en cada turno. | Que el especialista reciba solo la instrucción específica y el contexto necesario, no toda la metadata del sistema. |

## Instrucciones de la práctica

### Estructura del repositorio

- `state.py`: esquema de datos compartido.
- `agents/`: directorio con los especialistas (ej. `research_agent.py`, `analyst_agent.py`).
- `main.py` o `graph.py`: definición del grafo principal.

### Implementación del grafo

- Usar `StateGraph` de LangGraph.
- Definir al menos un nodo **Supervisor** que decida dinámicamente el flujo usando `Literal` en el retorno de
  las aristas condicionales.

### Herramientas (tools)

- Los agentes deben tener **al menos una herramienta funcional** (`TavilySearchResults` o una función propia
  que consulte una base de datos).

### Validación

- Implementar un nodo de **Validation** o asegurar que el Supervisor tenga una **rúbrica personalizada** en su
  prompt para validar los resultados de los especialistas antes de dar el `END`.

### Documentación

- El `README.md` debe incluir un **diagrama del grafo** (puede generarse con
  `graph.get_graph().draw_mermaid_png()`).
- Explicar brevemente **por qué se eligió esa topología** y **cómo se manejan los posibles conflictos entre
  agentes**.

## 📦 Qué se entrega y en qué formato

- **Tipo:** 💻 Código — un repositorio de GitHub.
- **Artefacto concreto:**
  - Repositorio con `state.py`, la carpeta `agents/` (investigación + análisis), el grafo con nodo Supervisor
    y un `README.md` con el diagrama Mermaid del grafo y la explicación de la topología elegida.
  - Un **video corto o notebook** que demuestre el flujo de delegación.
- **Qué NO hace falta:** el video/notebook es una demo del flujo, no un informe escrito.
