"""API pública estable para usar el simulador desde Python."""

from .models import Configuration, Machine, Result, Transition
from .parser import ConfigurationError, load_machine, parse_machine
from .simulator import simulate

__all__ = [
    "Configuration", "ConfigurationError", "Machine", "Result",
    "Transition", "load_machine", "parse_machine", "simulate",
]
