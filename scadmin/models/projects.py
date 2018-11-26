#!/usr/bin/env python
# -*- coding: utf-8 -*-#
#
#
# Copyright (C) 2016-2018, University of Zurich. All rights reserved.
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

from flask import session, current_app as app
from collections import defaultdict, OrderedDict
import re

from scadmin.auth import get_session
from scadmin.exceptions import InsufficientAuthorization
from scadmin import config
from scadmin.utils import to_bib

from keystoneclient.v3 import client as keystone_client
from keystoneauth1.exceptions.http import Forbidden

from novaclient.client import Client as nova_client
from neutronclient.v2_0 import client as neutron_client
from neutronclient.common.exceptions import Conflict


class Project(object):
    def __init__(self, name_or_id=None):
        self.session = get_session()
        self.keystone = keystone_client.Client(session=self.session)
        if name_or_id == None:
            name_or_id = session['auth']['project_id']

        try:
            self.project = self.keystone.projects.get(name_or_id)
        except Forbidden:
            projects = self.keystone.projects.list(user=self.session.get_user_id(), enabled=True)
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
                    'name',
                    'id']:
            try:
                return getattr(self.project, attr)
            except AttributeError:
                return ''
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
        try:
            role = self.keystone.roles.find(name=rolename)
            self.keystone.roles.grant(role, user=username, project=self.project)
        except Forbidden:
            raise InsufficientAuthorization


    def revoke(self, username, rolename):
        try:
            role = self.keystone.roles.find(name=rolename)
            self.keystone.roles.revoke(role, user=username, project=self.project)
        except Forbidden:
            raise InsufficientAuthorization


    def add_to_history(self, history):
        try:
            newhistory = self.project.quota_history.strip() + '\n' + history
        except AttributeError:
            newhistory = history

        self.keystone.projects.update(self.project, quota_history=newhistory)
        self.project.quota_history = newhistory

    def history(self):
        """Returns an ordered dictionary {
        'YYYY-MM-DD': {'msg': "commit message",
                       'services': {
                           '<service>': {'<type>': (<old>, <new>, <oldunit>, <newunit>)}}
                      },
        }"""
        quota_history = OrderedDict()
        remsg = re.compile('\((?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2}(\s*[0-9]{2}:[0-9]{2})?)\) *(?P<msg>.*)')
        requotaline = re.compile('(?P<service>NEUTRON|SWIFT|CINDER[^:]*|NOVA): (?P<update>.*)')
        requota = re.compile('((?P<type>[^:]+): )?(?P<new>[+-]*[0-9]+) *(?P<unit>GiB|TiB)? *\((?P<delta>[+-][0-9]+) *(?P<oldunit>GiB|TiB)?\)')
        requota2 = re.compile('Update (?P<type>[^:]+) (?P<old>[0-9]+) -> (?P<new>[0-9]+)')


        for line in self.quota_history.splitlines():
            if not remsg.match(line):
                continue
            m = remsg.search(line)
            date = m.group('date')
            msg = m.group('msg')
            if date not in quota_history:
                quota_history[date] = {'msg': '', 'services': []}

            curdata = quota_history[date]['services']

            m = requotaline.match(msg)
            if not m and msg:
                if quota_history[date]['msg']:
                    quota_history[date]['msg'] += ('\n%s' % msg)
                else:
                    quota_history[date]['msg'] = msg
                continue
            service = m.group('service')
            d = OrderedDict()
            curdata.append((service, d))
            for update in m.group('update').split(','):
                u = requota.search(update.strip())
                if not u:
                    continue
                new, delta = int(u.group('new')), int(u.group('delta'))
                old = new - delta
                oldunit = u.group('unit')
                newunit = oldunit
                if newunit is None:
                    newunit = oldunit = ''

                typ = u.group('type')
                if typ in ['ram', 'bytes', 'gigabytes', 'gigabytes_vhp']:
                    if typ == 'ram':
                        old *= 2**20
                        new *= 2**20
                    elif typ.startswith('gigabytes'):
                        old *= 2**30
                        new *= 2**30
                    if not newunit:
                        old, oldunit = to_bib(old)
                        new, newunit = to_bib(new)
                if not typ:
                    typ = 'default'
                if typ in d:
                    typidx = 1
                    while '%s %d' % (typ, typidx) in d:
                        typidx += 1
                    # This usually measn that there were two quota updates in the same day.
                    typ = "%s (%d)" % (typ, typidx)
                d[typ] = (old, new, oldunit, newunit)
            # Also check if the quota history line matches the new regexp
            u = requota2.search(m.group('update'))
            if u:
                # Note: these values are absolute, so we might want to
                # convert them to human-readable.
                old, new = int(u.group('old')), int(u.group('new'))
                oldunit = newunit = ''
                typ = u.group('type')
                if typ in ['ram', 'bytes', 'gigabytes', 'gigabytes_vhp']:
                    if typ == 'ram':
                        old *= 2**20
                        new *= 2**20
                    elif typ.startswith('gigabytes'):
                        old *= 2**30
                        new *= 2**30
                    old, oldunit = to_bib(old)
                    new, newunit = to_bib(new)
                d[typ] = (old, new, oldunit, newunit)

        return quota_history

class Projects(object):
    def __init__(self):
        self.session = get_session()
        self.keystone = keystone_client.Client(session=self.session)
        self.neutron = neutron_client.Client(session=self.session)
        self.nova = nova_client('2', session=self.session)

        self.project = Project(self.session.auth.project_id).project
        self.id = self.project.id
        self.name = self.project.name


    def list(self):
        plist = []

        # FIXME!!! Hardcoding the role meaning!

        if 'admin' in session['auth']['roles'] or 'usermanager' in session['auth']['roles']:
            projects = self.keystone.projects.list(enabled=True)
            rolenames = {r.id: r.name for r in self.keystone.roles.list()}
            roles = self.keystone.role_assignments.list()
            myroles = self.keystone.role_assignments.list(user=self.session.get_user_id())
        elif 'project_admin' in session['auth']['roles']:
            projects = self.keystone.projects.list(user=self.session.get_user_id(), enabled=True)
            rolenames = {r.id: r.name for r in self.keystone.roles.list()}
            myroles = self.keystone.role_assignments.list(user=self.session.get_user_id())
            roles = myroles
        else:
            projects = self.keystone.projects.list(user=self.session.get_user_id(), enabled=True)


        if not session['auth']['regular_member']:
            for project in projects:
                plist.append({
                    'p': project,
                    'roles': [rolenames.get(r.role['id']) for r in roles if r.scope['project']['id'] == project.id],
                    'myroles': [rolenames.get(r.role['id']) for r in myroles if r.scope['project']['id'] == project.id],
                })
        else:
            # Regular member
            for project in projects:
                plist.append({'p': project})

        return plist

    def create(self, form):
        # FIXME: always creating projects in default domain
        domain = self.keystone.domains.get(config.os_project_domain_id)
        project = self.keystone.projects.create(
            form.name.data,
            domain,
            description=form.description.data,
            enabled=False,  # will enable after configuring it
            owner=form.owner.data,
            owner_email=form.owner_email.data,
            contact=form.contact.data,
            contact_email=form.contact_email.data,
            s3it_owner=form.s3it_owner.data,
            s3it_owner_email=form.s3it_owner_email.data,
            faculty=form.faculty.data,
            institute=form.institute.data,
        )
        # additional configuration
        self.neutron.update_quota(project.id, {
            'quota': {
                'floatingip': 0,  # see: https://trello.com/c/ywH3WR8c/132-newly-created-project-have-a-10-floating-ips-quota-instead-of-0
            },
        })
        # all done, enable project
        self.keystone.projects.update(project, enabled=True)
        return project
