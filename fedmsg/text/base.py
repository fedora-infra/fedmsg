class BaseProcessor(object):
    """ Base Processor... can't handle anything.

    Override handle_{title,subtitle} to use.
    """

    def __init__(self, internationalization_callable):
        self._ = internationalization_callable

    def handle_title(self, msg, **config):
        return False

    def handle_subtitle(self, msg, **config):
        return False

    def handle_link(self, msg, **config):
        return False
