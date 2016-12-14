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

from scadmin.auth import get_session
from scadmin.exceptions import InsufficientAuthorization
from scadmin import config

from keystoneclient.v3 import client as keystone_client
from keystoneauth1.exceptions.http import Forbidden

from collections import defaultdict

import json

class Users:
    def __init__(self):
        self.session = get_session()
        self.keystone = keystone_client.Client(session=self.session)

    def list(self):
        users = defaultdict(list)
        rolenames  = {r.id: r.name for r in self.keystone.roles.list()}
        
        for role in self.keystone.role_assignments.list():
            users[role.user['id']].append({'project': role.scope['project']['id'],
                                           'role': rolenames.get(role.role['id'])})
        return users

    def search(self, username):
        users = {uid:u for uid,u in self.list().items() if username in uid}
        return users

    def get(self, uid):
        user = self.keystone.users.get(uid)
        return user.to_dict()
