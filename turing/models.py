"""Estructuras de la máquina y representación de una ID."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Transition:
    state: str
    cache: str | None
    read: str | None
    next_state: str
    next_cache: str | None
    write: str | None
    move: int


@dataclass(frozen=True)
class Machine:
    states: frozenset[str]
    initial: str
    final: str
    alphabet: frozenset[str]
    tape_alphabet: frozenset[str]
    transitions: dict[tuple[str, str | None, str | None], Transition]
    inputs: tuple[str, ...]


@dataclass(frozen=True)
class Configuration:
    step: int
    state: str
    cache: str | None
    head: int
    tape: dict[int, str]

    def render(self) -> str:
        """ID: contenido a la izquierda, estado/memoria, celda leída y derecha."""
        positions = set(self.tape) | {self.head}
        lo, hi = min(positions), max(positions)

        def cell(pos: int) -> str:
            return self.tape.get(pos, '□')

        left = ''.join(cell(i) for i in range(lo, self.head))
        right = ''.join(cell(i) for i in range(self.head + 1, hi + 1))
        memory = self.cache if self.cache is not None else '□'
        return f'{left}[{self.state}|{memory}]{cell(self.head)}{right}'


@dataclass(frozen=True)
class Result:
    accepted: bool
    reason: str
    steps: int
    configuration: Configuration


