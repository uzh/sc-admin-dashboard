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

from wtforms import Form, widgets, SelectMultipleField, SubmitField, validators
from flask_wtf import FlaskForm
from scadmin import config
from wtforms.widgets.core import HTMLString

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class SympaAddRemove(FlaskForm):
    email_add = MultiCheckboxField('email', choices=[])
    email_remove = MultiCheckboxField('email', choices=[])

    submit = SubmitField('Add/remove users to mailing list')
