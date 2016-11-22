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

from keystoneclient.v3 import client as keystone_client
from keystoneauth1.exceptions.http import Forbidden




class Project:
    def __init__(self, name_or_id=None):
        self.session = get_session()
        self.keystone = keystone_client.Client(session=self.session)
        if name_or_id == None:
            name_or_id = session['auth']['project_id']

        try:
            self.project = self.keystone.projects.get(name_or_id)
        except Forbidden:
            projects = self.keystone.projects.list(user=self.session.get_user_id())
            for project in projects:
                if project.id == self.session.auth.project_id:
                    self.project = project

    def members(self):
        try:
            roles = {r.id: r.name for r in self.keystone.roles.list()}
            assignments = self.keystone.role_assignments.list(project=self.project.id)
        except Forbidden:
            raise InsufficientAuthorization
        
        return {a.user['id']: roles[a.role['id']] for a in assignments}

    def add_suer(self, userid):
        pass


class Projects:
    def __init__(self):
        self.session = get_session()
        self.keystone = keystone_client.Client(session=self.session)
        self.project = Project(self.session.auth.project_id).project

    def list(self):
        try:
            return self.keystone.projects.list()
        except:
            return self.keystone.projects.list(user=self.session.get_user_id())
