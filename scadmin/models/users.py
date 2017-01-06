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
import re

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
        
        assignments = self.list()
        projects = {p.id: p for p in self.keystone.projects.list()}
        for uid in assignments:
            user = self.keystone.users.get(uid)
            if user.domain_id == 'default':
                roles = assignments.get(uid)
                for role in roles:
                    role['project_name'] = projects[role['project']].name
                u = {'id':uid,
                     'email':user.email,
                     'roles': roles}
                users.append(u)

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

    def search(self, regexp, email=False):
        if email:
            return self._search_full(regexp)
        else:
            return self._search_uid(regexp)

    def _search_full(self, regexp):
        try:
            regexp = re.compile(regexp)
            def match(user):
                if regexp.match(user['id']) or \
                   regexp.match(user['email']):
                    return True
                else:
                    return False
        except re.error:
            def match(user):
                return regexp in user['id'] or regexp in user['email']

        users = {u['id']:u for u in self.list_users() if match(u)}
        return users

    def _search_uid(self, regexp):
        try:
            regexp = re.compile(regexp)
            def match(uid):
                if regexp.match(uid):
                    return True
                else:
                    return False
        except re.error:
            def match(uid):
                return regexp in uid
        return {uid:{'roles': u} for uid, u in self.list().items() if match(uid)}
    
    def get(self, uid):
        try:
            user = self.keystone.users.get(uid)
            u = user.to_dict()
        except http_NotFound as ex:
            raise NotFound('User %s not found' % uid)

        u['roles'] = roles = []
        rolenames  = {r.id: r.name for r in self.keystone.roles.list()}
        projects = {p.id: p for p in self.keystone.projects.list()}
        for role in self.keystone.role_assignments.list(user=uid):
            pid = role.scope['project']['id']
            rid = role.role['id']
            roles.append({'project': pid,
                     'project_name': projects[pid].name,
                     'role': rid,
                     'role_name': rolenames[rid],
                     })
                 
        return u

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
