
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from fedmsg.utils import load_class, dict_query


class LoadClassTests(unittest.TestCase):

    def test_load_class_succeed(self):
        cls = load_class("shelve:Shelf")
        from shelve import Shelf
        self.assertEqual(cls, Shelf)

    def test_load_class_import_error(self):
        with self.assertRaises(ImportError):
            load_class("thisisnotapackage:ThisIsNotAClass")

    def test_load_class_attribute_error(self):
        with self.assertRaises(ImportError):
            load_class("shelve:ThisIsNotAClass")


class DictQueryTests(unittest.TestCase):

    def test_dict_query_basic(self):
        dct = {
            'foo': {
                'bar': {
                    'baz': 'wat',
                }
            }
        }
        key = 'foo.bar.baz'
        result = dict_query(dct, key)
        self.assertEqual(result, {key: 'wat'})

    def test_dict_query_miss(self):
        dct = {
            'foo': {
                'bar': {
                    'baz': 'wat',
                }
            }
        }
        key = 'foo.bar.zomg'
        result = dict_query(dct, key)
        self.assertEqual(result, {key: None})

    def test_dict_query_fancy_one(self):
        dct = {
            'foo': {
                'bar': {
                    'zip': 'zoom',
                    'baz': 'wat',
                }
            }
        }
        key = 'foo.bar'
        result = dict_query(dct, key)
        self.assertEqual(result, {key: {'baz': 'wat', 'zip': 'zoom'}})

    def test_dict_query_fancy_two(self):
        dct = {
            'foo': {
                'bar': {
                    'zip': 'zoom',
                    'baz': 'wat',
                },
                'har': 'loktar ogar',
            }
        }
        key1 = 'foo.bar'
        result = dict_query(dct, key1)
        self.assertEqual(result, {key1: {'baz': 'wat', 'zip': 'zoom'}})
        key2 = 'foo.har'
        result = dict_query(dct, key2)
        self.assertEqual(result, {key2: 'loktar ogar'})

    def test_dict_query_weird_inputs(self):
        dct = {
            'foo': {
                'bar': {
                    'baz': 'wat',
                },
            }
        }
        with self.assertRaises(ValueError):
            dict_query(dct, None)
