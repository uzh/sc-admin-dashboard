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

from wtforms import Form, StringField, SelectField, SubmitField, TextAreaField, validators
from flask_wtf import FlaskForm
from scadmin import config

class CreateProjectForm(FlaskForm):
    name = StringField(
        'Project Name',
        [validators.Length(min=4), validators.DataRequired()]
    )
    description = TextAreaField(
        'Description',
        [validators.Length(min=4), validators.DataRequired()]
    )
    faculty = SelectField(
        'Faculty',
        [validators.DataRequired()],
        choices=config.valid_faculties,
        description='''One of the UZH faculties, or "<i>none</i>" if it's an'''
        ''' external or cross-faculty project.'''
    )
    institute = StringField(
        'Institute',
        [validators.DataRequired()]
    )

    owner = StringField(
        'Owner',
        [validators.DataRequired()],
        description='Also known as SC-C or SC-Customer, is the owner of the'
        ' project and the person who can represents the group.'
    )
    owner_email = StringField(
        "Email address of the project owner",
        [validators.DataRequired(), validators.Email()],
    )


    contact = StringField(
        'Technical Contact',
        [validators.DataRequired()],
        description='Also known as SC-TC, is the technical contact for this project.'
    )

    contact_email = StringField(
        "Email address of technical contact person",
        [validators.DataRequired(), validators.Email()],
    )

    s3it_owner = StringField(
        'S3IT Owner', [validators.DataRequired()],
        description='S3IT contact person for this project.'
    )

    s3it_owner_email = StringField(
        "Email address of the S3IT contact person",
        [validators.DataRequired(), validators.Email()],
    )
    submit = SubmitField('Create project')
