# Copyright (C) 2019 cyclopsian
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

from .errors import UserExit, GtkImportError
from .recaptcha import ChallengeGoal, GridDimensions, ImageGridChallenge
from .recaptcha import DynamicSolver, MultiCaptchaSolver, Solver
from .recaptcha import ReCaptcha, Solution
from .typing import Callable, Iterable, List
from PIL import Image

from collections import namedtuple
from typing import Any, Optional, Union
import html
import re
import sys
import threading

try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
except ImportError as e:
    raise GtkImportError from e


def tiles_from_image(
    image: Image.Image,
    dimensions: GridDimensions,
) -> Iterable[Image.Image]:
    tile_width = image.width // dimensions.columns
    tile_height = image.height // dimensions.rows
    for row in range(0, dimensions.rows):
        for column in range(0, dimensions.columns):
            left = tile_width * column
            top = tile_height * row
            right = left + tile_width
            bottom = top + tile_height
            yield image.crop((left, top, right, bottom))


def image_to_gdk_pixbuf(image: Image.Image):
    width, height = image.size
    image_bytes = GLib.Bytes(image.tobytes())
    has_alpha = (image.mode == "RGBA")
    bpp = 4 if has_alpha else 3
    return GdkPixbuf.Pixbuf.new_from_bytes(
        image_bytes, GdkPixbuf.Colorspace.RGB,
        has_alpha, 8, width, height, width * bpp,
    )


CSS = """\
grid {
    margin-top: 1px;
    margin-left: 1px;
}

.challenge-button {
    margin: 0;
    padding: 0;
    border-radius: 0;
    box-shadow: none;
    -gtk-icon-shadow: none;
    border-width: 1px;
    margin-top: -1px;
    margin-left: -1px;
}

.challenge-check, .challenge-header {
    margin-left: 1px;
    margin-top: 1px;
    color: @theme_selected_fg_color;
    background-image: linear-gradient(
        @theme_selected_bg_color,
        @theme_selected_bg_color
    );
}

.challenge-header {
    padding: 12px;
}

.challenge-check {
    border-radius: 50%;
}
"""


def load_css():
    global CSS
    if CSS is None:
        return

    css_provider = Gtk.CssProvider.new()
    css_provider.load_from_data(CSS.encode())
    CSS = None
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


Dispatch = Callable[[Any], None]


class DynamicTile:
    def __init__(self, dispatch: Dispatch):
        self.dispatch = dispatch
        self.pres: Optional["DynamicTilePres"] = None
        self.box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.inner = None
        self.inner_size = (0, 0)  # (width, height)

    @property
    def widget(self):
        return self.box

    def update(self, pres: "DynamicTilePres"):
        if pres.same(self.pres):
            return
        if self.inner is not None:
            self.box.remove(self.inner)
        self.make_inner(pres.image)
        self.box.show_all()
        self.pres = pres

    def make_inner(self, image: Image.Image):
        if image is None:
            self.make_spinner()
            return

        button = Gtk.Button.new()
        button.get_style_context().add_class("challenge-button")
        button.add(Gtk.Image.new_from_pixbuf(image_to_gdk_pixbuf(image)))
        button.connect("clicked", lambda _: self.pres.on_click(self.dispatch))

        def on_size_allocate(obj, size):
            self.inner_size = (size.width, size.height)
        button.connect("size-allocate", on_size_allocate)
        self.set_inner(button)

    def make_spinner(self):
        width, height = (max(n, 32) for n in self.inner_size)
        spinner = Gtk.Spinner.new()
        spinner.set_size_request(32, 32)
        left = (width - 32) // 2
        top = (height - 32) // 2
        spinner.set_margin_top(top)
        spinner.set_margin_start(left)
        spinner.set_margin_bottom(height - top - 32)
        spinner.set_margin_end(width - left - 32)
        self.set_inner(spinner)
        spinner.start()
        return spinner

    def set_inner(self, widget):
        self.inner = widget
        self.box.add(self.inner)


class MultiCaptchaTile:
    def __init__(self, dispatch: Dispatch):
        self.dispatch = dispatch
        self.pres: Optional["MultiCaptchaTilePres"] = None

        self.image = Gtk.Image.new()
        self.check = self.make_check()
        self.fixed = Gtk.Fixed.new()
        self.fixed.put(self.image, 0, 0)
        self.fixed.put(self.check, 0, 0)

        self.button = Gtk.ToggleButton.new()
        self.button.get_style_context().add_class("challenge-button")
        self.button.add(self.fixed)
        self.toggle_id = None

        self.pixbuf = None
        self.small_pixbuf = None
        self.button.show_all()

    @property
    def widget(self):
        return self.button

    def update(self, pres: "MultiCaptchaTilePres"):
        if pres.same(self.pres):
            return None

        if self.pres is None:
            def on_toggle(obj):
                self._set_active(not obj.get_active())
                self.pres.on_click(self.dispatch)
            self.toggle_id = self.button.connect("toggled", on_toggle)

        if (self.pres and self.pres.image) is not pres.image:
            self.pixbuf = image_to_gdk_pixbuf(pres.image)
            width = self.pixbuf.get_width()
            height = self.pixbuf.get_height()
            self.image.set_size_request(width, height)
            self.small_pixbuf = self.pixbuf.scale_simple(
                width * 0.9, height * 0.9, GdkPixbuf.InterpType.BILINEAR,
            )

        if pres.selected:
            self.check.show()
            self.image.set_from_pixbuf(self.small_pixbuf)
        else:
            self.check.hide()
            self.image.set_from_pixbuf(self.pixbuf)

        self._set_active(pres.selected)
        self.pres = pres

    def make_check(self):
        check = Gtk.Image.new_from_icon_name(
            "object-select-symbolic", Gtk.IconSize.DND,
        )
        check.set_pixel_size(24)
        check.set_no_show_all(True)
        check.get_style_context().add_class("challenge-check")
        return check

    def _set_active(self, selected: bool):
        self.button.handler_block(self.toggle_id)
        self.button.set_active(selected)
        self.button.handler_unblock(self.toggle_id)


class ChallengeTile:
    def __init__(self, dispatch: Dispatch):
        self.dispatch = dispatch
        self.box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.tile = None

    @property
    def widget(self):
        return self.box

    def update(self, pres: "TilePres"):
        tile_type = {
            DynamicTilePres: DynamicTile,
            MultiCaptchaTilePres: MultiCaptchaTile,
        }[type(pres)]

        if type(self.tile) is not tile_type:
            if self.tile is not None:
                self.box.remove(self.tile.widget)
            self.tile = tile_type(self.dispatch)
            self.box.add(self.tile.widget)
            self.box.show_all()
        self.tile.update(pres)


class ImageGridChallengeDialog:
    def __init__(self, dispatch: Dispatch):
        self.dispatch = dispatch
        self.pres: Optional["ImageGridChallengePres"] = None

        self.dialog = Gtk.Dialog.new()
        self.dialog.set_resizable(False)
        self.dialog.set_title("librecaptcha")
        self.dialog.set_icon_name("view-refresh-symbolic")

        self.verify = self.dialog.add_button("", Gtk.ResponseType.OK)
        self.verify.get_style_context().add_class("suggested-action")

        def on_click(obj):
            # This will get reset in `self.update()`, but it prevents multiple
            # clicks from taking effect if the UI temporarily pauses.
            self.verify.set_sensitive(False)
        self.verify.connect("clicked", on_click)

        self.header = Gtk.Label.new("")
        self.header.set_xalign(0)
        self.header.get_style_context().add_class("challenge-header")

        self.content = self.dialog.get_content_area()
        self.content.set_spacing(6)
        for dir in ["start", "end", "top", "bottom"]:
            getattr(self.content, "set_margin_" + dir)(6)
        self.content.pack_start(self.header, False, False, 0)

        self.grid = None
        self.tiles = []
        self.dialog.show_all()

    def run(self) -> bool:
        """Returns ``True`` on success, or ``False`` if the dialog was closed
        without activating the default button.
        """
        return self.dialog.run() == Gtk.ResponseType.OK

    def destroy(self):
        self.dialog.destroy()

    def update(self, pres: "ImageGridChallengePres"):
        if pres.same(self.pres):
            return

        dimensions = pres.dimensions
        if dimensions != (self.pres and self.pres.dimensions):
            if self.grid is not None:
                self.content.remove(self.grid)
            self.grid = self.make_grid(dimensions)
            self.grid.show_all()
            self.content.pack_start(self.grid, True, True, 0)

        if not pres.same_goal(self.pres):
            self.header.set_markup(pres.goal)

        if not pres.same_verify_label(self.pres):
            self.verify.set_label(pres.verify_label)
        self.verify.set_sensitive(pres.is_verify_enabled)

        for tile, tile_pres in zip(self.tiles, pres.tiles):
            tile.update(tile_pres)
        self.pres = pres

    def make_grid(self, dimensions: GridDimensions):
        grid = Gtk.Grid.new()
        self.tiles = []
        for row in range(0, dimensions.rows):
            for column in range(0, dimensions.columns):
                tile = ChallengeTile(self.dispatch)
                grid.attach(tile.widget, column, row, 1, 1)
                self.tiles.append(tile)
        return grid


def format_goal(goal: ChallengeGoal) -> str:
    if goal.raw is None:
        return goal.fallback
    match = re.fullmatch(r"(.*)<strong>(.*)</strong>(.*)", goal.raw)
    if not match:
        return html.escape(goal.raw)
    groups = match.groups()
    return '{}<span size="xx-large">{}</span>{}'.format(
        *map(html.escape, [
            groups[0] and groups[0] + "\n",
            groups[1],
            groups[2],
        ]),
    )


def format_goal_with_note(goal: ChallengeGoal, note: str) -> str:
    return "{}\n{}".format(format_goal(goal), note)


# Messages
Start = namedtuple("Start", [])
FinishChallenge = namedtuple("FinishChallenge", [])
SelectTile = namedtuple("SelectTile", [
    "index",  # int
])
ReplaceTile = namedtuple("ReplaceTile", [
    "index",  # int
    "image",  # Image.Image
])
SetState = namedtuple("SetState", [
    "state",  # State
])
SetNextChallenge = namedtuple("NextChallenge", [
    "challenge",  # ImageGridChallenge
])


def gtk_run(f: Callable[[], Any]):
    old_excepthook = sys.excepthook

    def excepthook(*args, **kwargs):
        old_excepthook(*args, **kwargs)
        sys.exit(1)

    try:
        sys.excepthook = excepthook
        return f()
    finally:
        sys.excepthook = old_excepthook


class Gui:
    def __init__(self, rc: ReCaptcha):
        self.store = Store(self.final_dispatch, rc)
        self.view = ImageGridChallengeDialog(self.dispatch)
        self.update_pending = False

    @property
    def dispatch(self) -> Dispatch:
        return self.store.dispatch

    @property
    def state(self) -> Optional["State"]:
        return self.store.state

    def final_dispatch(self, msg):
        self.store.state = reduce_state(self.state, msg)
        if not self.update_pending:
            self.update_pending = True
            GLib.idle_add(self._update)

    def _update(self):
        self.update_pending = False
        pres = self.pres
        if pres is not None:
            self.view.update(pres)
        return False

    def run(self) -> str:
        load_css()
        self.dispatch(Start())
        try:
            while self.token is None:
                if not gtk_run(self.view.run):
                    raise UserExit
                self.dispatch(FinishChallenge())
        finally:
            self.view.destroy()
            while Gtk.events_pending():
                Gtk.main_iteration()
        return self.token

    @property
    def pres(self) -> Optional["ImageGridChallengePres"]:
        return pres(self.state)

    @property
    def token(self) -> Optional[str]:
        if isinstance(self.state, str):
            return self.state
        return None


class Store:
    state: Optional["State"]
    dispatch: Dispatch

    def __init__(self, final_dispatch: Dispatch, rc: ReCaptcha):
        self.state = None
        middleware = WarningMiddleware(self, final_dispatch)
        middleware = SolverMiddleware(self, middleware.dispatch, rc)
        self.dispatch = middleware.dispatch


def pres(state: "State") -> Optional["ImageGridChallengePres"]:
    return {
        DynamicState: DynamicPres,
        MultiCaptchaState: MultiCaptchaPres,
    }.get(type(state), lambda _: None)(state)


def state_from_solver(solver: Solver) -> "SolverState":
    return {
        DynamicSolver: DynamicState,
        MultiCaptchaSolver: MultiCaptchaState,
    }[type(solver)].from_new_solver(solver)


# Returns the new state after applying `msg`.
def reduce_state(state: "State", msg) -> "State":
    if type(msg) is SetState:
        return msg.state
    if type(state) in SOLVER_STATE_TYPES:
        return state.reduce(msg)
    return state


class SolverMiddleware:
    def __init__(self, store: Store, next: Dispatch, rc: ReCaptcha):
        self.store = store
        self.next = next
        self.rc = rc
        self.solver = None
        self._select_tile_lock = threading.Lock()

    def dispatch(self, msg):
        if type(msg) is Start:
            self.solver = self.rc.first_solver()
            self.next(SetState(state_from_solver(self.solver)))
        elif isinstance(self.solver, DynamicSolver):
            self.dispatch_dynamic(msg)
        elif isinstance(self.solver, MultiCaptchaSolver):
            self.dispatch_multicaptcha(msg)
        else:
            self.next(msg)

    def dispatch_dynamic(self, msg):
        if type(msg) is FinishChallenge:
            if self.store.state.num_waiting <= 0:
                self.send_solution(self.solver.finish())
        elif type(msg) is SelectTile:
            self.dynamic_select_tile(msg)
        else:
            self.next(msg)

    def dynamic_select_tile(self, msg: SelectTile):
        def select_tile():
            with self._select_tile_lock:
                tile = self.solver.select_tile(msg.index)

            def replace():
                self.next(ReplaceTile(index=msg.index, image=tile.image))
                return False
            GLib.timeout_add(round(tile.delay * 1000), replace)

        self.next(ReplaceTile(index=msg.index, image=None))
        if self.store.state.num_waiting <= 0:
            raise RuntimeError("num_waiting should be greater than 0")
        threading.Thread(target=select_tile, daemon=True).start()

    def dispatch_multicaptcha(self, msg):
        if type(msg) is FinishChallenge:
            self.multicaptcha_finish()
        else:
            self.next(msg)

    def multicaptcha_finish(self):
        result = self.solver.select_indices(self.store.state.indices)
        if isinstance(result, Solution):
            self.send_solution(result)
        elif isinstance(result, ImageGridChallenge):
            self.next(SetNextChallenge(result))
        else:
            raise TypeError("Unexpected type: {}".format(type(result)))

    def send_solution(self, solution: Solution):
        self.solver = None
        result = self.rc.send_solution(solution)
        if not isinstance(result, str):
            self.solver = result
            result = state_from_solver(result)
        self.next(SetState(result))


class WarningMiddleware:
    def __init__(self, store: Store, next: Dispatch):
        self.next = next

    def dispatch(self, msg):
        if type(msg) is SetNextChallenge:
            self.check_goal(msg.challenge.goal)
        elif type(msg) is SetState:
            if type(msg.state) in SOLVER_STATE_TYPES:
                self.check_goal(msg.state.challenge.goal)
        self.next(msg)

    def check_goal(self, goal: ChallengeGoal):
        if goal.raw is not None:
            return
        msg = "WARNING: Could not determine challenge objective in: {}"
        print(msg.format(goal.fallback), file=sys.stderr)


class DynamicState(namedtuple("DynamicState", [
    "challenge",  # Challenge
    "tile_images",  # List[Optional[Image.Image]]
    "num_waiting",  # int
])):
    @classmethod
    def from_new_solver(cls, solver: Solver):
        challenge = solver.get_challenge()
        tiles = list(tiles_from_image(challenge.image, challenge.dimensions))
        return cls(
            challenge=challenge,
            tile_images=tiles,
            num_waiting=0,
        )

    def replace_tile(
        self,
        index: int,
        image: Optional[Image.Image],
    ) -> "DynamicState":
        old_image = self.tile_images[index]
        num_waiting = self.num_waiting
        if (old_image is None) != (image is None):
            num_waiting += 1 if image is None else -1

        images = list(self.tile_images)
        images[index] = image
        return self._replace(tile_images=images, num_waiting=num_waiting)

    def reduce(self, msg) -> "DynamicState":
        if type(msg) is ReplaceTile:
            return self.replace_tile(msg.index, msg.image)
        return self


class MultiCaptchaState(namedtuple("MultiCaptchaState", [
    "challenge",  # Challenge
    "tile_images",  # List[Image.Image]
    "selected",  # List[bool]
])):
    @classmethod
    def from_new_solver(cls, solver: Solver):
        return cls.from_challenge(solver.first_challenge())

    @classmethod
    def from_challenge(cls, challenge: ImageGridChallenge):
        tiles = list(tiles_from_image(challenge.image, challenge.dimensions))
        return cls(
            challenge=challenge,
            tile_images=tiles,
            selected=([False] * challenge.dimensions.count),
        )

    def toggle_tile(self, index: int) -> "MultiCaptchaState":
        selected = list(self.selected)
        selected[index] ^= True
        return self._replace(selected=selected)

    @property
    def indices(self) -> List[int]:
        return [i for i, selected in enumerate(self.selected) if selected]

    @property
    def any_selected(self) -> bool:
        return any(self.selected)

    def same_any_selected(self, other) -> bool:
        return type(self) is type(other) and (
            self.selected is other.selected or
            self.any_selected is other.any_selected
        )

    def reduce(self, msg) -> "MultiCaptchaState":
        if type(msg) is SelectTile:
            return self.toggle_tile(msg.index)
        if type(msg) is SetNextChallenge:
            return self.from_challenge(msg.challenge)
        return self


SOLVER_STATE_TYPES = (MultiCaptchaState, DynamicState)
SolverState = Union[SOLVER_STATE_TYPES]
State = Union[SolverState, str, None]


class ImageGridChallengePres:
    def __init__(self, state: SolverState):
        self.state = state

    def same(self, other) -> bool:
        return (
            type(self) is type(other) and
            self.state is other.state
        )

    @property
    def dimensions(self) -> GridDimensions:
        return self.state.challenge.dimensions

    @property
    def goal(self) -> str:
        raise NotImplementedError

    def same_goal(self, other) -> bool:
        raise NotImplementedError

    @property
    def verify_label(self) -> str:
        return "Ver_ify"

    def same_verify_label(self, other) -> bool:
        return type(self) is type(other)

    @property
    def is_verify_enabled(self) -> bool:
        return True


class DynamicPres(ImageGridChallengePres):
    def __init__(self, state: DynamicState):
        super().__init__(state)

    @property
    def goal(self) -> str:
        note = "Click verify once there are none left."
        return format_goal_with_note(self.state.challenge.goal, note)

    # This method is more efficient than comparing `self.goal` and `other.goal`
    # as it avoids formatting the goal strings.
    def same_goal(self, other) -> bool:
        return (
            type(self) is type(other) and
            self.state.challenge.goal is other.state.challenge.goal
        )

    @property
    def is_verify_enabled(self) -> bool:
        return self.state.num_waiting <= 0

    @property
    def tiles(self) -> Iterable["DynamicTilePres"]:
        for i, image in enumerate(self.state.tile_images):
            yield DynamicTilePres(index=i, image=image)


class MultiCaptchaPres(ImageGridChallengePres):
    def __init__(self, state: MultiCaptchaState):
        super().__init__(state)

    @property
    def goal(self) -> str:
        note = "If there are none, click skip."
        if any(self.state.selected):
            note = '<span alpha="30%">{}</span>'.format(note)
        return format_goal_with_note(self.state.challenge.goal, note)

    # This method is more efficient than comparing `self.goal` and `other.goal`
    # as it avoids formatting the goal strings.
    def same_goal(self, other) -> bool:
        return (
            type(self) is type(other) and
            self.state.challenge.goal is other.state.challenge.goal and
            self.state.same_any_selected(other.state)
        )

    @property
    def verify_label(self) -> str:
        if self.state.any_selected:
            return "Ver_ify"
        return "Sk_ip"

    def same_verify_label(self, other) -> bool:
        return (
            type(self) is type(other) and
            self.state.same_any_selected(other.state)
        )

    @property
    def tiles(self) -> Iterable["MultiCaptchaTilePres"]:
        iterable = enumerate(zip(self.state.tile_images, self.state.selected))
        for i, (image, selected) in iterable:
            yield MultiCaptchaTilePres(index=i, image=image, selected=selected)


class TilePres:
    index: int
    image: Image.Image

    def __init__(self, index: int, image: Image.Image):
        self.index = index
        self.image = image

    def same(self, other) -> bool:
        return (
            type(self) is type(other) and
            self.index == other.index and
            self.image is other.image
        )

    def on_click(self, dispatch: Dispatch):
        dispatch(SelectTile(index=self.index))


class DynamicTilePres(TilePres):
    pass


class MultiCaptchaTilePres(TilePres):
    selected: bool

    def __init__(self, index: int, image: Image.Image, selected: bool):
        super().__init__(index, image)
        self.selected = selected

    def same(self, other) -> bool:
        return (
            super().same(other) and
            self.selected == other.selected
        )
