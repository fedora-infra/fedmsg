from fedmsg.text.base import BaseProcessor

class BodhiProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return any([target in msg['topic'] for target in [
            'bodhi.update.comment',
            'bodhi.update.request',
            'bodhi.update.complete.',
            'bodhi.mashtask.mashing',
            'bodhi.mashtask.start',
            'bodhi.mashtask.complete',
            'bodhi.mashtask.sync.wait',
            'bodhi.mashtask.sync.done',
        ]])

    def subtitle(self, msg, **config):
        if 'bodhi.update.comment' in msg['topic']:
            author = msg['msg']['comment']['author']
            karma = msg['msg']['comment']['karma']
            tmpl = self._(
                "{author} commented on a bodhi update (karma: {karma})"
            )
            return tmpl.format(author=author, karma=karma)
        elif 'bodhi.update.complete.' in msg['topic']:
            author = msg['msg']['update']['submitter']
            package = msg['msg']['update']['title']
            status = msg['msg']['update']['status']
            tmpl = self._(
                "{author}'s {package} bodhi update completed push to {status}"
            )
            return tmpl.format(author=author, package=package, status=status)
        elif 'bodhi.update.request' in msg['topic']:
            action = msg['topic'].split('.')[-1]
            title = msg['msg']['update']['title']
            tmpl = self._("{title} requested {action}")
            return tmpl.format(action=action, title=title)
        elif 'bodhi.mashtask.mashing' in msg['topic']:
            repo = msg['msg']['repo']
            tmpl = self._("bodhi masher is mashing {repo}")
            return tmpl.format(repo=repo)
        elif 'bodhi.mashtask.start' in msg['topic']:
            return self._("bodhi masher started its mashtask")
        elif 'bodhi.mashtask.complete' in msg['topic']:
            success = msg['msg']['success']
            if success:
                return self._("bodhi masher successfully completed mashing")
            else:
                return self._("bodhi masher failed to complete its mashtask!")
        elif 'bodhi.mashtask.sync.wait' in msg['topic']:
            return self._("bodhi masher is waiting on mirror repos to sync")
        elif 'bodhi.mashtask.sync.done' in msg['topic']:
            return self._("bodhi masher finished waiting on mirror repos " + \
                          "to sync")
        else:
            raise NotImplementedError
