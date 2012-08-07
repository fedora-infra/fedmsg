from fedmsg.text.base import BaseProcessor

class BodhiProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return 'bodhi.update.comment' in msg['topic']

    def subtitle(self, msg, **config):
        if 'bodhi.update.comment' in msg['topic']:
            author = msg['msg']['comment']['author']
            karma = msg['msg']['comment']['karma']
            tmpl = "{author} commented on a bodhi update (karma: {karma})"
            return tmpl.format(author=author, karma=karma)
        else:
            raise NotImplementedError
