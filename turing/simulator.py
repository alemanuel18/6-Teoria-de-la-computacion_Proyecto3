"""Ejecución de una máquina sobre una cinta dispersa."""
from __future__ import annotations

from typing import Callable

from .models import Configuration, Machine, Result


def simulate(machine: Machine, value: str, *, max_steps: int = 100_000,
             on_configuration: Callable[[Configuration], None] | None = None) -> Result:
    if max_steps < 0:
        raise ValueError('max_steps debe ser no negativo')
    if any(char not in machine.alphabet for char in value):
        raise ValueError('la entrada contiene símbolos fuera de alphabet')
    tape = {i: char for i, char in enumerate(value)}
    state, cache, head, steps = machine.initial, None, 0, 0
    while True:
        terminal = state == machine.final
        transition = None if terminal else machine.transitions.get((state, cache, tape.get(head)))
        stopped = terminal or transition is None or steps >= max_steps
        configuration = Configuration(steps, state, cache, head, tape.copy()) if stopped or on_configuration else None
        if on_configuration is not None:
            on_configuration(configuration)
        if terminal:
            return Result(True, 'estado final', steps, configuration)
        if transition is None:
            return Result(False, 'sin transición aplicable', steps, configuration)
        if steps >= max_steps:
            return Result(False, 'límite de pasos alcanzado', steps, configuration)
        if transition.write is None:
            tape.pop(head, None)
        else:
            tape[head] = transition.write
        state, cache, head = transition.next_state, transition.next_cache, head + transition.move
        steps += 1
