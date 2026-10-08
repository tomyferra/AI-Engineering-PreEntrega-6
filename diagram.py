"""Exportación del diagrama del grafo (Mermaid en texto y PNG)."""
import logging
from pathlib import Path
from typing import List

from langgraph.graph.state import CompiledStateGraph

logger = logging.getLogger(__name__)


def export_diagram(graph: CompiledStateGraph, out_dir: Path) -> List[Path]:
    """Escribe graph.mmd siempre y graph.png si el renderer (mermaid.ink, requiere internet) está disponible."""
    out_dir.mkdir(parents=True, exist_ok=True)
    drawable = graph.get_graph()
    mermaid_path = out_dir / "graph.mmd"
    mermaid_path.write_text(drawable.draw_mermaid(), encoding="utf-8")
    paths = [mermaid_path]
    try:
        png_path = out_dir / "graph.png"
        png_path.write_bytes(drawable.draw_mermaid_png())
        paths.append(png_path)
    except Exception as exc:  # noqa: BLE001 - el PNG es opcional; el .mmd ya documenta el grafo
        logger.warning("No se pudo generar el PNG del grafo: %s", exc)
    return paths
