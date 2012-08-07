from fedmsg.text.base import BaseProcessor

class BodhiProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return any([target in msg['topic'] for target in [
            'bodhi.update.comment',
            'bodhi.update.request',
        ]])

    def subtitle(self, msg, **config):
        if 'bodhi.update.comment' in msg['topic']:
            author = msg['msg']['comment']['author']
            karma = msg['msg']['comment']['karma']
            tmpl = "{author} commented on a bodhi update (karma: {karma})"
            return tmpl.format(author=author, karma=karma)
        elif 'bodhi.update.request' in msg['topic']:
            action = msg['topic'].split('.')[-1]
            title = msg['msg']['update']['title']
            tmpl = "{title} requested {action}"
            return tmpl.format(action=action, title=title)
        else:
            raise NotImplementedError
