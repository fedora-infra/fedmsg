from fedmsg.text.base import BaseProcessor

class DefaultProcessor(BaseProcessor):
    def handle_title(self, msg, **config):
        return True

    def handle_subtitle(self, msg, **config):
        return True

    def title(self, msg, **config):
        return '.'.join(msg['topic'].split('.')[3:])

    def subtitle(self, msg, **config):
        return ""
