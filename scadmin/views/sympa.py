#!/usr/bin/env python
# -*- coding: utf-8 -*-#
#
#
# Copyright (C) 2017, S3IT, University of Zurich. All rights reserved.
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

from flask import session, request, render_template, redirect, url_for, current_app as app
from scadmin.auth import authenticated, has_role
from scadmin.models.users import Users
from scadmin.models.sympa import ML
from scadmin import config
from scadmin.forms.sympa import SympaAddRemove

from . import sympa_bp

@sympa_bp.route('/', methods=['GET', 'POST'])
@authenticated
@has_role(['admin', 'usermanager'])
def list_users():
    data = {
        'auth': session['auth'],
        'error': [],
        'info': [],
        'missing': [],
        'exceeding': [],
        'sy_user': config.SYMPA_USERNAME,
    }
    form = data['form'] = SympaAddRemove(request.form)

    scusers = data['scusers'] = Users()
    ml = data['ml'] = ML()
    try:
        ml.login()
    except Exception as ex:
        data['error'].append("Unable to access Sympa mailing list server: %s" % ex)
        return render_template('ml_users.html', **data)
        

    all_users = scusers.list_users(project_admins=False)
    users_email = [u['email'] for u in all_users] + [i[1] for i in config.SYMPA_EMAIL_MAPPINGS if i[1]]

    missing_email, exceeding = ml.missing_and_exceeding(users_email)
    data['exceeding'] = exceeding
    missing = data['missing'] = [u for u in all_users if u['email'] in missing_email]

    form.email_add.choices = [(i,i) for i in missing_email]
    form.email_remove.choices = [(i,i) for i in exceeding]

    if request.method == 'POST' and form.validate():
        to_add = [f.data for f in form.email_add if f.checked]
        if to_add:
            info, err = ml.add(to_add)

        to_remove = [f.data for f in form.email_remove if f.checked]
        if to_remove:
            info2, err2 = ml.remove(to_remove)
            info += info2
            err += err2

        missing_email, exceeding = ml.missing_and_exceeding([u['email'] for u in all_users])
        missing = [u for u in all_users if u['email'] in missing_email]

        form.email_add.choices = [(i,i) for i in missing_email]
        form.email_remove.choices = [(i,i) for i in exceeding]
        return render_template('ml_users.html', **data)

    return render_template('ml_users.html', **data)
