"""Orquestador multi-agente de GenPet (supervisor + investigador + analista + sintetizador).

Uso:
    python main.py                       # corre la consulta de demo (investigación -> análisis -> síntesis)
    python main.py "tu consulta"         # corre una consulta propia
    python main.py --traza demo          # nombre de la traza en traces/<nombre>.json y .log
    python main.py --diagrama            # exporta docs/graph.mmd y docs/graph.png y termina
"""
import argparse
import asyncio
import logging
import sys

from dotenv import load_dotenv

from config import DIAGRAMS_DIR, TRACES_DIR, get_llm_settings
from diagram import export_diagram
from graph import create_orchestrator
from runner import run_query
from tracing import TraceRecorder

DEMO_QUESTION = (
    "Necesito un informe de desempeño de GenPet en 2026: ¿cuáles fueron los ingresos netos de cada trimestre "
    "(Q1 a Q3) y cuáles eran las metas del plan comercial? Calculá el crecimiento porcentual entre trimestres, "
    "el porcentaje de cumplimiento de cada meta y cuánto falta facturar en el Q4 para llegar al objetivo anual "
    "de ingresos. Si GenPet cumple exactamente la meta del Q4, ¿alcanza el objetivo anual?"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Orquestador multi-agente de análisis e investigación")
    parser.add_argument("consulta", nargs="?", default=DEMO_QUESTION, help="Consulta (default: consulta de demo)")
    parser.add_argument("--traza", default="ultima", help="Nombre de la traza en traces/ (default: 'ultima')")
    parser.add_argument("--diagrama", action="store_true", help="Exporta el diagrama del grafo y termina")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    settings = get_llm_settings()
    graph = create_orchestrator(settings)

    if args.diagrama:
        for path in export_diagram(graph, DIAGRAMS_DIR):
            print(f"Diagrama exportado: {path}")
        return

    recorder = TraceRecorder(echo=print, llm=settings.label)
    try:
        await run_query(graph, args.consulta, recorder)
    except Exception as exc:  # noqa: BLE001 - error de API/red: se informa sin traceback y se guarda la traza
        recorder.finish("", error=f"Error del proveedor LLM ({settings.label}): {exc}")
        raise SystemExit(1) from exc
    finally:
        recorder.save(TRACES_DIR / f"{args.traza}.json", TRACES_DIR / f"{args.traza}.log")
        print(f"\nTraza guardada en {TRACES_DIR / args.traza}.json / .log")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    load_dotenv()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    asyncio.run(main())
