from __future__ import annotations

from dataclasses import dataclass


def log_progress(scope: str, message: str) -> None:
    print(f"[{scope}] {message}", flush=True)


@dataclass(frozen=True)
class StepProgress:
    scope: str
    current: int
    total: int
    label: str

    def render(self) -> str:
        width = len(str(self.total))
        return f"[{self.current:>{width}}/{self.total}] {self.label}"


def log_step(scope: str, current: int, total: int, label: str) -> None:
    log_progress(scope, StepProgress(scope=scope, current=current, total=total, label=label).render())
