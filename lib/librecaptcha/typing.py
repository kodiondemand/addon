# Copyright (C) 2021 taylor.fish <contact@taylor.fish>
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

from collections.abc import Callable, Iterable
import typing

try:
    list[int]
except Exception:
    List = typing.List
    Dict = typing.Dict
    Tuple = typing.Tuple
else:
    List = list
    Dict = dict
    Tuple = tuple

try:
    Callable[[], int]
except Exception:
    Callable = typing.Callable

try:
    Iterable[int]
except Exception:
    Iterable = typing.Iterable
