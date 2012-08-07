
# TODO - internationalization
_ = lambda s: s


def msg2repr(msg, **config):
    fmt = "%(title) -- %(subtitle)"
    suffix = _msg2suffix(msg, **config)
    if suffix:
        fmt = "%(title) %(suffix) -- %(subtitle)"

    title = _msg2title(msg, **config)
    subtitle = _msg2subtitle(msg, **config)

    return fmt.format(**locals())

def _msg2title(msg, **config)
    # TODO -- title
    title = msg['topic']
    return title

def _msg2subtitle(msg, **config)
    # TODO.. subtitle
    return "todo.. subtitle"


def _msg2suffix(msg, **config):
    if 'signature' not in msg:
        return _("(unsigned)")
    else:
        if not fedmsg.crypto.validate(msg, **config):
            return _("(invalid signature!)")

    return ""

