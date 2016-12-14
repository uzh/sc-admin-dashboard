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

from novaclient.client import Client as nova_client
from cinderclient import client as cinder_client
from neutronclient.v2_0 import client as neutron_client
import swiftclient

class Quota:
    def __init__(self, project_id):
        self.project_id = project_id
        self.session = get_session()

        self.nova = nova_client('2', session=self.session)
        self.neutron = neutron_client.Client(session=self.session)
        self.cinder = cinder_client.Client('2', session=self.session)

        self.quota = {
            'nova': { },
            'neutron': {},
            'cinder': {},
            'swift': {},
        }

        # Get nova quota
        quota = self.nova.quotas.get(project_id)
        self.quota['nova'] = {
            'cores': quota.cores,
            'instances': quota.instances,
            'ram': quota.ram,
        }

        quota = self.cinder.quotas.get(project_id)
        self.quota['cinder'] = {
            'volumes': quota.volumes,
            'gigabytes': quota.gigabytes,
        }
        
        # Get neutron quota
        quota = self.neutron.show_quota(project_id)['quota']
        self.quota['neutron'].update(quota)


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

        # Check if we need to update nova quota
        for key, value in toupdate['nova'].items():
            if value == self.quota['nova'][key]:
                del toupdate['nova'][key]
        self.nova.quotas.update(self.project_id, **toupdate['nova'])

        for key, value in toupdate['cinder'].items():
            if value == self.quota['cinder'][key]:
                del toupdate['cinder'][key]
        self.cinder.quotas.update(self.project_id, **toupdate['cinder'])

        for key, value in toupdate['neutron'].items():
            if value == self.quota['neutron'][key]:
                del toupdate['neutron'][key]
        self.neutron.update_quota(self.project_id, {'quota': toupdate['neutron']})
        
        return ""
