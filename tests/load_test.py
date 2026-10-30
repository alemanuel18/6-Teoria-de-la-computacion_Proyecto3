"""Prueba de carga reproducible; ejecutar con python -m tests.load_test."""
from pathlib import Path
from time import perf_counter

from turing.core import load_machine, simulate

root = Path(__file__).resolve().parents[1]
transformer = load_machine(root / 'examples/alteradora.yaml')
recognizer = load_machine(root / 'examples/reconocedora.yaml')

for length in (10_000, 50_000, 100_000):
    word = '01' * (length // 2)
    start = perf_counter()
    result = simulate(transformer, word, max_steps=length + 1)
    seconds = perf_counter() - start
    assert result.accepted and result.steps == length + 1
    assert result.configuration.tape[0] == '1'
    assert result.configuration.tape[length - 1] == '0'
    print(f'alteradora: {length:,} símbolos, {result.steps:,} pasos, {seconds:.3f} s')

word = 'a' * 200 + 'b' * 200
start = perf_counter()
result = simulate(recognizer, word, max_steps=1_000_000)
seconds = perf_counter() - start
assert result.accepted
print(f'reconocedora: {len(word):,} símbolos, {result.steps:,} pasos, {seconds:.3f} s')
