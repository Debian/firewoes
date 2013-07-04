# The settings defined here will override those defined in webconfig.py

# database
DATABASE_URI = "postgresql://matthieu:matthieu@localhost:5432/firewose"

# use your own themes! in web/app/frontend/themes
# THEME = "foo"

# the url pattern used to generate urls to point on source code
DEBIAN_SOURCES_URL = "http://sources.debian.net/src/{package}/{version}-{release}/{path}?msg={message}&hl={lines_range}#L{anchor}"

# the url pattern used for embedded source code
DEBIAN_EMBEDDED_SOURCES_URL = "http://sources.debian.net/embedded/{package}/{version}-{release}/{path}?msg={message}&hl={lines_range}#L{anchor}"
