from nose.tools import raises, eq_
from fedmsg.utils import load_class


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
