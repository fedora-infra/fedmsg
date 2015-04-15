from nose.tools import raises, eq_
from fedmsg.utils import load_class, dict_query

try:
    import mock
except ImportError:
    from unittest import mock


def test_load_class_succeed():
    cls = load_class("shelve:Shelf")
    from shelve import Shelf
    eq_(cls, Shelf)


@raises(ImportError)
def test_load_class_import_error():
    cls = load_class("thisisnotapackage:ThisIsNotAClass")


@raises(ImportError)
def test_load_class_attribute_error():
    cls = load_class("shelve:ThisIsNotAClass")


def test_dict_query_basic():
    dct = {
        'foo': {
            'bar': {
                'baz': 'wat',
            }
        }
    }
    key = 'foo.bar.baz'
    result = dict_query(dct, key)
    eq_(result, {key: 'wat'})


def test_dict_query_miss():
    dct = {
        'foo': {
            'bar': {
                'baz': 'wat',
            }
        }
    }
    key = 'foo.bar.zomg'
    result = dict_query(dct, key)
    eq_(result, {key: None})


def test_dict_query_fancy_one():
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
    eq_(result, {key: {'baz': 'wat', 'zip': 'zoom'}})


def test_dict_query_fancy_two():
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
    eq_(result, {key1: {'baz': 'wat', 'zip': 'zoom'}})
    key2 = 'foo.har'
    result = dict_query(dct, key2)
    eq_(result, {key2: 'loktar ogar'})


@raises(ValueError)
def test_dict_query_weird_inputs():
    dct = {
        'foo': {
            'bar': {
                'baz': 'wat',
            },
        }
    }
    key = None
    result = dict_query(dct, key)
    eq_(result, {key: {'baz': 'wat', 'zip': 'zoom'}})
