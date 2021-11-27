# Copyright (C) 2017, 2019, 2021 taylor.fish <contact@taylor.fish>
#
# This file is part of librecaptcha.
#
# librecaptcha is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# librecaptcha is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with librecaptcha.  If not, see <https://www.gnu.org/licenses/>.

from . import cli
from .errors import ChallengeBlockedError, UnknownChallengeError
from .errors import GtkImportError
from .recaptcha import ReCaptcha

__version__ = "0.7.4-dev"

GUI_MISSING_MESSAGE = """\
Error: Could not load the GUI. Is PyGObject installed?
Try (re)installing librecaptcha[gtk] with pip.
For more details, add the --debug option.
"""

CHALLENGE_BLOCKED_MESSAGE = """\
ERROR: Received challenge type "{}".

This is usually an indication that reCAPTCHA requests from this network are
being blocked.

Try installing Tor (the full installation, not just the browser bundle) and
running this program over Tor with the "torsocks" command.

Alternatively, try waiting a while before requesting another challenge over
this network.
"""

UNKNOWN_CHALLENGE_MESSAGE = """\
ERROR: Received unrecognized challenge type "{}".
Currently, the only supported challenge types are "dynamic" and "multicaptcha".
Please file an issue if this problem persists.
"""


def _get_gui():
    from . import gui
    return gui


def has_gui():
    try:
        _get_gui()
    except GtkImportError:
        return False
    return True


def get_token(
    api_key: str,
    site_url: str,
    user_agent: str, *,
    gui=False,
    debug=False,
) -> str:
    ui = (_get_gui().Gui if gui else cli.Cli)(ReCaptcha(
        api_key=api_key,
        site_url=site_url,
        user_agent=user_agent,
        debug=debug,
    ))
    try:
        return ui.run()
    except ChallengeBlockedError as e:
        print(CHALLENGE_BLOCKED_MESSAGE.format(e.challenge_type))
        raise
    except UnknownChallengeError as e:
        print(UNKNOWN_CHALLENGE_MESSAGE.format(e.challenge_type))
        raise
