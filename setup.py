from setuptools import setup

setup(
    name='sc-admin-dashboard',
    packages=['scadmin', 'scadmin.auth', 'scadmin.forms', 'scadmin.models', 'scadmin.views'],
    include_package_data=True,
    install_requires=[
        'Flask',
        'wtforms',
        'Flask-Wtf',
        'Flask-Bootstrap',
        'Flask-Nav',
        'robobrowser',
        'python-keystoneclient',
        'python-novaclient',
        'python-cinderclient',
        'python-neutronclient',
        'python-swiftclient',
    ],
)
