========
Firewoes
========

Firewoes is intended to be a web user interface for Firehose.

Dependencies
============

Debian dependencies
-------------------

* python
* python-flask
* python-six (required by Firehose)
* postgresql (dev fast configuration: http://doc.ubuntu-fr.org/postgresql)
* python-sqlalchemy >= 0.8.1
* python-psycopg2 (required by SQLAlchemy)
* python-jinja2 >= 2.7-3 [1]
* python-debian
* python-firehose >= 0.3

[1] to use the option lstrip_block=True, for better whitespace dealing
    in templates

Python packages
---------------

(everythng is packaged in Debian for now)

Installation
============

* At least on Debian, libpq-dev is needed to install psycopg2 via pip

* Production: $ python setup.py install
* Development: $ python setup.py develop

Ruuning
=======

* With the development Flask server:
  $ export FIREWOES_CONFIG=path/to/yout/local/config.py
  $ python firewoes/web/run.py
