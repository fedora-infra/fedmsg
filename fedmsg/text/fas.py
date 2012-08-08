from fedmsg.text.base import BaseProcessor

class FASProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return any([target in msg['topic'] for target in [
            'fas.user.create',
            'fas.user.update',
            'fas.group.member.',
            'fas.group.create',
            'fas.group.update',
            'fas.role.update',
        ]])

    def subtitle(self, msg, **config):
        if 'fas.user.create' in msg['topic']:
            agent = msg['msg']['agent']['username']
            user = msg['msg']['user']['username']
            tmpl = self._(
                "New FAS account:  '{user}'  (created by '{agent}')"
            )
            return tmpl.format(agent=agent, user=user)
        elif 'fas.user.update' in msg['topic']:
            agent = msg['msg']['agent']['username']
            user = msg['msg']['user']['username']
            fields = ", ".join(msg['msg']['fields'])
            tmpl = self._(
                "{agent} edited the following fields of " +
                "{user}'s FAS profile:  {fields}"
            )
            return tmpl.format(agent=agent, user=user, fields=fields)
        elif 'fas.group.member.' in msg['topic']:
            action = msg['topic'].split('.')[-1]
            agent = msg['msg']['agent']['username']
            user = msg['msg']['user']['username']
            group = msg['msg']['group']['name']
            tmpls = {
                'apply': self._(
                    "{agent} applied for {user}'s membership " +
                    "in the {group} group"
                ),
                'sponsor': self._(
                    "{agent} sponsored {user}'s membership " +
                    "in the {group} group"
                ),
                'remove': self._(
                    "{agent} removed {user} from " +
                    "the {group} group"
                ),
            }
            tmpl = tmpls.get(action, self._(
                '<unhandled action in fedmsg.text.fas>'
            ))
            return tmpl.format(agent=agent, user=user, group=group)
        elif 'fas.group.create' in msg['topic']:
            agent = msg['msg']['agent']['username']
            group = msg['msg']['group']['name']
            tmpl = self._("{agent} created new FAS group {group}")
            return tmpl.format(agent=agent, group=group)
        elif 'fas.group.update' in msg['topic']:
            agent = msg['msg']['agent']['username']
            group = msg['msg']['group']['name']
            fields = ", ".join(msg['msg']['fields'])
            tmpl = self._(
                "{agent} edited the following fields of the {group} " + \
                "FAS group:  {fields}"
            )
            return tmpl.format(agent=agent, group=group, fields=fields)
        elif 'fas.role.update' in msg['topic']:
            agent = msg['msg']['agent']['username']
            user = msg['msg']['user']['username']
            group = msg['msg']['group']['name']
            tmpl = self._(
                "{agent} changed {user}'s role in the {group} group"
            )
            return tmpl.format(agent=agent, group=group, user=user)
        else:
            raise NotImplementedError
