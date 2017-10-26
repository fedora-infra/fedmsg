"""
This module defines the base class of message objects and keeps a registry of known
message implementations. This registry is populated from Python entry points. The registry
keys are message topics and the values are sub-classes of :class:`Message`.

Each topic can have one, and only one, class. If a message is received with a topic that is
not in the registry, the topic is split on the ``.`` character and that topic is used. The
base :class:`Message` maps to the empty topic, ``''``, and is used if there are no other
message classes.
"""

import collections
import json
import logging

import jsonschema
import pkg_resources

_log = logging.getLogger(__name__)


def get_class(topic):
    """
    Retrieve the message class for the given topic.

    If the topic is not a key in the message dictionary, the topic is split on the last
    ``.`` character in the topic and the prefix is used. This is repeated until a class
    is found or the topic is the empty string in which case the base :class:`Message` class
    is used.

    Args:
        topic (six.text_type): The message topic to map to a :class:`Message` class.

    Returns:
        Message: A sub-class of :class:`Message` to create the message from.
    """
    try:
        return _class_registry[topic]
    except KeyError:
        new_topic = topic.rsplit('.', 1)[0] if '.' in topic else u''
        return get_class(new_topic)


def load_message_classes():
    """Load the 'fedmsg.messages' entry points and register the message classes."""
    for message in pkg_resources.iter_entry_points('fedmsg.messages'):
        cls = message.load()
        _log.info("Registering topic '{}' to the '{}' class", message.name, cls)
        register(message.name, cls)


def register(topic, message_class):
    """
    Register a message class to a topic.

    Only one class can be mapped to a topic. If the topic already has a class registered with it,
    an exception will be raised.

    Exceptions:
        ValueError: Raised if two message classes are registered with the same topic.
    """
    if topic in _class_registry and _class_registry[topic] is not message_class:
        raise ValueError('Cannot register {}; the {} topic is already registered with the '
                         '{} class'.format(message_class, topic, _class_registry[topic]))
    _class_registry[topic] = message_class


class Message(collections.MutableMapping):
    """
    This class represents a fedmsg.

    When using fedmsg, it is a good idea to define a message schema. This allows
    message authors to define a schema and implement Python methods to abstract
    the raw message from the user. This allows the schema to change and evolve
    without breaking the user-facing API.

    Each message class has a one-to-one relationship with a message topic. In
    ZeroMQ, topics are simply binary data. In fedmsg, topics are restricted to
    UTF-8 encoded strings.

    .. warning:: for backwards-compatibility with the old fedmsg messages, which
        were plain dictionaries, this class implements the dictionary interface.
        These methods are marked as deprecated and should not be used. Instead, use
        the Python interface defined by the message authors.

    Attributes:
        topic (six.text_type): The message topic as a unicode string.
        headers_schema (dict): A `JSON schema <http://json-schema.org/>`_ to be used with
            :func:`jsonschema.validate` to validate the message headers.
        body_schema (dict): A `JSON schema <http://json-schema.org/>`_ to be used with
            :func:`jsonschema.validate` to validate the message headers.

    Args:
        headers (dict): A set of message headers. Consult the headers schema for
            expected keys and values.
        body (dict): The message body. Consult the body schema for expected keys
            and values.
    """

    topic = u''
    headers_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'description': 'Schema for fedmsg headers',
        'type': 'object',
    }
    body_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'description': 'Schema for a fedmsg body',
        'type': 'object',
    }

    def __init__(self, headers=None, body=None):
        self.headers = headers or {}
        self.body = body or {}
        self.validate()

    def __str__(self):
        """
        A human-readable representation of this message.

        This should provide a detailed representation of the message, much like the body
        of an email.

        The default implementation is to format the raw message topic, headers, and body.
        Applications use this to present messages to users.
        """
        # TODO all error handling here - json errors, unicode problems, etc.
        return 'Topic: {t} \n\nHeaders: {h}\n\nBody: {b}'.format(
            t=self.topic,
            h=json.dumps(self.headers, sort_keys=True, indent=4),
            b=json.dumps(self.headers, sort_keys=True, indent=4)
        )

    def summary(self):
        """
        A short, human-readable representation of this message.

        This should provide a short summary of the message, much like the subject line
        of an email.

        The default implementation is to simply return the message topic.
        """
        return self.topic

    def validate(self):
        """
        Validate the headers and body with the message schema, if any.

        Raises:
            jsonschema.ValidationError: If either the message headers or the message body
                are invalid.
            jsonschema.SchemaError: If either the message header schema or the message body
                schema are invalid.
        """
        if self.headers_schema is not None:
            jsonschema.validate(self.headers, self.headers_schema)
        if self.body_schema is not None:
            jsonschema.validate(self.body, self.body_schema)

    def __getitem__(self, key):
        return self.body.__getitem__(key)

    def __setitem__(self, key, value):
        return self.body.__setitem__(key, value)

    def __delitem__(self, key):
        return self.body.__delitem__(key)

    def __iter__(self):
        return self.body.__iter__()

    def __len__(self):
        return self.body.__len__()

    def __contains__(self, value):
        return self.body.__contains__()

    def keys(self):
        return self.body.keys()

    def items(self):
        return self.body.items()

    def values(self):
        return self.body.values()

    def get(self, key, default=None):
        return self.body.get(key, default=default)

    def __eq__(self, other):
        return self.body.__eq__(other)

    def __ne__(self, other):
        return self.body.__ne__(other)

    def pop(self, key):
        return self.body.pop(key)

    def popitem(self):
        return self.body.popitem()

    def clear(self):
        return self.body.clear()

    def update(self):
        return self.body.update()

    def setdefault(self):
        return self.body.setdefault()


_class_registry = {
    u'': Message,
}
