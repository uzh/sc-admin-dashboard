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

from datetime import datetime

from flask import session, request, render_template, redirect, current_app as app
from flask.json import jsonify
from  werkzeug.datastructures import MultiDict

from scadmin.auth import authenticated, authenticate_with_token
from scadmin.models.projects import Projects, Project
from scadmin.models.users import Users
from scadmin.models.quota import Quota
from scadmin.exceptions import InsufficientAuthorization
from scadmin.forms.create_project import CreateProjectForm
from scadmin.forms.adduser import AddUserForm
from scadmin.forms.quotas import SetQuotaForm

from . import main_bp


@main_bp.route('/')
@authenticated
def list_projects():
    projects = Projects()
    return render_template('projects_list.html',
                           # projects=[],
                           projects=projects.list(),
                           auth=session['auth'],
                           curproject=projects.project)

@main_bp.route('project/<project_id>/active')
@authenticated
def set_active_project(project_id):
    authenticate_with_token(project_id=project_id)
    return redirect('/')

@main_bp.route('create-project', methods=['GET', 'POST'])
@authenticated
def create_project():
    form = CreateProjectForm(request.form)
    if request.method == 'POST' and form.validate():
        # create project
        projects = Projects()
        project = projects.create(form)
        return redirect('project/%s' % project.id)
    return render_template('create-project.html', form=form)


@main_bp.route('project/<project_id>', methods=['GET', 'POST'])
@authenticated
def show_project(project_id):
    form = AddUserForm(request.form)
    data = {
        'auth': session['auth'],
        'project': None,
        'project_id': project_id,
        'form': form
    }

    try:
        data['project'] =  Project(project_id)
    except InsufficientAuthorization:
        try:
            # Try again switching to the specified project
            authenticate_with_token(project_id=project_id)
            data['project'] = Project(project_id)
        except InsufficientAuthorization:
            data['error'] = 'Unauthorized: unable to get info on project %s' % project_id

    if request.method == 'POST' and form.validate():
        try:
            users = Users()
            user = users.get(form.uid.data)
            data['project'].grant(form.uid.data, form.role.data)

            data['message'] = 'User %s added to project'
        except Exception as ex:
            data['error'] = "Error setting grant to user '%s': %s" % (form.uid.data, ex)
    try:
        if data['project']:
            data['users'] = data['project'].members()
    except InsufficientAuthorization:
        pass

    return render_template('project.html', **data)

@main_bp.route('project/<project_id>/revoke')
@authenticated
def revoke_grant(project_id):
    uid = request.args.get('userid')
    role = request.args.get('role')
    project = Project(project_id)
    project.revoke(uid, role)
    return redirect('project/%s' % project_id)

@main_bp.route('quota/<project_id>', methods=['GET', 'POST'])
@authenticated
def quota(project_id):
    quota = Quota(project_id)
    project = Project(project_id)
    error = ''
    msg = None

    if request.method == 'POST':
        form = SetQuotaForm(request.form)
        if not quota.has_swift():
            del form.s_bytes
        if form.validate():
            # Update quota
            try:
                updated = quota.set(form.data)
                # Build updated message.
                msg = []
                for qtype, qvalue in updated.items():
                    for key, values in qvalue.items():
                        msg.append("%s: Update %s %d -> %d" % (
                            qtype.upper(), key, values[0], values[1]))
            except Exception as ex:
                error += "Error while updating quota: %s\n" % ex

            try:
                # Update project
                curdate = datetime.now().strftime('(%Y-%d-%m)')
                history = ["%s %s updated quota" % (curdate, session['auth']['user_id'])]
                if form.comment.data:
                    history.append("%s %s" % (curdate, form.comment.data))
                history.extend(["%s %s" % (curdate, line) for line in msg])
                project.add_to_history(str.join('\n', history))
            except Exception as ex:
                app.logger.error("Error while updating history of project %s: %s",
                                  project.name, ex)
                error += 'Error while updating history: %s\n' % ex
            # set some message
            quota = Quota(project_id)
            form = SetQuotaForm(MultiDict(quota.to_dict()))
            if not quota.has_swift():
                del form.s_bytes
    else:
        form = SetQuotaForm(MultiDict(quota.to_dict()))
        if not quota.has_swift():
            del form.s_bytes


    return render_template('quota.html',
                           project=project,
                           form=form,
                           error=error,
                           messages=msg,
                           auth=session['auth'])

@main_bp.route('user')
@authenticated
def search_user():
    users = Users()
    uid = request.args.get('search')
    if uid:
        return jsonify(users.search(uid))
    else:
        return jsonify(users.list())

@main_bp.route('user/<uid>')
@authenticated
def get_user(uid):
    users = Users()
    user = users.get(uid)
    return jsonify(user)
