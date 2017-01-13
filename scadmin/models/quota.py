#!/usr/bin/env python
# -*- coding: utf-8 -*-#
#
#
# Copyright (C) 2016, S3IT, University of Zurich. All rights reserved.
#
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

__docformat__ = 'reStructuredText'
__author__ = 'Antonio Messina <antonio.s.messina@gmail.com>'

from flask import session
from collections import defaultdict

from scadmin.auth import get_session
from scadmin.exceptions import InsufficientAuthorization
from scadmin import config
from flask import current_app as app

from keystoneclient.v3 import client as keystone_client
from novaclient.client import Client as nova_client
from cinderclient import client as cinder_client
from neutronclient.v2_0 import client as neutron_client
import swiftclient

class Quota:
    def __init__(self, project_id):
        self.project_id = project_id
        self.session = get_session()

        self.keystone = keystone_client.Client(session=self.session)
        self.nova = nova_client('2', session=self.session)
        self.neutron = neutron_client.Client(session=self.session)
        self.cinder = cinder_client.Client('2', session=self.session)
        self.storage_url = None
        self.update_quota()

    def update_quota(self):
        # Create swift client
        try:
            swift_service = self.keystone.services.find(type='object-store')
            swift_endpoint = self.keystone.endpoints.find(service_id=swift_service.id, interface='public')
            self.storage_url = swift_endpoint.url % dict(tenant_id=self.project_id)
            app.logger.info("Using swift storage_url %s", self.storage_url)
            account = swiftclient.head_account(self.storage_url, self.session.get_token())
            swift_curquota = account.get('x-account-meta-quota-bytes', -1)
        except Exception as ex:
            app.logger.warning("No swift endpoint found. (exception was: %s", ex)
            swift_curquota = -1


        self.quota = {
            'nova': { },
            'neutron': {},
            'cinder': {},
            'swift': {'bytes': swift_curquota},
        }

        # Get nova quota
        quota = self.nova.quotas.get(self.project_id)
        self.quota['nova'] = {
            'cores': quota.cores,
            'instances': quota.instances,
            'ram': quota.ram * 2**20,
        }

        quota = self.cinder.quotas.get(self.project_id)
        self.quota['cinder'] = {
            'volumes': quota.volumes,
            'gigabytes': quota.gigabytes * 2**30,
        }

        # Get neutron quota
        quota = self.neutron.show_quota(self.project_id)['quota']
        self.quota['neutron'].update(quota)

    def has_swift(self):
        return self.storage_url is not None

    def to_dict(self):
        toret = {}
        for key,value in self.quota['nova'].items():
            toret['c_' + key] = value

        for key,value in self.quota['neutron'].items():
            toret['n_' + key] = value

        for key,value in self.quota['cinder'].items():
            toret['v_' + key] = value

        for key,value in self.quota['swift'].items():
            toret['s_' + key] = value

        return toret

    def from_dict(self, data):
        toret = {'nova': {},
                 'neutron': {},
                 'cinder': {},
                 'swift': {},
        }

        for key, value in data.items():
            if key[:2] == 'c_':
                toret['nova'][key[2:]] = value
            if key[:2] == 'n_':
                toret['neutron'][key[2:]] = value
            if key[:2] == 'v_':
                toret['cinder'][key[2:]] = value
            if key[:2] == 's_':
                toret['swift'][key[2:]] = value
        return toret

    def set(self, quota):
        """Update quota for project"""
        toupdate = self.from_dict(quota)
        updated = defaultdict(dict)
        # Check if we need to update nova quota
        for key, value in list(toupdate['nova'].items()):
            if value == self.quota['nova'][key]:
                del toupdate['nova'][key]
            else:
                updated['nova'][key] = (self.quota['nova'][key], toupdate['nova'][key])

        if toupdate['nova']:
            # All quota is stored in bytes, but nova wants ram quota in megabytes
            if 'ram' in toupdate['nova']:
                toupdate['nova']['ram'] = int(toupdate['nova']['ram']/2**20)
                updated['nova']['ram'] = (
                    int(self.quota['nova']['ram']/2**20),
                    toupdate['nova']['ram'])
        self.nova.quotas.update(self.project_id, **toupdate['nova'])

        for key, value in list(toupdate['cinder'].items()):
            if value == self.quota['cinder'][key]:
                del toupdate['cinder'][key]
            else:
                updated['cinder'][key] = (self.quota['cinder'][key], toupdate['cinder'][key])
        if toupdate['cinder']:
            # All quota is stored in bytes, but cinder wants quota in gigabytes
            if 'gigabytes' in toupdate['cinder']:
                toupdate['cinder']['gigabytes'] = int(toupdate['cinder']['gigabytes']/2**30)
                updated['cinder']['gigabytes'] = (
                    self.quota['cinder']['gigabytes']/2**30,
                    toupdate['cinder']['gigabytes'])
            self.cinder.quotas.update(self.project_id, **toupdate['cinder'])

        for key, value in list(toupdate['neutron'].items()):
            if value == self.quota['neutron'][key]:
                del toupdate['neutron'][key]
            else:
                updated['neutron'][key] = (self.quota['neutron'][key], toupdate['neutron'][key])
        self.neutron.update_quota(self.project_id, {'quota': toupdate['neutron']})

        for key, value in list(toupdate['swift'].items()):
            if value is None or value == self.quota['swift'][key]:
                del toupdate['swift'][key]
            else:
                updated['swift'][key] = (self.quota['swift'][key], toupdate['swift'][key])

        # Re-read from API
        self.update_quota()
        return updated

    def _update_swift_quota(self, quota):
        if not self.storage_url:
            app.logger.warning("Not updating swift quota as storage_url is empty")
            return
        token = self.session.get_token()
        account = swiftclient.head_account(self.storage_url, token)
        swiftclient.post_account(url=self.storage_url,
                                 token=token,
                                 headers={'x-account-meta-quota-bytes': str(quota['bytes'])})

