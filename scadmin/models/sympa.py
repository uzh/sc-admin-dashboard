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

import robobrowser
from flask import session, current_app as app

from scadmin import config


class ML:
    def __init__(self):
        self.url_base = '%s/sympa' % config.SYMPA_URL
        self.url_review = '{}?sortby=email&action=review&list={}&size={}'.format(
            self.url_base, config.SYMPA_LIST, config.SYMPA_SIZE)
        self.url_remove = self.url_review
        # SYMPA(6.2.32): changed url from 'add_request' to 'import'
        self.url_add = '%s/import/%s' % (self.url_base, config.SYMPA_LIST)
        self.br = robobrowser.RoboBrowser(user_agent='Chrome', parser='html.parser')
        self.br.session.verify = False
        app.logger.warning("Disabling SSL verification to access %s", self.url_base)
        self.logged_in = False

    def login(self):
        """Login to the mailing list"""
        self.br.open(self.url_base)

        form = self.br.get_forms()[1]

        form['email'] = config.SYMPA_USERNAME
        form['passwd'] = config.SYMPA_PASSWORD

        self.br.submit_form(form)
        self.logged_in = True

    def open(self, url):
        if not self.logged_in:
            self.login()
        self.br.open(url)
        
    def list(self, allusers=False):
        """Return a list of email addresses subscribed to the mailing list"""
        subscribers = []
        self.open(self.url_review)

        for row in self.br.find_all('tr'):
            email = row.find('a').text
            if email and email.strip():
                subscribers.append(email.lower())

        if allusers:
            subscribers.extend([i[0] for i in config.SYMPA_EMAIL_MAPPINGS])

        return subscribers

    def missing_and_exceeding(self, users):
        users = [u.lower() for u in users if u and u.strip()]
        subscribers = self.list(allusers=True)
        missing = set(users).difference(subscribers)
        exceeding = set(subscribers).difference(users)
        return missing, exceeding

    def add(self, users, quiet=True):
        """Add all email addresses listed in `users to the mailing list.

        Returns two lists `info`, `err` containins info and error messages
        """
        self.open(self.url_add)

        form = self.br.get_forms()[1]
        form['dump'] = str.join('\n', [u for u in users if u and  '@' in u])

        # SYMPA(6.2.32): changed back quietly to quiet.
        if quiet:
            form['quiet'].value = ['quiet']
        
        # SYMPA(6.2.32): added mandatory form value.
        form['action_import'].value = ['Add+subscribers']

        self.br.submit_form(form)

        info, err = [], []
        if self.br.find(id='ephemeralMsg'):
            info.extend(self.br.find(id='ephemeralMsg').text.strip().splitlines())
        if self.br.find(id='ErrorMsg'):
            # S3IT issue3567: when adding an user to the mailing list
            # Sympa is returning an error, but for us this is not
            # really an error, rather an informational message, as we
            # will get this "error" every time we add an user to more
            # than one tenant. Let's therefore add it to info instead.
            #
            # To identify if this is actually an error or not, we need
            # to see if the line "is already subscribed to the list"
            # is present in the error message, and check if this is
            # the case for *all* the email addresses
            errorlines = [i.strip() for i in self.br.find(id='ErrorMsg').text.strip().splitlines()]
            for line in errorlines[:]:
                # SYMPA(6.2.32): "new" English translation.
                if 'is already subscriber of list' in line:
                    info.append(line)
                    errorlines.remove(line)
            # If all the users were already subscribed, then the
            # errorlines list will only contain one line. In all other
            # cases, we extend the err list.
            # SYMPA(6.2.32): 'ErrorMsg' now returns an extra empty line.
            if errorlines != ['ERROR (import)  -', '']:
                err.extend(errorlines)

        return info, err


    def remove(self, users, quiet=True):
        """Remove all email addresses listed in `users from the mailing list.

        Returns two lists `info`, `err` containins info and error messages
        """
        self.open(self.url_remove)

        form = self.br.get_forms()[4]
        form['email'].value = users

        if quiet:
            form['quiet'].value = ['on']

        self.br.submit_form(form)

        info, err = [], []
        if self.br.find(id='ephemeralMsg'):
            info.extend(self.br.find(id='ephemeralMsg').text.strip().splitlines())
        if self.br.find(id='ErrorMsg'):
            err.extend(self.br.find(id='ErrorMsg').text.strip().splitlines())

        return info, err
