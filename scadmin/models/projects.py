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

from keystoneclient.v3 import client as keystone_client
from keystoneauth1.exceptions.http import Forbidden

from novaclient.client import Client as nova_client


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


    def __getattr__(self, attr):
        # Some attributes we want to pass them down to self.project
        if attr in ['owner', 'owner_email',
                    'contact', 'contact_email',
                    's3it_owner', 's3it_owner_email',
                    'quota_history',
                    'institute',
                    'faculty',
                    'description',
                    'name']:
            return getattr(self.project, attr)
        else:
            return object.__getattr__(self, attr)


    def members(self):
        try:
            roles = {r.id: r.name for r in self.keystone.roles.list()}
            assignments = self.keystone.role_assignments.list(project=self.project.id)
        except Forbidden:
            raise InsufficientAuthorization

        users = defaultdict(list)
        for a in assignments:
            users[a.user['id']].append(roles[a.role['id']])
        return users

    def grant(self, username, rolename):
        role = self.keystone.roles.find(name=rolename)
        self.keystone.roles.grant(role, user=username, project=self.project)

    def revoke(self, username, rolename):
        role = self.keystone.roles.find(name=rolename)
        self.keystone.roles.revoke(role, user=username, project=self.project)

    def add_to_history(self, history):
        try:
            oldprop = self.project.quota_history
            self.keystone.projects.update(self.project, quota_history=oldprop.strip() + '\n' + history)
        except AttributeError:
            app.logger.info("quota_history property not present in project %s", self.project.name)
            self.keystone.projects.update(self.project, quota_history=history)
        
class Projects:
    def __init__(self):
        self.session = get_session()
        self.keystone = keystone_client.Client(session=self.session)
        self.project = Project(self.session.auth.project_id).project
        self.id = self.project.id
        self.name = self.project.name

    def list(self):
        try:
            projects = self.keystone.projects.list()
            roles = self.keystone.role_assignments.list()
            myroles = self.keystone.role_assignments.list(user=self.session.get_user_id())
        except:
            projects = self.keystone.projects.list(user=self.session.get_user_id())
            roles = self.keystone.role_assignments.list(user=self.session.get_user_id())
            myroles = roles
        rolenames = {r.id: r.name for r in self.keystone.roles.list()}
        plist = []
        for project in projects:
            plist.append({
                'p': project,
                'roles': [rolenames.get(r.role['id']) for r in roles if r.scope['project']['id'] == project.id],
                'myroles': [rolenames.get(r.role['id']) for r in myroles if r.scope['project']['id'] == project.id],
            })
        return plist

    def create(self, form):
        # WARNING: always creating projects in default domain
        domain = self.keystone.domains.get(config.os_project_domain_id)
        project = self.keystone.projects.create(
            form.name.data,
            domain,
            description=form.description.data,
            owner=form.owner.data,
            owner_email=form.owner_email.data,
            contact=form.contact.data,
            contact_email=form.contact_email.data,
            s3it_owner=form.s3it_owner.data,
            s3it_owner_email=form.s3it_owner_email.data,
            faculty=form.faculty.data,
            institute=form.institute.data,
        )
        return project
