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

class SetQuotaForm(FlaskForm):
    c_instances = S3ITField('Nr. of Instances')
    c_cores = S3ITField('Nr. of vCores')
    c_ram = BytesField('Max Ram')


    n_port = S3ITField('Number of network ports')
    n_network = S3ITField('Number of networks')
    n_subnet = S3ITField('Number of subnets')
    n_security_group = S3ITField('Number of security groups')
    n_floatingip = S3ITField('Number of floating IPs')
    n_router = S3ITField('Number of routers')

    v_gigabytes = BytesField('Volumes: gigabytes')
    v_volumes = S3ITField('Number of volumes')

    s_bytes = BytesField('Swift bytes')

    comment = StringField("Comment", [validators.DataRequired()])
    submit = SubmitField('Set quota')

    def validate_c_ram(form, field):
        if field.data != 4*2**30*form.c_cores.data:
            raise validators.ValidationError(
                "Ram should be 4 GiB x nr.vcores, in this case: %d B instead of %d B" % (4*2**30*form.c_cores.data, field.data))

    def validate_n_port(form, field):
        if field.data < form.c_instances.data:
            raise validators.ValidationError(
                "Network ports should at least be as much as the number of instances (%d)" % form.c_instances.data)
    def validate_c_instances(form, field):
        if field.data > form.n_port.data:
            raise validators.ValidationError(
                "Nr. of instances should at most be as much as the number of network ports (%d)" % form.n_port.data)
