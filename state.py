"""Estado compartido del orquestador multi-agente.

Hereda de MessagesState (conversación con el usuario) y agrega campos estructurados para saber
qué agente aportó qué información, qué decidió el supervisor en cada paso y cuándo cortar el flujo.
"""
import operator
from typing import Annotated, List, Literal, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState

# Nombres de los nodos del grafo: son el "vocabulario" con el que el supervisor enruta.
SUPERVISOR = "supervisor"
RESEARCHER = "investigador"
ANALYST = "analista"
SYNTHESIZER = "sintetizador"

SpecialistName = Literal["investigador", "analista"]
# Destinos posibles de la arista condicional del supervisor.
NextNode = Literal["investigador", "analista", "sintetizador"]


class ToolCallRecord(TypedDict):
    """Una llamada real a una herramienta dentro del especialista (evidencia verificable, no autodeclarada)."""

    tool: str
    args: dict
    result: str


class Contribution(TypedDict):
    """Aporte de un especialista: trazabilidad de quién produjo qué, con qué instrucción y con qué tools."""

    agent: SpecialistName
    attempt: int  # 1 = primer intento; >1 = refinamiento pedido por el supervisor
    instruction: str
    content: str
    tool_calls: List[ToolCallRecord]
    issues: List[str]  # problemas detectados por la validación determinista (vacío = aporte validado)


class RoutingDecision(TypedDict):
    """Decisión del supervisor en un paso. `forced` indica que una guarda de seguridad pisó al LLM."""

    step: int
    next: NextNode
    instruction: str
    reasoning: str
    forced: bool


class OrchestratorState(MessagesState):
    """Estado del grafo.

    - messages: pregunta del usuario y respuesta final (reducer add_messages). Los mensajes internos de los
      especialistas (tool calls, observaciones) NO se vuelcan acá: se resumen en `contributions`.
    - contributions / decisions: listas acumulativas (reducer operator.add) -> nunca se pierde un aporte.
    - next_agent / current_instruction: el "despacho" del supervisor hacia el próximo nodo.
    - delegations: contador de delegaciones, base de la condición de parada.
    - task_completed / final_answer: cierre del flujo por el sintetizador.
    """

    next_agent: NextNode
    current_instruction: str
    contributions: Annotated[List[Contribution], operator.add]
    decisions: Annotated[List[RoutingDecision], operator.add]
    delegations: int
    task_completed: bool
    final_answer: str


def initial_state(question: str) -> dict:
    """Estado inicial con todos los campos que leen los nodos."""
    return {
        "messages": [HumanMessage(question)],
        "next_agent": SYNTHESIZER,
        "current_instruction": "",
        "contributions": [],
        "decisions": [],
        "delegations": 0,
        "task_completed": False,
        "final_answer": "",
    }
