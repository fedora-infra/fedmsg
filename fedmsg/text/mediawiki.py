from fedmsg.text.base import BaseProcessor

class WikiProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return any([
            target in msg['topic'] for target in [
                'wiki.article.edit',
                'wiki.upload.complete',
            ]
        ])

    def subtitle(self, msg, **config):
        if 'wiki.article.edit' in msg['topic']:
            user = msg['msg']['user']
            title = msg['msg']['title']
            tmpl = self._('{user} made a wiki edit to "{title}"')
            return tmpl.format(user=user, title=title)
        elif 'wiki.upload.complete' in msg['topic']:
            user = msg['msg']['user_text']
            filename = msg['msg']['title']['mPrefixedText']
            description = msg['msg']['description'][:35]
            tmpl = self._(
                '{user} uploaded {filename} to the wiki: "{description}..."'
            )
            return tmpl.format(user=user, filename=filename,
                               description=description)
        else:
            raise NotImplementedError
