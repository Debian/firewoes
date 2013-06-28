# Copyright (C) 2013  Matthieu Caneill <matthieu.caneill@gmail.com>
#
# This file is part of Firewose.
#
# Firewose is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# unless for testing/dev, always set this to false
DEBUG = False

# we don't need csrf, currently there's no form which writes data somewhere
CSRF_ENABLED = False

# this sould be configured later, in a local configuration file
DATABASE_URI = ""

# echoes SQLAlchemy requests in standard output
SQLALCHEMY_ECHO = True

# The css used for the main design
CSS_FILE = "css/base-debian.css"

# The maximum number of elements which are displayed in the drill-down menu
SEARCH_MENU_MAX_NUMBER_OF_ELEMENTS = 10

# The maximum width of a result in the drill-down menu
SEARCH_MENU_MAX_NUMBER_OF_CHARS = 28

# The number of results to display (per default) on a search results page
SEARCH_RESULTS_OFFSET = 10

# The default theme used for rendering html
THEME = "debian"
