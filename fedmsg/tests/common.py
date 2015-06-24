import os
import socket
import fedmsg.config

from nose.tools.nontrivial import make_decorator

try:
    import unittest2 as unittest
except ImportError:
    import unittest


def load_config(name='fedmsg-test-config.py'):
    here = os.path.sep.join(__file__.split(os.path.sep)[:-1])
    test_config = os.path.sep.join([here, name])

    config = fedmsg.config.load_config(
        [],
        "awesome",
        filenames=[
            test_config,
        ],
        invalidate_cache=True
    )

    # Enable all of our test consumers so they can do their thing.
    config['test_consumer_enabled'] = True

    # TODO -- this appears everywhere and should be encapsulated in a func
    # Massage the fedmsg config into the moksha config.
    config['zmq_subscribe_endpoints'] = ','.join(
        ','.join(bunch) for bunch in config['endpoints'].values()
    )
    hub_name = "twisted.%s" % socket.gethostname().split('.', 1)[0]
    config['zmq_publish_endpoints'] = ','.join(
        config['endpoints'][hub_name]
    )
    return config


def requires_network(function):
    """ Decorator to skip tests if FEDMSG_NETWORK is not in os.environ """
    @make_decorator(function)
    def decorated_function(*args, **kwargs):
        """ Decorated function, actually does the work. """
        if not os.environ.get('FEDMSG_NETWORK'):
            raise unittest.SkipTest("Skip test since we don't have network")
        return function(*args, **kwargs)
    return decorated_function
