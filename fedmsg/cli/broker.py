# This file is part of the fedmsg project
# Copyright (C) 2017 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""The Click command-line interface for the fedmsg broker."""
from __future__ import absolute_import

from gettext import gettext as _
import logging
import logging.config

import click

from fedmsg import config
from fedmsg.broker.service import BrokerService
from . import cli

_log = logging.getLogger(__name__)

_sub_help = _('The endpoint to use for message submission; defaults to the '
              'fedmsg "submission_endpoint" configuration setting')


@cli.command()
@click.option('--submission-endpoint', '-s', help=_sub_help)
def broker(submission_endpoint):
    """
    The fedmsg broker service.

    This service is responsible for accepting messages from applications and publishing
    them to the configured publication destinations.

    Note: This service is experimental and may change without a major release.
    """
    logging.config.dictConfig(config.conf['logging'])

    submission_endpoint = submission_endpoint or config.conf['submission_endpoint']

    broker_service = BrokerService(submission_endpoint, config.conf['publishers'])
    broker_service.start()
