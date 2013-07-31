import os

os.environ["FIREWOES_CONFIG"] = "/home/matthieu/work/debian/firewoes/config/webconfig_local.example.py"

from firewoes.web.app import app as application
