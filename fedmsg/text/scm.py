# This file is part of fedmsg.
# Copyright (C) 2012 Red Hat, Inc.
#
# fedmsg is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# fedmsg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with fedmsg; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Authors:  Ralph Bean <rbean@redhat.com>
#
from fedmsg.text.base import BaseProcessor


class SCMProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        result = any([target in msg['topic'] for target in [
            '.git.receive.',
            '.git.branch.',
            '.git.lookaside.',
            '.git.pkgdb2branch.start',
            '.git.pkgdb2branch.complete',
            '.git.mass_branch.start',
            '.git.mass_branch.complete',
        ]])
        return result

    def handle_link(self, msg, **config):
        result = any([target in msg['topic'] for target in [
            '.git.receive.',
            '.git.branch.',
            '.git.lookaside.',
        ]])
        return result

    def handle_icon(self, msg, **config):
        return True

    def icon(self, msg, **config):
        return "http://git-scm.com/images/logo.png"

    def subtitle(self, msg, **config):
        if '.git.receive.' in msg['topic']:
            repo = '.'.join(msg['topic'].split('.')[5:-1])
            user = msg['msg']['commit']['name']
            summ = msg['msg']['commit']['summary']
            branch = msg['msg']['commit']['branch']
            tmpl = self._('{user} pushed to {repo} ({branch}).  "{summary}"')
            return tmpl.format(user=user, repo=repo,
                               branch=branch, summary=summ)
        elif '.git.branch.' in msg['topic']:
            repo = '.'.join(msg['topic'].split('.')[5:-1])
            branch = msg['topic'].split('.')[-1]
            agent = msg['msg']['agent']
            tmpl = self._(
                "{agent} created branch '{branch}' for the '{repo}' package"
            )
            return tmpl.format(agent=agent, branch=branch, repo=repo)
        elif '.git.lookaside.' in msg['topic']:
            name = msg['msg']['name']
            agent = msg['msg']['agent']
            filename = msg['msg']['filename']
            tmpl = self._(
                "{agent} uploaded {filename} for {name}"
            )
            return tmpl.format(agent=agent, name=name, filename=filename)
        elif '.git.mass_branch.start' in msg['topic']:
            tmpl = self._('{agent} started a mass branch')
        elif '.git.mass_branch.complete' in msg['topic']:
            tmpl = self._('mass branch started by {agent} completed')
        elif '.git.pkgdb2branch.start' in msg['topic']:
            tmpl = self._('{agent} started a run of pkgdb2branch')
        elif '.git.pkgdb2branch.complete' in msg['topic']:
            errors = len(msg['msg']['unbranchedPackages'])
            if errors == 0:
                tmpl = self._(
                    'run of pkgdb2branch started by {agent} completed')
            elif errors == 1:
                tmpl = self._(
                    'run of pkgdb2branch started by {agent} completed' +
                    ' with 1 error'
                )
            else:
                tmpl = self._(
                    'run of pkgdb2branch started by {agent} completed' +
                    ' with %i errors'
                ) % errors
        else:
            raise NotImplementedError

        agent = msg['msg']['agent']
        return tmpl.format(agent=agent)

    def link(self, msg, **config):
        prefix = "http://pkgs.fedoraproject.org/cgit"
        if '.git.receive.' in msg['topic']:
            repo = '.'.join(msg['topic'].split('.')[5:-1])
            rev = msg['msg']['commit']['rev']
            branch = msg['msg']['commit']['branch']
            tmpl = "{prefix}/{repo}.git/commit/?h={branch}&id={rev}"
            return tmpl.format(prefix=prefix, repo=repo,
                               branch=branch, rev=rev)
        elif '.git.branch.' in msg['topic']:
            repo = '.'.join(msg['topic'].split('.')[5:-1])
            branch = msg['topic'].split('.')[-1]
            tmpl = "{prefix}/{repo}.git/log/?h={branch}"
            return tmpl.format(prefix=prefix, repo=repo, branch=branch)
        elif '.git.lookaside.' in msg['topic']:
            prefix = "http://pkgs.fedoraproject.org/lookaside/pkgs"
            name = msg['msg']['name']
            md5sum = msg['msg']['md5sum']
            filename = msg['msg']['filename']
            tmpl = "{prefix}/{name}/{filename}/{md5sum}/{filename}"
            return tmpl.format(prefix=prefix, name=name,
                               md5sum=md5sum, filename=filename)
        else:
            raise NotImplementedError
