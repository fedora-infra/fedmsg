from fedmsg.text.base import BaseProcessor

class SCMProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return '.git.receive.' in msg['topic']

    def subtitle(self, msg, **config):
        if '.git.receive.' in msg['topic']:
            repo = '.'.join(msg['topic'].split('.')[5:-1])
            user = msg['msg']['commit']['name']
            summ = msg['msg']['commit']['summary']
            branch = msg['msg']['commit']['branch']
            tmpl = self._('{user} pushed to {repo} ({branch}).  "{summary}"')
            return tmpl.format(user=user, repo=repo,
                               branch=branch, summary=summ)
        else:
            raise NotImplementedError
