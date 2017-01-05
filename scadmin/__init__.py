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

from flask import Flask, render_template, redirect, url_for, session
from flask_bootstrap import Bootstrap
from flask_nav import Nav
import flask_nav.elements as nave

from scadmin.views import main_bp, sympa_bp
from scadmin.auth import login_bp
from scadmin import config


# Navigation
class UserElement(nave.Text):
    def __init__(self):
        pass

    @property
    def text(self):
        return 'Username: {}, current project: {}'.format(
            session['auth']['user_id'],
            session['auth']['project_name'],
        )

class ProjectCreation(nave.View):
    def __init__(self):
        pass

    def get_url(self):
        return url_for('main.create_project')

    @property
    def endpoint(self):
        return self.get_url()

    @property
    def text(self):
        return "Create Project"

def top_nav():
    elements = [nave.View('Project List', 'main.list_projects')]
    if 'admin' in session['auth']['roles'] or \
       'usermanager' in session['auth']['roles']:
        elements.append(ProjectCreation())
        elements.append(nave.View('Check mailing list users', 'sympa.list_users'))
    elements += [UserElement(), nave.View('Logout', 'auth.logout')]
    return nave.Navbar(*elements)

app = Flask(__name__)
app.config.from_object('scadmin.config')

nav = Nav()
nav.register_element('top', top_nav)

Bootstrap(app)
nav.init_app(app)

app.register_blueprint(main_bp, url_prefix='/')
app.register_blueprint(login_bp, url_prefix='/auth')
app.register_blueprint(sympa_bp, url_prefix='/sympa')
