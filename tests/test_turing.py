import copy
import itertools
import tempfile
import unittest
from pathlib import Path

from turing.core import ConfigurationError, load_machine, parse_machine, simulate


ROOT = Path(__file__).resolve().parents[1]


class ExamplesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recognizer = load_machine(ROOT / 'examples/reconocedora.yaml')
        cls.transformer = load_machine(ROOT / 'examples/alteradora.yaml')

    def test_recognizer_exhaustive(self):
        for length in range(9):
            for chars in itertools.product('ab', repeat=length):
                word = ''.join(chars)
                with self.subTest(word=word):
                    expected = any(word == 'a' * n + 'b' * n for n in range(1, 5))
                    self.assertEqual(simulate(self.recognizer, word).accepted, expected)

    def test_transformer_exhaustive(self):
        for length in range(9):
            for chars in itertools.product('01', repeat=length):
                word = ''.join(chars)
                with self.subTest(word=word):
                    result = simulate(self.transformer, word)
                    self.assertEqual(result.accepted, bool(word))
                    self.assertEqual(''.join(result.configuration.tape.get(i, '') for i in range(length)), word.translate(str.maketrans('01', '10')))

    def test_trace_and_limit(self):
        ids = []
        result = simulate(self.recognizer, 'aabb', on_configuration=ids.append)
        self.assertEqual(len(ids), result.steps + 1)
        self.assertIn('[buscar_a|□]aabb', ids[0].render())
        self.assertEqual(ids[-1].state, 'aceptar')
        limited = simulate(self.recognizer, 'aabb', max_steps=2)
        self.assertEqual(limited.reason, 'límite de pasos alcanzado')
        self.assertEqual(limited.steps, 2)

    def test_invalid_direct_input(self):
        with self.assertRaises(ValueError):
            simulate(self.transformer, 'x')
        with self.assertRaises(ValueError):
            simulate(self.transformer, '0', max_steps=-1)


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.base = {
            'q_states': {'q_list': ['q0', 'qf'], 'initial': 'q0', 'final': 'qf'},
            'alphabet': ['a'], 'tape_alphabet': ['a', 'X', None],
            'delta': [], 'simulation_strings': ['a', ''],
        }

    def test_memory_left_blank_and_stay(self):
        data = copy.deepcopy(self.base)
        data['delta'] = [
            {'params': {'initial_state': 'q0', 'mem_cache_value': None, 'tape_input': 'a'},
             'output': {'final_state': 'q0', 'mem_cache_value': 'X', 'tape_output': None, 'tape_displacement': 'L'}},
            {'params': {'initial_state': 'q0', 'mem_cache_value': 'X', 'tape_input': None},
             'output': {'final_state': 'qf', 'mem_cache_value': 'X', 'tape_output': 'a', 'tape_displacement': 'S'}},
        ]
        result = simulate(parse_machine(data), 'a')
        self.assertTrue(result.accepted)
        self.assertEqual(result.configuration.head, -1)
        self.assertEqual(result.configuration.tape, {-1: 'a'})
        self.assertIn('[qf|X]a', result.configuration.render())

    def test_reject_bad_descriptions(self):
        variants = []
        for key, value in [('alphabet', ['a', 'a']), ('tape_alphabet', ['a']), ('simulation_strings', ['b'])]:
            data = copy.deepcopy(self.base)
            data[key] = value
            variants.append(data)
        data = copy.deepcopy(self.base)
        data['q_states']['final'] = 'missing'
        variants.append(data)
        data = copy.deepcopy(self.base)
        data['delta'] = [{'params': {'initial_state': 'q0', 'tape_input': 'a'},
                          'output': {'final_state': 'qf', 'tape_output': 'a', 'tape_displacement': 'R'}}] * 2
        variants.append(data)
        data = copy.deepcopy(self.base)
        data['delta'] = [{'params': {'initial_state': 'q0', 'tape_input': 'a'},
                          'output': {'final_state': 'qf', 'tape_output': 'a', 'tape_displacement': 'X'}}]
        variants.append(data)
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(ConfigurationError):
                parse_machine(variant)

    def test_yaml_syntax_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.yaml'
            path.write_text('q_states: [unterminated', encoding='utf-8')
            with self.assertRaises(ConfigurationError):
                load_machine(path)


if __name__ == '__main__':
    unittest.main()
