# Test variables will override webconfig_defaults.py

TESTING = True

# a little bit too verbose for testing
SQLALCHEMY_ECHO = False

# you should use another database, as it will empty and fill it again
DATABASE_URI = "postgresql://matthieu:matthieu@localhost:5432/firewose_test"
