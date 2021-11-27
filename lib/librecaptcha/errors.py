# Copyright (C) 2019, 2021 taylor.fish <contact@taylor.fish>
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

GUI_MISSING_MESSAGE = """\
Error: Could not load the GUI. Is PyGObject installed?
Try (re)installing librecaptcha[gtk] with pip.
For more details, add the --debug option.
"""[:-1]

CHALLENGE_BLOCKED_MESSAGE = """\
Error: Unsupported challenge type: {}
Requests are most likely being blocked; see the previously displayed messages.
"""[:-1]

UNKNOWN_CHALLENGE_MESSAGE = """\
Error: Unsupported challenge type: {}
See the previously displayed messages for more information.
"""[:-1]


class UserError(Exception):
    """A user-facing exception for an expected error condition (e.g., bad
    user-supplied data). When librecaptcha is run as a program, exceptions of
    this type are shown without a traceback unless --debug is passed.
    """
    def __init__(self, message):
        super().__init__(message)

    @property
    def message(self):
        return self.args[0]

    @property
    def show_by_default(self) -> bool:
        """Whether the exception message should be shown to the user by
        default. Certain exception types may want to set this to ``False`` if a
        detailed message has already been displayed to the user.
        """
        return True


class UserExit(UserError):
    """When librecaptcha is run as a program, throwing this exception causes
    the program to terminate. The exception message is not shown by default.
    """
    def __init__(self, message="Program terminated."):
        super().__init__(message)


class GtkImportError(ImportError):
    def __str__(self) -> str:
        return GUI_MISSING_MESSAGE


class SiteUrlParseError(ValueError):
    pass


class UnsupportedChallengeError(Exception):
    def __init__(self, challenge_type: str):
        self.challenge_type = challenge_type

    def __str__(self):
        return "Error: Unsupported challenge type: {}".format(
            self.challenge_type,
        )


class ChallengeBlockedError(UnsupportedChallengeError):
    def __str__(self) -> str:
        return CHALLENGE_BLOCKED_MESSAGE.format(self.challenge_type)

    @property
    def show_by_default(self) -> bool:
        # A detailed message is already shown in `librecaptcha.get_token()`.
        return False


class UnknownChallengeError(UnsupportedChallengeError):
    def __str__(self) -> str:
        return UNKNOWN_CHALLENGE_MESSAGE.format(self.challenge_type)

    @property
    def show_by_default(self) -> bool:
        # A detailed message is already shown in `librecaptcha.get_token()`.
        return False
