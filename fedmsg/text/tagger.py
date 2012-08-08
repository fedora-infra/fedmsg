from fedmsg.text.base import BaseProcessor

class TaggerProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return any([
            target in msg['topic'] for target in [
                'fedoratagger.tag.update',
                'fedoratagger.tag.create',
                'fedoratagger.login.tagger',
            ]
        ])

    def subtitle(self, msg, **config):
        if 'fedoratagger.tag.update' in msg['topic']:
            user = msg['msg']['user']['username']
            tag = msg['msg']['tag']['tag']
            tmpl = self._("{user} voted on the package tag '{tag}'")
            return tmpl.format(user=user, tag=tag)
        elif 'fedoratagger.tag.create' in msg['topic']:
            tag = msg['msg']['tag']['tag']
            tmpl = self._('Added new tag "{tag}"')
            return tmpl.format(tag=tag)
        elif 'fedoratagger.login.tagger' in msg['topic']:
            user = msg['msg']['user']['username']
            tmpl = self._("{user} logged in to fedoratagger")
            return tmpl.format(user=user)
        else:
            raise NotImplementedError
