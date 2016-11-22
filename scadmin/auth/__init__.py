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

from flask import redirect, current_app as app, session, Blueprint, url_for, request, render_template

from functools import wraps

from scadmin.exceptions import AuthenticationRequired
from scadmin.forms import LoginForm
from scadmin import config

from keystoneauth1.identity import v3
from keystoneauth1 import session as ksession
from keystoneauth1.exceptions.http import Unauthorized
from keystoneclient.v3 import client as keystone_client


login_bp = Blueprint('auth', __name__)

def authenticate_with_password(username, password):
    auth_data = {}
    auth = v3.Password(auth_url=config.os_auth_url,
                       username=username,
                       password=password,
                       user_domain_name=config.os_user_domain_name)
    sess = ksession.Session(auth=auth)
    keystone = keystone_client.Client(session=sess)
    projects = keystone.projects.list(user=sess.get_user_id())
    # pick one project at random
    auth = v3.Password(auth_url=config.os_auth_url,
                       username=username,
                       password=password,
                       user_domain_name=config.os_user_domain_name,
                       project_id=projects[0].id,
                       project_domain_id=projects[0].domain_id)
    app.logger.info("Correctly authenticated as {}".format(username))
    # get new scoped token
    sess = ksession.Session(auth=auth)
    session['auth'] = {}
    session['auth']['token'] = sess.get_token()
    session['auth']['user_id'] = sess.get_user_id()
    session['auth']['project_id'] = sess.auth.project_id
    session['auth']['project_domain_id'] = sess.auth.project_domain_id
    app.logger.info("User {}: switching to tenant {}".format(username, sess.auth.project_id))


def get_session(auth):
    auth = v3.Token(
        auth_url=config.os_auth_url,
        token=session['auth']['token'],
        project_id=session['auth']['project_id'],
        project_domain_name=session['auth']['project_domain_id'],
    )
    sess = ksession.Session(auth=auth)
    return sess
    
def authenticate_with_token():
    sess = get_session(session['auth'])
    session['auth']['token'] = sess.get_token()
    session['auth']['user_id'] = sess.get_user_id()
    session['auth']['project_id'] = sess.auth.project_id
    session['auth']['project_domain_id'] = sess.auth.project_domain_id
    app.logger.info("User {} authenticated on tenant tenant {} using token".format(session['auth']['user_id'], sess.auth.project_id))


def authenticated(f):
    """Decorator"""
    @wraps(f)
    def decorated(*args, **kw):
        # Check session
        if 'auth' not in session:
            return redirect(url_for('auth.login'))
        else:
            try:
                authenticate_with_token()
            except Unauthorized:
                return redirect(url_for('auth.login'))
            return f(*args, **kw)
    return decorated


@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        authenticate_with_password(form.username.data, form.password.data)
        return redirect('/')
    return render_template('auth/login.html', form=form)
                        
@login_bp.route('/logout')
def logout():
    if 'auth' in session:
        del session['auth']
    return redirect(url_for('auth.login'))
