from fedmsg.text.base import BaseProcessor

class FASProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return any([target in msg['topic'] for target in [
            'fas.user.update',
            'fas.group.member.apply',
        ]])

    def subtitle(self, msg, **config):
        if 'fas.user.update' in msg['topic']:
            agent = msg['msg']['agent']['username']
            user = msg['msg']['user']['username']
            fields = ", ".join(msg['msg']['fields'])
            tmpl = self._(
                "{agent} edited the following fields of " +
                "{user}'s FAS profile:  {fields}"
            )
            return tmpl.format(agent=agent, user=user, fields=fields)
        elif 'fas.group.member.apply' in msg['topic']:
            agent = msg['msg']['agent']['username']
            user = msg['msg']['user']['username']
            group = msg['msg']['group']['name']
            tmpl = self._(
                "{agent} applied for {user}'s membership " +
                "in the {group} group"
            )
            return tmpl.format(agent=agent, user=user, group=group)
        else:
            raise NotImplementedError
