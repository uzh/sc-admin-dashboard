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
from scadmin.exceptions import InsufficientAuthorization, NotFound
from scadmin import config

from keystoneclient.v3 import client as keystone_client
from keystoneauth1.exceptions.http import Forbidden, NotFound as http_NotFound

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

    def list_users(self, project_admins=False):
        users = []

        for uid in set((u.user['id'] for u in self.keystone.role_assignments.list())):
            user = self.keystone.users.get(uid)
            if user.domain_id == 'default':
                users.append({'id':uid, 'email':user.email})

        emails = [u['email'] for u in users]

        if project_admins:
            for project in self.keystone.projects.list():
                if not project.enabled:
                    continue
                for attr in ['owner', 'contact', 's3it_owner']:
                    try:
                        name = getattr(project, attr)
                        email = getattr(project, attr+'_email')
                        if email not in emails:
                            users.append({'id': name, 'email': email})
                            emails.append(email)
                    except AttributeError:
                        pass

        return users

    def search(self, username):
        users = {uid:u for uid,u in self.list().items() if username in uid}
        return users

    def get(self, uid):
        try:
            user = self.keystone.users.get(uid)
        except http_NotFound as ex:
            raise NotFound('User %s not found' % uid)

        return user.to_dict()

    def admin_emails(self):
        """List all email addresses listed in project fields like 'owner' and 's3it_owner'"""
        emails = set()
        for project in self.keystone.projects.list():
            if not project.enabled:
                continue
            for attr in ['owner_email', 'contact_email', 's3it_owner_email']:
                try:
                    emails.add(getattr(project, attr))
                except AttributeError:
                    pass
        return list(emails)
