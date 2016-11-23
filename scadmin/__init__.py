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

from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_nav import Nav
import flask_nav.elements as nave

from scadmin.views import main_bp
from scadmin.auth import login_bp

# Navigation
nav = Nav()
nav.register_element('top', nave.Navbar(
    nave.View('SC dashboard', 'main.list_projects'),
    nave.View('Logout', 'auth.logout'),
))


app = Flask(__name__)
Bootstrap(app)
nav.init_app(app)

app.config.from_object('scadmin.config')

app.register_blueprint(main_bp, url_prefix='/')
app.register_blueprint(login_bp, url_prefix='/auth')
