"""Ejecución de una consulta en el orquestador, registrando cada paso del flujo de delegación."""
import logging
from typing import Optional

from langgraph.errors import GraphRecursionError
from langgraph.graph.state import CompiledStateGraph

from config import RECURSION_LIMIT
from state import initial_state
from tracing import TraceRecorder

logger = logging.getLogger(__name__)


async def run_query(graph: CompiledStateGraph, question: str, recorder: Optional[TraceRecorder] = None,
                    recursion_limit: int = RECURSION_LIMIT) -> dict:
    """Ejecuta el grafo y devuelve el estado final. `recursion_limit` es el respaldo de las guardas del supervisor."""
    recorder = recorder or TraceRecorder(echo=None)
    recorder.start(question)
    final_state: dict = {}
    try:
        async for mode, chunk in graph.astream(initial_state(question), config={"recursion_limit": recursion_limit},
                                               stream_mode=["updates", "values"]):
            if mode == "values":
                final_state = chunk
                continue
            for node, update in chunk.items():
                recorder.on_update(node, update or {})
    except GraphRecursionError:
        error = f"Se alcanzó el límite de {recursion_limit} pasos sin una respuesta final."
        logger.warning(error)
        recorder.finish("", error=error)
        return {**final_state, "task_completed": False, "final_answer": ""}
    recorder.finish(final_state.get("final_answer", ""))
    return final_state
