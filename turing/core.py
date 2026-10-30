"""Parser, validación y ejecución de máquinas deterministas de una cinta."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml


class ConfigurationError(ValueError):
    """La descripción YAML no define una máquina válida."""


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


def _mapping(value: object, path: str) -> dict:
    if not isinstance(value, dict):
        raise ConfigurationError(f'{path}: se espera un objeto')
    return value


def _list(value: object, path: str) -> list:
    if not isinstance(value, list):
        raise ConfigurationError(f'{path}: se espera una lista')
    return value


def _state(value: object, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigurationError(f'{path}: se espera un estado de texto no vacío')
    return value


def _symbol(value: object, path: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) != 1:
        raise ConfigurationError(f'{path}: se espera un símbolo de un carácter o null')
    return value


def parse_machine(data: object) -> Machine:
    root = _mapping(data, 'raíz')
    states_data = _mapping(root.get('q_states'), 'q_states')
    state_list = [_state(s, 'q_states.q_list') for s in _list(states_data.get('q_list'), 'q_states.q_list')]
    if not state_list or len(set(state_list)) != len(state_list):
        raise ConfigurationError('q_states.q_list: debe contener estados únicos')
    states = frozenset(state_list)
    initial = _state(states_data.get('initial'), 'q_states.initial')
    final = _state(states_data.get('final'), 'q_states.final')
    if initial not in states or final not in states:
        raise ConfigurationError('los estados initial y final deben estar en q_list')
    input_list = [_symbol(s, 'alphabet') for s in _list(root.get('alphabet'), 'alphabet')]
    tape_list = [_symbol(s, 'tape_alphabet') for s in _list(root.get('tape_alphabet'), 'tape_alphabet')]
    if None in input_list or not input_list or len(set(input_list)) != len(input_list):
        raise ConfigurationError('alphabet: símbolos únicos, sin blank')
    if None not in tape_list or len(set(tape_list)) != len(tape_list):
        raise ConfigurationError('tape_alphabet: símbolos únicos y exactamente un blank (null)')
    alphabet = frozenset(input_list)
    tape_alphabet = frozenset(tape_list)
    if not alphabet <= tape_alphabet:
        raise ConfigurationError('tape_alphabet debe contener alphabet')
    transitions = {}
    for i, item in enumerate(_list(root.get('delta'), 'delta')):
        row = _mapping(item, f'delta[{i}]')
        params = _mapping(row.get('params'), f'delta[{i}].params')
        output = _mapping(row.get('output'), f'delta[{i}].output')
        state = _state(params.get('initial_state'), f'delta[{i}].params.initial_state')
        cache = _symbol(params.get('mem_cache_value'), f'delta[{i}].params.mem_cache_value')
        read = _symbol(params.get('tape_input'), f'delta[{i}].params.tape_input')
        next_state = _state(output.get('final_state'), f'delta[{i}].output.final_state')
        next_cache = _symbol(output.get('mem_cache_value'), f'delta[{i}].output.mem_cache_value')
        write = _symbol(output.get('tape_output'), f'delta[{i}].output.tape_output')
        direction = output.get('tape_displacement')
        if state not in states or next_state not in states:
            raise ConfigurationError(f'delta[{i}]: estado no declarado')
        if cache not in tape_alphabet or next_cache not in tape_alphabet or read not in tape_alphabet or write not in tape_alphabet:
            raise ConfigurationError(f'delta[{i}]: símbolo no declarado en tape_alphabet')
        if direction not in ('L', 'R', 'S'):
            raise ConfigurationError(f'delta[{i}]: tape_displacement debe ser L, R o S')
        if state == final:
            raise ConfigurationError(f'delta[{i}]: el estado final es terminal')
        key = (state, cache, read)
        if key in transitions:
            raise ConfigurationError(f'delta[{i}]: transición duplicada para {key}')
        transitions[key] = Transition(state, cache, read, next_state, next_cache, write, {'L': -1, 'R': 1, 'S': 0}[direction])
    inputs = []
    for i, value in enumerate(_list(root.get('simulation_strings'), 'simulation_strings')):
        if not isinstance(value, str):
            raise ConfigurationError(f'simulation_strings[{i}]: se espera texto (use "" para vacío)')
        if any(char not in alphabet for char in value):
            raise ConfigurationError(f'simulation_strings[{i}]: símbolo fuera de alphabet')
        inputs.append(value)
    return Machine(states, initial, final, alphabet, tape_alphabet, transitions, tuple(inputs))


def load_machine(path: str | Path) -> Machine:
    try:
        with open(path, encoding='utf-8') as stream:
            return parse_machine(yaml.safe_load(stream))
    except yaml.YAMLError as exc:
        raise ConfigurationError(f'YAML inválido: {exc}') from exc


def simulate(machine: Machine, value: str, *, max_steps: int = 100_000,
             on_configuration: Callable[[Configuration], None] | None = None) -> Result:
    if max_steps < 0:
        raise ValueError('max_steps debe ser no negativo')
    if any(char not in machine.alphabet for char in value):
        raise ValueError('la entrada contiene símbolos fuera de alphabet')
    tape = {i: char for i, char in enumerate(value)}
    state, cache, head, steps = machine.initial, None, 0, 0
    while True:
        configuration = Configuration(steps, state, cache, head, tape.copy())
        if on_configuration is not None:
            on_configuration(configuration)
        if state == machine.final:
            return Result(True, 'estado final', steps, configuration)
        transition = machine.transitions.get((state, cache, tape.get(head)))
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
