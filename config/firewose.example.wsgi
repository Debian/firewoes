import os

os.environ["FIREWOSE_CONFIG"] = "/home/matthieu/work/debian/firewose/config/webconfig_local.example.py"

from firewose.web.app import app as application
