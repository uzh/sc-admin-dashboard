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

from flask import session, request, render_template, redirect, url_for, current_app as app
from flask.json import jsonify
from  werkzeug.datastructures import MultiDict

from scadmin import config
from scadmin.auth import authenticated, authenticate_with_token
from scadmin.models.projects import Projects, Project
from scadmin.models.users import Users
from scadmin.models.quota import Quota
from scadmin.models.sympa import ML
from scadmin.exceptions import InsufficientAuthorization, NotFound
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
    return redirect(url_for('main.list_projects'))

@main_bp.route('create-project', methods=['GET', 'POST'])
@authenticated
def create_project():
    data = {
        'auth': session['auth'],
        'error': [],
        'info': [],
    }

    form = data['form'] = CreateProjectForm(request.form)
    if request.method == 'POST' and form.validate():
        # create project
        projects = Projects()
        project = projects.create(form)
        return redirect('project/%s' % project.id)
    return render_template('create-project.html', **data)


@main_bp.route('project/<project_id>', methods=['GET', 'POST'])
@authenticated
def show_project(project_id):
    form = AddUserForm(request.form)
    data = {
        'auth': session['auth'],
        'project': None,
        'project_id': project_id,
        'form': form,
        'error': [],
        'info': [],
    }
    reqerror = request.args.get('error')
    if reqerror:
        data['error'].append(reqerror)
        
    reqinfo = request.args.get('info')
    if reqinfo:
        data['info'].append(reqinfo)
    
    try:
        data['project'] =  Project(project_id)
    except InsufficientAuthorization:
        try:
            # Try again switching to the specified project
            authenticate_with_token(project_id=project_id)
            data['project'] = Project(project_id)
        except InsufficientAuthorization:
            data['error'].append('Unauthorized: unable to get info on project %s\n' % project_id)

    if request.method == 'POST' and form.validate():
        try:
            users = Users()
            user = users.get(form.uid.data)
            data['project'].grant(form.uid.data, form.role.data)

            data['info'].append('User %s (%s) added to project' % (user['id'], user['email']))

            # Add user to mailing list
            if config.USE_SYMPA:
                ml = ML()
                ml.login()
                info, err = ml.add([user['email']])
                if err:
                    data['error'].append('Error while adding user to mailing list\n')
                    data['error'] += err
                if info:
                    data['info'] += info
        except Exception as ex:
            data['error'].append("Error setting grant to user '%s': %s\n" % (form.uid.data, ex))


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
    return redirect(url_for('main.show_project',
                            project_id=project_id,
                            info="Role %s revoked from user %s" % (role, uid)))


@main_bp.route('quota/<project_id>', methods=['GET', 'POST'])
@authenticated
def quota(project_id):
    data = {
        'auth': session['auth'],
        'error': [],
        'info': [],
        'form': None,
    }
    data['quota'] = Quota(project_id)
    project = data['project'] = Project(project_id)

    if request.method == 'POST':
        data['form'] = SetQuotaForm(request.form)
        if not data['quota'].has_swift():
            del data['form'].s_bytes

        if data['form'].validate():
            # Update quota
            try:
                updated = data['quota'].set(data['form'].data)
                # Build updated message.
            except Exception as ex:
                data['error'].append("Error while updating quota: %s\n" % ex)
            try:
                h_update = []
                for qtype, qvalue in updated.items():
                    for key, values in qvalue.items():
                        h_update.append("%s: Update %s %s -> %s" % (
                            qtype.upper(), key, values[0], values[1]))
            except Exception as ex:
                data['error'].append("Error while writing quota message: %s\n" % ex)
            try:
                if not data['error']:
                    # Update project
                    curdate = datetime.now().strftime('(%Y-%m-%d %H:%M)')
                    history = ["%s %s updated quota" % (curdate, session['auth']['user_id'])]
                    if data['form'].comment.data:
                        history.append("%s %s" % (curdate, data['form'].comment.data))
                    history.extend(["%s %s" % (curdate, line) for line in h_update])
                    data['info'].extend(h_update)
                    project.add_to_history(str.join('\n', history))
            except Exception as ex:
                app.logger.error("Error while updating history of project %s: %s",
                                  project.name, ex)
                data['error'].append('Error while updating history: %s\n' % ex)
            # set some message
            data['quota'] = Quota(project_id)
            data['form'] = SetQuotaForm(MultiDict(data['quota'].to_dict()))
            if not data['quota'].has_swift():
                del data['form'].s_bytes
        else:
            data['error'].append('Some data is missing/wrong.')
    else:
        data['form'] = SetQuotaForm(MultiDict(data['quota'].to_dict()))
        if not data['quota'].has_swift():
            del data['form'].s_bytes


    return render_template('quota.html', **data)

@main_bp.route('user')
@authenticated
def search_user():
    users = Users()
    uid = request.args.get('search')
    email = request.args.get('email', '')

    if uid and email.lower() in ['1', 'yes', 'on']:
        return jsonify(users.search(uid, email=True))
    elif uid:
        return jsonify(users.search(uid))
    else:
        return jsonify(users.list())

@main_bp.route('user/<uid>')
@authenticated
def get_user(uid):
    users = Users()
    try:
        user = users.get(uid)
    except NotFound:
        return jsonify({})
    return jsonify(user)
