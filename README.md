# sc-admin-dashboard

This Flask-based dashboard is a proof-of-concept of a dashboard to
provide some functionalities to Science Cloud users and operators.

## For S3IT operators

* Create projects
* Update project quota
* add/remove users to projects

## For ScienceCloud Project Admin

* Add users to their project
* request for quota change

## for ScienceCloud users

* Display detailed usage (as in the monthly report)
* Check remaining capacity of current flavors


# Why not Horizon?

Horizon is a big project and changes often. With the Newton release it
should be easier to implement new functionalities in Horizon, but we
are still at Liberty and we are not sure this tool will be used in
production, so we decided to make a proof-of-concept to check if the
functionalities are actually useful for our users.
