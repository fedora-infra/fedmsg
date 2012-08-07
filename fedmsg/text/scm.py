from fedmsg.text.base import BaseProcessor

class SCMProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return '.git.receive' in msg['topic']

    def subtitle(self, msg, **config):
        if '.git.receive' in msg['topic']:
            repo = '.'.join(msg['topic'].split('.')[4:-1])
            user = msg['msg']['commits'][-1]['name']
            summ = msg['msg']['commits'][-1]['summary']
            tmpl = '{user} pushed to {repo}.  "{summary}"'
            return tmpl.format(user=user, repo=repo, summary=summ)
        else:
            raise NotImplementedError
