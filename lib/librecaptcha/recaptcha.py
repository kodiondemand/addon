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

from .errors import ChallengeBlockedError, UnknownChallengeError
from .errors import SiteUrlParseError
from .extract_strings import extract_and_save
from .typing import Dict, Iterable, List, Tuple

import requests

from collections import namedtuple
from html.parser import HTMLParser
from typing import Optional, Union
from urllib.parse import urlparse
import base64
import io
import json
import os
import os.path
import re
import sys
import time

BASE_URL = "https://www.google.com/recaptcha/api2/"
API_JS_URL = "https://www.google.com/recaptcha/api.js"
JS_URL_TEMPLATE = """\
https://www.gstatic.com/recaptcha/releases/{}/recaptcha__{}.js
"""[:-1]

STRINGS_VERSION = "0.1.0"
STRINGS_PATH = os.path.join(
    os.path.expanduser("~"), ".cache", "librecaptcha", "cached-strings",
)
CHALLENGE_GOAL_TEXT = {
    'en': 'select all',
    'it': 'seleziona tutti'
}

DYNAMIC_SELECT_DELAY = 4.5  # seconds
FIND_GOAL_SEARCH_DISTANCE = 10


def get_testing_url(url: str) -> str:
    return urlparse(url)._replace(
        scheme="http",
        netloc="localhost:55476",
    ).geturl()


if os.getenv("LIBRECAPTCHA_USE_TEST_SERVER"):
    BASE_URL = get_testing_url(BASE_URL)
    API_JS_URL = get_testing_url(API_JS_URL)
    JS_URL_TEMPLATE = get_testing_url(JS_URL_TEMPLATE)


def get_full_url(url: str) -> str:
    return BASE_URL.rstrip("/") + "/" + url.lstrip("/")


def get_rc_site_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.hostname:
        raise SiteUrlParseError("Error: Site URL has no hostname.")
    if not parsed.scheme:
        raise SiteUrlParseError("Error: Site URL has no scheme.")
    if parsed.scheme not in ["http", "https"]:
        raise SiteUrlParseError(
            "Error: Site URL has invalid scheme: {}".format(parsed.scheme),
        )
    port = parsed.port
    if port is None:
        port = {"http": 80, "https": 443}[parsed.scheme]
    return "{}://{}:{}".format(parsed.scheme, parsed.hostname, port)


def rc_base64(string: str) -> str:
    data = string
    if isinstance(string, str):
        data = string.encode()
    return base64.b64encode(data, b"-_").decode().replace("=", ".")


def load_rc_json(text: str):
    return json.loads(text.split("\n", 1)[1])


def get_meta(pmeta, probable_index: int):
    if not isinstance(pmeta, list):
        raise TypeError("pmeta is not a list: {!r}".format(pmeta))

    def matches(meta):
        return meta and isinstance(meta, list)

    if probable_index < len(pmeta):
        meta = pmeta[probable_index]
        if matches(meta):
            return meta

    for child in pmeta:
        if matches(child):
            return child
    raise RuntimeError("Could not find meta; pmeta: {!r}".format(pmeta))


def get_rresp(uvresp):
    if not isinstance(uvresp, list):
        raise TypeError("uvresp is not a list: {!r}".format(uvresp))

    for child in uvresp:
        if child and isinstance(child, list) and child[0] == "rresp":
            return child
    return None


def get_js_strings(user_agent: str, rc_version: str, lang : str = 'en') -> List[str]:
    def get_json():
        with open(STRINGS_PATH + '-' + lang) as f:
            version, text = f.read().split("\n", 1)
            if version != "{}/{}".format(STRINGS_VERSION, rc_version):
                raise OSError("Incorrect version: {}".format(version))
            return json.loads(text)

    try:
        return get_json()
    except (OSError, ValueError, json.JSONDecodeError):
        pass

    result = extract_and_save(
        url=JS_URL_TEMPLATE.format(rc_version, lang),
        path=STRINGS_PATH + '-' + lang,
        version=STRINGS_VERSION,
        rc_version=rc_version,
        user_agent=user_agent,
    )
    print(file=sys.stderr)
    return result


def get_rc_version(user_agent: str) -> str:
    match = re.search(r"/recaptcha/releases/(.+?)/", requests.get(
        API_JS_URL, headers={
            "User-Agent": user_agent,
        },
    ).text)
    if match is None:
        raise RuntimeError("Could not extract version from api.js.")
    return match.group(1)


# def get_image(data: bytes) -> Image.Image:
#     image = Image.open(io.BytesIO(data))
#     if image.mode in ["RGB", "RGBA"]:
#         return image
#     return image.convert("RGB")


def varint_encode(n: int, out: bytearray) -> bytes:
    if n < 0:
        raise ValueError("n must be nonnegative")
    while True:
        b = n & 127
        n >>= 7
        if n > 0:
            out.append(b | 128)
        else:
            out.append(b)
            break


def protobuf_encode(fields: Iterable[Tuple[int, bytes]]) -> bytes:
    result = bytearray()
    for num, value in fields:
        # Wire type of 2 indicates a length-delimited field.
        varint_encode((num << 3) | 2, result)
        varint_encode(len(value), result)
        result += value
    return bytes(result)


def format_reload_protobuf(
    rc_version: str,
    token: str,
    reason: str,
    api_key: str,
) -> bytes:
    # Note: We're not sending fields 3, 5, and 16.
    return protobuf_encode([
        (1, rc_version.encode()),
        (2, token.encode()),
        (6, reason.encode()),
        (14, api_key.encode()),
    ])


class GridDimensions(namedtuple("GridDimensions", [
    "rows",  # int
    "columns",  # int
])):
    @property
    def count(self) -> int:
        return self.rows * self.columns


Solution = namedtuple("Solution", [
    "response",
])

ImageGridChallenge = namedtuple("ImageGridChallenge", [
    "goal",  # ChallengeGoal
    "image",  # Image.Image
    "dimensions",  # GridDimensions
])

DynamicTile = namedtuple("DynamicTile", [
    "image",  # Image.Image
    "delay",  # float
])


class DynamicSolver:
    def __init__(self, recaptcha: "ReCaptcha", pmeta):
        self.rc = recaptcha
        self.selections = []
        meta = get_meta(pmeta, 1)
        self.meta = meta
        self.tile_index_map = list(range(self.num_tiles))
        self.last_request_map = [0] * self.num_tiles
        self.latest_index = self.num_tiles - 1
        self.challenge_retrieved = False

    def get_challenge(self) -> ImageGridChallenge:
        if self.challenge_retrieved:
            raise RuntimeError("Challenge was already retrieved")
        self.challenge_retrieved = True
        goal = self.rc.get_challenge_goal(self.meta)
        image = self._first_image()
        return ImageGridChallenge(
            goal=goal,
            image=image,
            dimensions=self.dimensions,
        )

    def select_tile(self, index: int) -> DynamicTile:
        if not self.challenge_retrieved:
            raise RuntimeError("Challenge must be retrieved first")
        image = self._replace_tile(index)
        delay = self.get_timeout(index)
        return DynamicTile(image=image, delay=delay)

    def finish(self) -> Solution:
        if not self.challenge_retrieved:
            raise RuntimeError("Challenge must be retrieved first")
        return Solution(self.selections)

    @property
    def final_timeout(self):
        return max(self.get_timeout(i) for i in range(self.num_tiles))

    @property
    def dimensions(self) -> GridDimensions:
        return GridDimensions(rows=self.meta[3], columns=self.meta[4])

    @property
    def num_tiles(self):
        return self.dimensions.count

    def get_timeout(self, index: int):
        elapsed = time.monotonic() - self.last_request_map[index]
        duration = max(DYNAMIC_SELECT_DELAY - elapsed, 0)
        return duration

    def _first_image(self):
        return self.rc.get("payload", params={
            "p": None,
            "k": None,
        }).content

    def _replace_tile(self, index: int):
        real_index = self.tile_index_map[index]
        self.selections.append(real_index)
        r = self.rc.post("replaceimage", data={
            "v": None,
            "c": None,
            "ds": "[{}]".format(real_index),
        })

        self.last_request_map[index] = time.monotonic()
        data = load_rc_json(r.text)
        self.latest_index += 1
        self.tile_index_map[index] = self.latest_index

        self.rc.current_token = data[1]
        self.rc.current_p = data[5]
        replacement_id = data[2][0]

        # The server might not return any image, but it seems unlikely in
        # practice. If it becomes a problem we can handle this case.
        return self.rc.get("payload", params={
            "p": None,
            "k": None,
            "id": replacement_id,
        }).content


class MultiCaptchaSolver:
    def __init__(self, recaptcha: "ReCaptcha", pmeta):
        """The current challenge."""
        self.rc = recaptcha
        self.selection_groups = []
        self.challenge_type = None
        self.id = "2"
        self.metas = list(get_meta(pmeta, 5)[0])
        self.challenge_index = -1

    def first_challenge(self) -> ImageGridChallenge:
        if self.challenge_index >= 0:
            raise RuntimeError("Already retrieved first challenge")
        return self._get_challenge(self._first_image())

    def select_indices(self, indices) -> Union[ImageGridChallenge, Solution]:
        if self.challenge_index < 0:
            raise RuntimeError("First challenge wasn't retrieved")
        self.selection_groups.append(list(sorted(indices)))
        if not self.metas:
            return Solution(self.selection_groups)
        return self._get_challenge(self._replace_image())

    def _get_challenge(self, image):
        self.challenge_index += 1
        meta = self.metas.pop(0)
        dimensions = GridDimensions(rows=meta[3], columns=meta[4])
        goal = self.rc.get_challenge_goal(meta)
        return ImageGridChallenge(
            goal=goal,
            image=image,
            dimensions=dimensions,
        )

    def _first_image(self):
        return self.rc.get("payload", params={
            "c": self.rc.current_token,
            "k": self.rc.api_key,
        }).content

    def _replace_image(self):
        selections = self.selection_groups[-1]
        r = self.rc.post("replaceimage", data={
            "v": None,
            "c": self.rc.current_token,
            "ds": json.dumps([selections], separators=",:"),
        })

        data = load_rc_json(r.text)
        self.rc.current_token = data[1]

        prev_p = self.rc.current_p
        self.rc.current_p = data[5]

        prev_id = self.id
        self.id = (data[2] or [None])[0]

        return self.rc.get("payload", params={
            "p": prev_p,
            "k": None,
            "id": prev_id,
        }).content


Solver = Union[DynamicSolver, MultiCaptchaSolver]


class ChallengeGoal(namedtuple("ChallengeGoal", [
    "raw",  # Optional[str]
    "meta",
])):
    @property
    def plain(self) -> Optional[str]:
        if self.raw is None:
            return None
        return self.raw.replace("<strong>", "").replace("</strong>", "")

    @property
    def fallback(self) -> str:
        return json.dumps(self.meta)


class ReCaptcha:
    def __init__(self, api_key, site_url, user_agent, debug=False,
                 make_requests=True, lang = 'en'):
        self.api_key = api_key
        self.site_url = get_rc_site_url(site_url)
        self.debug = debug
        self.co = rc_base64(self.site_url)

        self.first_token = None
        self.current_token = None
        self.current_p = None
        self.user_agent = user_agent

        self.js_strings = None
        self.rc_version = None

        self.language = lang

        if make_requests:
            self.rc_version = get_rc_version(self.user_agent)
            self.js_strings = get_js_strings(self.user_agent, self.rc_version, self.language)
        self.solver_index = -1


    def first_solver(self) -> Solver:
        if self.solver_index >= 0:
            raise RuntimeError("First solver was already retrieved")
        self._request_first_token()
        rresp = self._get_first_rresp()
        return self._get_solver(rresp)

    def send_solution(self, solution: Solution) -> Union[Solver, str]:
        if self.solver_index < 0:
            raise RuntimeError("First solver wasn't retrieved")
        uvtoken, rresp = self._verify(solution.response)
        if rresp is not None:
            return self._get_solver(rresp)
        if not uvtoken:
            raise RuntimeError("Got neither uvtoken nor new rresp.")
        return uvtoken

    def debug_print(self, *args, **kwargs):
        if not self.debug:
            return
        if len(args) == 1 and callable(args[0]):
            args = (args[0](),)
        print(*args, file=sys.stderr, **kwargs)

    def get_challenge_goal(self, meta) -> ChallengeGoal:
        raw = self.find_challenge_goal_text(meta[0])
        return ChallengeGoal(raw=raw, meta=meta)

    def find_challenge_goal_text(self, id: str, raw=False) -> str:
        start = 0
        matching_strings = []

        def try_find():
            nonlocal start
            index = self.js_strings.index(id, start)
            for i in range(FIND_GOAL_SEARCH_DISTANCE):
                next_str = self.js_strings[index + i + 1]
                if re.search(r"\b{}\b".format( CHALLENGE_GOAL_TEXT[ self.language] ) , next_str, re.I):
                    matching_strings.append((i, index, next_str))
            start = index + FIND_GOAL_SEARCH_DISTANCE + 1

        try:
            while True:
                try_find()
        except (ValueError, IndexError):
            pass

        try:
            goal = min(matching_strings)[2]
        except ValueError:
            return None
        return goal

    def get_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        headers = headers or {}
        updates = {}
        if "User-Agent" not in headers:
            updates["User-Agent"] = self.user_agent
        if updates:
            headers = dict(headers)
            headers.update(updates)
        return headers

    def get(self, url, *, params=None, headers=None, allow_errors=None,
            **kwargs):
        if params is None:
            params = {"k": None, "v": None}
        if params.get("k", "") is None:
            params["k"] = self.api_key
        if params.get("v", "") is None:
            params["v"] = self.rc_version
        if params.get("p", "") is None:
            params["p"] = self.current_p
        headers = self.get_headers(headers)

        r = requests.get(
            get_full_url(url), params=params, headers=headers,
            **kwargs,
        )
        self.debug_print(lambda: "[http] [get] {}".format(r.url))
        if not (allow_errors is True or r.status_code in (allow_errors or {})):
            r.raise_for_status()
        return r

    def post(self, url, *, params=None, data=None, headers=None,
             allow_errors=None, no_debug_response=False, **kwargs):
        if params is None:
            params = {"k": None}
        if data is None:
            data = {"v": None}
        if params.get("k", "") is None:
            params["k"] = self.api_key
        if isinstance(data, dict) and data.get("v", "") is None:
            data["v"] = self.rc_version
        if isinstance(data, dict) and data.get("c", "") is None:
            data["c"] = self.current_token
        headers = self.get_headers(headers)

        r = requests.post(
            get_full_url(url), params=params, data=data, headers=headers,
            **kwargs,
        )
        self.debug_print(lambda: "[http] [post] {}".format(r.url))
        self.debug_print(lambda: "[http] [post] [data] {!r}".format(data))
        if not no_debug_response:
            self.debug_print(
                lambda: "[http] [post] [response] {}".format(r.text),
            )
        if not (allow_errors is True or r.status_code in (allow_errors or {})):
            r.raise_for_status()
        return r

    def _request_first_token(self):
        class Parser(HTMLParser):
            def __init__(p_self):
                p_self.token = None
                super().__init__()

            def handle_starttag(p_self, tag, attrs):
                attrs = dict(attrs)
                if attrs.get("id") == "recaptcha-token":
                    p_self.token = attrs.get("value")

        # Note: We're not sending "cb".
        text = self.get("anchor", params={
            "ar": "1",
            "k": None,
            "co": self.co,
            "hl": "en",
            "v": None,
            "size": "normal",
            "sa": "action",
        }).text
        parser = Parser()
        parser.feed(text)

        if not parser.token:
            raise RuntimeError(
                "Could not get first token. Response:\n{}".format(text),
            )
        self.current_token = parser.token

    def _verify(self, response):
        response_text = json.dumps({"response": response}, separators=",:")
        response_b64 = rc_base64(response_text)

        self.debug_print("Sending verify request...")
        # Note: We're not sending "t", "ct", and "bg".
        r = self.post("userverify", data={
            "v": None,
            "c": None,
            "response": response_b64,
        })

        uvresp = load_rc_json(r.text)
        self.debug_print(lambda: "Got verify response: {!r}".format(uvresp))
        rresp = get_rresp(uvresp)
        uvresp_token = uvresp[1]
        return (uvresp_token, rresp)

    def _get_first_rresp(self):
        self.debug_print("Getting first rresp...")
        r = self.post("reload", data=format_reload_protobuf(
            rc_version=self.rc_version,
            token=self.current_token,
            reason="fi",
            api_key=self.api_key,
        ), headers={
            "Content-Type": "application/x-protobuffer",
        })
        rresp = load_rc_json(r.text)
        self.debug_print(lambda: "Got first rresp: {!r}".format(rresp))
        return rresp

    def _get_solver(self, rresp) -> Solver:
        self.solver_index += 1
        challenge_type = rresp[5]
        self.debug_print(lambda: "Challenge type: {}".format(challenge_type))
        pmeta = rresp[4]
        self.debug_print(lambda: "pmeta: {}".format(pmeta))
        self.current_token = rresp[1]
        self.current_p = rresp[9]
        self.debug_print(
            lambda: "Current token: {}".format(self.current_token),
        )

        solver_class = {
            "dynamic": DynamicSolver,
            "multicaptcha": MultiCaptchaSolver,
        }.get(challenge_type)

        if solver_class is not None:
            return solver_class(self, pmeta)

        if challenge_type in ["default", "doscaptcha"]:
            raise ChallengeBlockedError(challenge_type)
        raise UnknownChallengeError(challenge_type)
