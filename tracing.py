"""Traza del flujo de delegación: convierte los updates del grafo en líneas legibles y en un JSON estructurado."""
import json
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from state import SUPERVISOR, SYNTHESIZER

MAX_CHARS = 600


def _shorten(texto: str, limite: int = MAX_CHARS) -> str:
    texto = " ".join(texto.split())
    return texto if len(texto) <= limite else texto[:limite] + "…"


def _format_args(args: dict) -> str:
    return ", ".join(f"{k}={v!r}" for k, v in args.items())


class TraceRecorder:
    """Registra cada paso del grafo (quién actuó, qué decidió o aportó) y opcionalmente lo imprime en vivo."""

    def __init__(self, echo: Optional[Callable[[str], None]] = print, llm: Optional[str] = None):
        self._echo = echo
        self.lines: List[str] = []
        self.events: List[dict] = []
        self.meta: dict = {"llm": llm}

    def _log(self, line: str) -> None:
        self.lines.append(line)
        if self._echo:
            self._echo(line)

    def start(self, question: str) -> None:
        self.meta.update(inicio=datetime.now().isoformat(timespec="seconds"), consulta=question)
        self._log(f'Consulta: "{question}"')

    def on_update(self, node: str, update: dict) -> None:
        paso = len(self.events) + 1
        if node == SUPERVISOR:
            decision = update["decisions"][-1]
            forzada = " [GUARDA]" if decision["forced"] else ""
            self._log(f"\n[{paso}] supervisor -> {decision['next']}{forzada}")
            self._log(f"    razonamiento: {_shorten(decision['reasoning'])}")
            if decision["instruction"]:
                self._log(f"    instrucción: {_shorten(decision['instruction'])}")
            self.events.append({"paso": paso, "nodo": node, **decision})
        elif node == SYNTHESIZER:
            self._log(f"\n[{paso}] sintetizador -> END")
            self.events.append({"paso": paso, "nodo": node, "respuesta": update["final_answer"]})
        else:
            aporte = update["contributions"][-1]
            self._log(f"\n[{paso}] {node} (intento {aporte['attempt']}) · {len(aporte['tool_calls'])} tool calls")
            for call in aporte["tool_calls"]:
                self._log(f"    · {call['tool']}({_format_args(call['args'])})")
            if aporte["issues"]:
                self._log(f"    VALIDACIÓN FALLIDA: {' '.join(aporte['issues'])}")
            self._log(f"    aporte: {_shorten(aporte['content'])}")
            self.events.append({"paso": paso, "nodo": node, **aporte})

    def finish(self, answer: str, error: Optional[str] = None) -> None:
        self.meta.update(fin=datetime.now().isoformat(timespec="seconds"), respuesta=answer, error=error)
        self._log("\n" + "=" * 80 + "\nRESPUESTA FINAL\n" + "=" * 80)
        self._log(error or answer)

    def save(self, json_path: Path, log_path: Path) -> None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps({**self.meta, "pasos": self.events}, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        log_path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
