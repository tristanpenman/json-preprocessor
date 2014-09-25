import json
import unittest

from json_preprocessor import resolve


test_cases = [
    ('data/001_ref_no_pointer.json', 'data/001_ref_no_pointer_expected.json'),
    ('data/005_ref_rel_with_arg.json', 'data/005_ref_rel_with_arg_expected.json'),
    ('data/010_join.json', 'data/010_join_expected.json'),
    ('data/020_exec.json', 'data/020_exec_expected.json'),
    ('data/030_merge.json', 'data/030_merge_expected.json')
]


class TestResolution(unittest.TestCase):
    def test(self):
        for test_case in test_cases:
            with open(test_case[0]) as data:
                actual = resolve(json.load(data), dict())
                with open(test_case[1]) as expected:
                    self.assertEqual(json.load(expected), actual)

if __name__ == '__main__':
    unittest.main()
