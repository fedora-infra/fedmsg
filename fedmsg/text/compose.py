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


class ComposeProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        result = any([target in msg['topic'] for target in [
            'compose.rawhide.start',
            'compose.rawhide.complete',
            'compose.rawhide.mash.start',
            'compose.rawhide.mash.complete',
            'compose.rawhide.rsync.start',
            'compose.rawhide.rsync.complete',
            'compose.branched.start',
            'compose.branched.complete',
            'compose.branched.mash.start',
            'compose.branched.mash.complete',
            'compose.branched.rsync.start',
            'compose.branched.rsync.complete',
            'compose.branched.pungify.start',
            'compose.branched.pungify.complete',
        ]])
        return result

    def handle_link(self, msg, **config):
        result = any([target in msg['topic'] for target in [
            'compose.rawhide.complete',
            'compose.rawhide.rsync.complete',
            'compose.branched.complete',
            'compose.branched.rsync.complete',
        ]])
        return result

    def subtitle(self, msg, **config):
        branch = msg['topic'].split('.')[4]

        if msg['topic'].endswith('.rsync.start'):
            tmpl = self._(
                "started rsyncing {branch} compose for public consumption")
        elif msg['topic'].endswith('.rsync.complete'):
            tmpl = self._(
                "finished rsync of {branch} compose for public consumption")
        elif msg['topic'].endswith('.mash.start'):
            tmpl = self._(
                "{branch} compose started mashing")
        elif msg['topic'].endswith('.mash.complete'):
            tmpl = self._(
                "{branch} compose finished mashing")
        elif msg['topic'].endswith('.pungify.start'):
            tmpl = self._(
                "started building boot.iso for {branch}")
        elif msg['topic'].endswith('.pungify.complete'):
            tmpl = self._(
                "finished building boot.iso for {branch}")
        elif msg['topic'].endswith('.start'):
            tmpl = self._("{branch} compose started")
        elif msg['topic'].endswith('.complete'):
            tmpl = self._("{branch} compose completed")
        else:
            raise NotImplementedError

        return tmpl.format(branch=branch)

    def link(self, msg, **config):
        base = "http://alt.fedoraproject.org/pub/fedora/linux/development"
        if 'rawhide' in msg['topic']:
            return base + "/rawhide"
        else:
            # For branched.  I'd rather not hardcode the branch name (f18)
            # here -- if we can help it -- so that we don't have to update this
            # code every time we do a new mass branch.
            return base
