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

from .recaptcha import ChallengeGoal, GridDimensions, ImageGridChallenge
from .recaptcha import DynamicSolver, MultiCaptchaSolver, Solver
from .recaptcha import ReCaptcha, Solution
from .typing import List
from PIL import Image, ImageDraw, ImageFont

from threading import Thread
from queue import Queue
import io
import os
import random
import readline  # noqa: F401
import subprocess
import sys
import time

TYPEFACES = [
    "FreeSans",
    "LiberationSans-Regular",
    "DejaVuSans",
    "Arial",
    "arial",
]


def get_font(size: int) -> ImageFont.ImageFont:
    for typeface in TYPEFACES:
        try:
            return ImageFont.truetype(typeface, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


FONT_SIZE = 16
FONT = get_font(FONT_SIZE)


def read_indices(prompt: str, max_index: int) -> List[int]:
    while True:
        line = input(prompt)
        try:
            indices = [int(i) - 1 for i in line.split()]
        except ValueError:
            print("Invalid input.")
            continue
        if all(0 <= i < max_index for i in indices):
            return indices
        print("Numbers out of bounds.")


def draw_lines(image: Image.Image, dimensions: GridDimensions):
    draw = ImageDraw.Draw(image)

    def line(p1, p2):
        draw.line([p1, p2], fill=(255, 255, 255), width=2)

    for i in range(1, dimensions.rows):
        y = image.height * i // dimensions.rows - 1
        line((0, y), (image.width, y))

    for i in range(1, dimensions.columns):
        x = image.width * i // dimensions.columns - 1
        line((x, 0), (x, image.height))


def draw_indices(image: Image.Image, dimensions: GridDimensions):
    draw = ImageDraw.Draw(image, "RGBA")
    for i in range(dimensions.rows * dimensions.columns):
        row, column = divmod(i, dimensions.columns)
        corner = (
            image.width * column // dimensions.columns,
            image.height * (row + 1) // dimensions.rows,
        )
        text_loc = (
            corner[0] + round(FONT_SIZE / 2),
            corner[1] - round(FONT_SIZE * 1.5),
        )

        text = str(i + 1)
        text_size = FONT.getsize(text)
        draw.rectangle([
            (text_loc[0] - round(FONT_SIZE / 10), text_loc[1]), (
                text_loc[0] + text_size[0] + round(FONT_SIZE / 10),
                text_loc[1] + text_size[1] + round(FONT_SIZE / 10),
            ),
        ], fill=(0, 0, 0, 128))
        draw.text(text_loc, str(i + 1), fill=(255, 255, 255), font=FONT)


def print_temporary(string: str, file=sys.stdout):
    end = "" if file.isatty() else "\n"
    print(string, file=file, end=end, flush=True)


def clear_temporary(file=sys.stdout):
    if not file.isatty():
        return
    print("\r\x1b[K", file=file, end="", flush=True)


HAS_DISPLAY_CMD = (os.name == "posix")


def run_display_cmd():
    return subprocess.Popen(
        ["display", "-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def try_display_cmd(image: Image.Image):
    global HAS_DISPLAY_CMD
    if not HAS_DISPLAY_CMD:
        return None

    img_buffer = io.BytesIO()
    image.save(img_buffer, "png")
    img_bytes = img_buffer.getvalue()

    try:
        proc = run_display_cmd()
    except FileNotFoundError:
        HAS_DISPLAY_CMD = False
        return None

    proc.stdin.write(img_bytes)
    proc.stdin.close()
    return proc


class SolverCli:
    def __init__(self, cli: "Cli", solver: Solver):
        self.cli = cli
        self.solver = solver
        self.__image_procs = []

    def show_image(self, image):
        proc = try_display_cmd(image)
        if proc is None:
            image.show()
        else:
            self.__image_procs.append(proc)

    def hide_images(self):
        for proc in self.__image_procs:
            proc.terminate()
        self.__image_procs.clear()

    def run(self):
        self.solver.run()


class DynamicCli(SolverCli):
    def __init__(self, cli: "Cli", solver: DynamicSolver):
        super().__init__(cli, solver)
        self.image_open = False
        self.image_queue = Queue()
        self.num_pending = 0

    def run(self):
        challenge = self.solver.get_challenge()
        self.cli.handle_challenge(challenge)

        image = challenge.image
        num_rows = challenge.dimensions.rows
        num_columns = challenge.dimensions.columns
        num_tiles = challenge.dimensions.count
        draw_indices(image, challenge.dimensions)
        self.show_image(image)

        print("Take a look at the grid of tiles that just appeared. ", end="")
        print("({} rows, {} columns)".format(num_rows, num_columns))
        print("Which tiles should be selected?")
        print("(Top-left is 1; bottom-right is {}.)".format(num_tiles))
        indices = read_indices(
            "Enter numbers separated by spaces: ",
            num_tiles,
        )
        print()
        self.hide_images()
        self.select_initial(indices)
        self.new_tile_loop()
        return self.solver.finish()

    def new_tile_loop(self):
        while self.num_pending > 0:
            print_temporary("Waiting for next image...")
            index, image = self.image_queue.get()
            clear_temporary()
            self.num_pending -= 1
            self.show_image(image)

            print("Take a look at the image that just appeared.")
            accept = input(
                "Should this image be selected? [y/N] ",
            )[:1].lower() == "y"
            print()

            self.hide_images()
            if accept:
                self.select_tile(index)

    def select_initial(self, indices):
        print_temporary("Selecting images...")
        for i, index in enumerate(indices):
            if i > 0:
                # Avoid sending initial requests simultaneously.
                time.sleep(random.uniform(0.5, 1))
            self.select_tile(index)
        clear_temporary()

    def select_tile(self, index: int):
        self.num_pending += 1
        tile = self.solver.select_tile(index)

        def add_to_queue():
            self.image_queue.put((index, tile.image))

        def target():
            time.sleep(tile.delay)
            add_to_queue()

        if tile.delay > 0:
            Thread(target=target, daemon=True).start()
        else:
            target()


class MultiCaptchaCli(SolverCli):
    def __init__(self, cli: "Cli", solver: MultiCaptchaSolver):
        super().__init__(cli, solver)

    def run(self) -> Solution:
        result = self.solver.first_challenge()
        while not isinstance(result, Solution):
            if not isinstance(result, ImageGridChallenge):
                raise TypeError("Unexpected type: {}".format(type(result)))
            indices = self.handle_challenge(result)
            result = self.solver.select_indices(indices)
        return result

    def handle_challenge(self, challenge: ImageGridChallenge) -> List[int]:
        self.cli.handle_challenge(challenge)
        num_rows = challenge.dimensions.rows
        num_columns = challenge.dimensions.columns
        num_tiles = challenge.dimensions.count

        image = challenge.image
        draw_lines(image, challenge.dimensions)
        draw_indices(image, challenge.dimensions)
        self.show_image(image)

        print("Take a look at the grid of tiles that just appeared. ", end="")
        print("({} rows, {} columns)".format(num_rows, num_columns))
        print("Which tiles should be selected?")
        print("(Top-left is 1; bottom-right is {}.)".format(num_tiles))
        indices = read_indices(
            "Enter numbers separated by spaces: ",
            num_tiles,
        )
        print()
        self.hide_images()
        return indices


class Cli:
    def __init__(self, rc: ReCaptcha):
        self.rc = rc
        self._first = True

    def run(self) -> str:
        result = self.rc.first_solver()
        while not isinstance(result, str):
            solution = self.run_solver(result)
            result = self.rc.send_solution(solution)
        return result

    def run_solver(self, solver: Solver) -> Solution:
        return {
            DynamicSolver: DynamicCli,
            MultiCaptchaSolver: MultiCaptchaCli,
        }[type(solver)](self, solver).run()

    def show_goal(self, goal: ChallengeGoal):
        plain = goal.plain
        if plain:
            print("CHALLENGE OBJECTIVE: {}".format(plain))
            return
        print("WARNING: Could not determine challenge objective.")
        print("Challenge information: {}".format(goal.fallback))

    def handle_challenge(self, challenge: ImageGridChallenge):
        if not self._first:
            print("You must solve another challenge.")
            print()
        self._first = False
        self.show_goal(challenge.goal)
