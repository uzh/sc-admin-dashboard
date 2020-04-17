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

from wtforms import Form, StringField, IntegerField, SubmitField, validators, BooleanField
from flask_wtf import FlaskForm
from scadmin import config
from wtforms.widgets.core import HTMLString

class S3ITField(IntegerField):
    def __call__(self, **kwargs):
        """Custom render"""
        label = '<label for="{id}" class="col-xs-1 col-form-label">{label}</label>'.format(
            id=self.id, label=self.label)
        input = '''
<div class="control-group col-xs-2 {haserror}">
  <input id="{id}" name="{name}" type="text" value="{value}" {extra}></input>
  <span class="help-block">{errors}</span>
</div>'''.format(id=self.id,
                 name=self.name,
                 value=self.data,
                 haserror='has-error' if self.errors else '',
                 errors=str.join('\n', self.errors),
                 extra=str.join(' ', ['%s="%s"' % (k,v) for k,v in kwargs.items()]))
        return HTMLString(str.join('\n', (label, input)))

class BytesField(IntegerField):
    """custom renderer"""
    def __call__(self, **kwargs):
        label = '<label for="{id}" class="col-xs-1 col-form-label">{label}</label>'.format(
            id=self.id, label=self.label)
        # hidden input contains the actual value.
        # _human form will hold the human readable value
        input = '''
<div class="control-group col-xs-2 {haserror}">
  <input id="{id}" name="{id}" type="hidden" value="{value}"></input>
  <input id="{id}_human" name="{name}_human" type="text" value="" {extra}></input>
  <span class="help-block">{errors}</span>
  <span id="{id}_old" cur="{value}"></span>
</div>'''.format(id=self.id,
                 name=self.name,
                 value=self.data,
                 haserror='has-error' if self.errors else '',
                 errors=str.join('\n', self.errors),
                 extra=str.join(' ', ['%s="%s"' % (k,v) for k,v in kwargs.items()]))


        javascript = '''<script type="text/javascript">
$(document).ready(function(){registerConverter('#%s')})
</script>''' % self.id

        return HTMLString(str.join('\n', (label, input, javascript)))

def b_to_human(value):
    """Convert bytes to human readable string"""
    value = float(value)
    for unit, threshold in [('EiB', 2**60),
                            ('PiB', 2**50),
                            ('TiB', 2**40),
                            ('GiB', 2**30),
                            ('MiB', 2**20),
                            ('KiB', 2**10),
                            ]:
        if value > threshold:
            return "%.2f %s" % (value/threshold, unit)
    return "%d B" % value


class SetQuotaForm(FlaskForm):
    c_instances = S3ITField('Nr. of Instances')
    c_cores = S3ITField('Nr. of vCores')
    c_ram = BytesField('Max Ram')


    n_port = S3ITField('Number of network ports')
    n_network = S3ITField('Number of networks')
    n_subnet = S3ITField('Number of subnets')
    n_security_group = S3ITField('Number of security groups')
    n_security_group_rule = S3ITField('Number of security group rules')
    n_floatingip = S3ITField('Number of floating IPs')
    n_router = S3ITField('Number of routers')

    v_gigabytes = BytesField('Volumes: gigabytes')
    v_volumes = S3ITField('Number of volumes')

    s_bytes = BytesField('Swift bytes')

    comment = StringField("Comment", [validators.DataRequired()])

    force = BooleanField("Bypass validation")
    submit = SubmitField('Set quota')

    def validate_c_ram(form, field):
        diff4 = field.data - 4*2**30*form.c_cores.data
        diff8 = field.data - 8*2**30*form.c_cores.data
        if not form.force.data and abs(float(diff8)/field.data) > 0.01:
            if abs(float(diff4)/field.data) > 0.01:
              raise validators.ValidationError(
                "Ram should be 4 or 8 GiB x nr.vcores, in case of 4:1 use %s (%s) instead of %s" % (b_to_human(4*2**30*form.c_cores.data), 4*2**30*form.c_cores.data, b_to_human(field.data)))

    def validate_n_port(form, field):
        if field.data < form.c_instances.data:
            raise validators.ValidationError(
                "Network ports should at least be as much as the number of instances (%d)" % form.c_instances.data)
    def validate_c_instances(form, field):
        if field.data > form.n_port.data:
            raise validators.ValidationError(
                "Nr. of instances should at most be as much as the number of network ports (%d)" % form.n_port.data)
