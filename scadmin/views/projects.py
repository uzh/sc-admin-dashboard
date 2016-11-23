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

from flask import session, request, render_template, redirect

from scadmin.auth import authenticated, authenticate_with_token
from scadmin.models.projects import Projects, Project
from scadmin.exceptions import InsufficientAuthorization

from . import main_bp

@main_bp.route('/')
@authenticated
def list_projects():
    projects = Projects()
    return render_template('projects_list.html',
                           # projects=[],
                           projects=projects.list(),
                           auth=session['auth'],
                           project=projects.project)

@main_bp.route('project/<project_id>/active')
@authenticated
def set_active_project(project_id):
    authenticate_with_token(project_id=project_id)
    return redirect('/')

@main_bp.route('project/<project_id>')
@authenticated
def show_project(project_id):
    project = None
    data = {
        'users': {},
        'auth': session['auth'],
        'project': None,
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
    try:
        if project:
            data['users'] = project.members()
    except InsufficientAuthorization:
        pass

    return render_template('project.html', **data)
