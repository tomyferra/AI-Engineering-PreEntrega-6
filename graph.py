"""Grafo jerárquico del orquestador:

    START -> supervisor --(route_from_supervisor)--> investigador -> supervisor   (ciclo de delegación)
                                                \\-> analista     -> supervisor
                                                \\-> sintetizador -> END
"""
from dataclasses import dataclass
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents import (
    build_supervisor_router,
    make_analyst_node,
    make_research_node,
    make_supervisor_node,
    make_synthesizer_node,
    route_from_supervisor,
)
from agents.specialist import SpecialistNode
from agents.supervisor import SupervisorNode
from agents.synthesizer import SynthesizerNode
from agents.validation import build_grounding_validator
from config import LLMSettings, get_llm_settings, get_tavily_api_key
from llm import build_chat_model
from state import ANALYST, RESEARCHER, SUPERVISOR, SYNTHESIZER, OrchestratorState
from tools import KnowledgeBase, build_math_tools, build_research_tools


@dataclass(frozen=True)
class OrchestratorNodes:
    supervisor: SupervisorNode
    researcher: SpecialistNode
    analyst: SpecialistNode
    synthesizer: SynthesizerNode


def build_graph(nodes: OrchestratorNodes) -> CompiledStateGraph:
    """Une los nodos. Recibe los nodos ya construidos (inyección de dependencias): testeable sin API keys."""
    workflow = StateGraph(OrchestratorState)

    workflow.add_node(SUPERVISOR, nodes.supervisor)
    workflow.add_node(RESEARCHER, nodes.researcher)
    workflow.add_node(ANALYST, nodes.analyst)
    workflow.add_node(SYNTHESIZER, nodes.synthesizer)

    workflow.add_edge(START, SUPERVISOR)
    workflow.add_conditional_edges(SUPERVISOR, route_from_supervisor,
                                   {RESEARCHER: RESEARCHER, ANALYST: ANALYST, SYNTHESIZER: SYNTHESIZER})
    # Topología jerárquica: los especialistas nunca hablan entre sí, siempre reportan al supervisor.
    workflow.add_edge(RESEARCHER, SUPERVISOR)
    workflow.add_edge(ANALYST, SUPERVISOR)
    workflow.add_edge(SYNTHESIZER, END)

    return workflow.compile()


def build_nodes(model: BaseChatModel, kb: KnowledgeBase, tavily_api_key: Optional[str] = None) -> OrchestratorNodes:
    return OrchestratorNodes(
        supervisor=make_supervisor_node(build_supervisor_router(model)),
        researcher=make_research_node(model, build_research_tools(kb, tavily_api_key),
                                      validator=build_grounding_validator(kb.documents.values())),
        analyst=make_analyst_node(model, build_math_tools()),
        synthesizer=make_synthesizer_node(model),
    )


def create_orchestrator(settings: Optional[LLMSettings] = None) -> CompiledStateGraph:
    """Orquestador listo para usar con el LLM de .env (llamar después de load_dotenv)."""
    model = build_chat_model(settings or get_llm_settings())
    return build_graph(build_nodes(model, KnowledgeBase(), get_tavily_api_key()))
