# The settings defined here will override those defined in webconfig.py

# database
DATABASE_URI = "postgresql://matthieu:matthieu@localhost:5432/firewose"

# use your own themes! in web/app/frontend/themes
# THEME = "foo"

# the url pattern used to generate urls to point on source code
SOURCE_CODE_URL = "http://sources.debian.net/src/{package}/{version}-{release}/{path}?msg={anchor}:error:{message}&hl={lines_range}#L{anchor}"
