from fedmsg.text.base import BaseProcessor

class TaggerProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return 'fedoratagger.tag.update' in msg['topic']

    def subtitle(self, msg, **config):
        if 'fedoratagger.tag.update' in msg['topic']:
            user = msg['msg']['user']['username']
            tag = msg['msg']['tag']['tag']
            tmpl = "{user} voted on the package tag '{tag}'"
            return tmpl.format(user=user, tag=tag)
        else:
            raise NotImplementedError
