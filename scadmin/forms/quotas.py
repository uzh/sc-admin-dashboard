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

from wtforms import Form, StringField, IntegerField, SubmitField, validators
from flask_wtf import FlaskForm
from scadmin import config

class SetQuotaForm(FlaskForm):
    c_instances = IntegerField('instances')
    c_cores = IntegerField('cores')
    c_ram = IntegerField('ram')


    n_port = IntegerField('Number of network ports')
    n_network = IntegerField('Number of networks')
    n_subnet = IntegerField('Number of subnets')
    n_security_group = IntegerField('Number of security groups')
    n_floatingip = IntegerField('Number of floating IPs')
    n_router = IntegerField('Number of routers')

    v_gigabytes = IntegerField('Volumes: gigabytes')
    v_volumes = IntegerField('Number of volumes')

    s_bytes = IntegerField('Swift bytes')

    comment = StringField("Comment")
    submit = SubmitField('Set quota')

    def validate_c_ram(form, field):
        if field.data != 4*1024*form.c_cores.data:
            raise validators.ValidationError(
                "Ram should be 4*1024 times the number of cores, in this case: %d" % (4*1024*form.c_cores.data))

    def validate_n_port(form, field):
        if field.data < form.c_instances.data:
            raise validators.ValidationError(
                "Network ports should at least be as much as the number of instances (%d)" % form.c_instances.data)
        
