import urllib
from hashlib import md5

_valid_gravatar_sizes = (32, 64, 140)


def gravatar_url(username, size=64, default=None):
    try:
        import fedora.client
        system = fedora.client.AccountSystem()
        return system.gravatar_url(
            username, size, default, lookup_email=False)
    except Exception:
        return _gravatar_url(username, size, default)


def _gravatar_url(username, size=64, default=None):
    """
    Our own implementation since fas doesn't support this nicely yet.
    """

    if size not in _valid_gravatar_sizes:
        raise ValueError(b_('Size %(size)i disallowed.  Must be in'
            ' %(valid_sizes)r') % { 'size': size,
                'valid_sizes': _valid_gravatar_sizes})

    if not default:
        default = "http://fedoraproject.org/static/images/" + \
                "fedora_infinity_%ix%i.png" % (size, size)

    query_string = urllib.urlencode({
        's': size,
        'd': default,
    })

    email = "%s@fedoraproject.org" % username
    hash = md5(email).hexdigest()

    return "http://www.gravatar.com/avatar/%s?%s" % (hash, query_string)
