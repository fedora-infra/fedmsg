from fedmsg.text.base import BaseProcessor

class WikiProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return 'wiki.article.edit' in msg['topic']

    def subtitle(self, msg, **config):
        if 'wiki.article.edit' in msg['topic']:
            user = msg['msg']['user']
            title = msg['msg']['title']
            tmpl = '{user} made a wiki edit to "{title}"'
            return tmpl.format(user=user, title=title)
        else:
            raise NotImplementedError
