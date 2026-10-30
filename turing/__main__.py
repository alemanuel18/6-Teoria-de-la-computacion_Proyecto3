"""Interfaz de consola: python -m turing archivo.yaml."""
import argparse
import sys

from .core import ConfigurationError, load_machine, simulate


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Simula una MT de una cinta desde YAML')
    parser.add_argument('yaml', help='archivo con máquina y entradas')
    parser.add_argument('--max-steps', type=int, default=100_000, help='límite por entrada (100000)')
    parser.add_argument('--no-trace', action='store_true', help='omite las IDs (útil para carga)')
    args = parser.parse_args(argv)
    try:
        machine = load_machine(args.yaml)
        if args.max_steps < 0:
            parser.error('--max-steps debe ser no negativo')
        for value in machine.inputs:
            print(f'Entrada: {value!r}')
            callback = None if args.no_trace else lambda c: print(f'{c.step}: {c.render()}')
            result = simulate(machine, value, max_steps=args.max_steps, on_configuration=callback)
            print(f'Resultado: {"ACEPTADA" if result.accepted else "RECHAZADA"} ({result.reason}; {result.steps} pasos)')
        return 0
    except (ConfigurationError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
