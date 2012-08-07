from fedmsg.text.base import BaseProcessor

class LoggerProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return 'logger.log' in msg['topic']

    def subtitle(self, msg, **config):
        if 'logger.log' in msg['topic']:
            if 'log' in msg['msg']:
                return msg['msg']['log']
            else:
                return "<custom JSON message>"
        else:
            raise NotImplementedError
