"""Modal screens: per-daemon configure, and the process-tree inspector."""

from typing import Any, Protocol, cast

import ops
from _lib import config, models, schedule_fmt
from rich.text import Text
from state import label_for, launchd_loaded, registered, sh
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, OptionList, Select, Static, Switch
from textual.widgets.option_list import Option

BACKENDS = ["claude"]


class _HasValue(Protocol):
    value: Any


class ConfigScreen(ModalScreen):
    CSS = """
    ConfigScreen { align: center middle; }
    #dialog { width: 72; height: auto; max-height: 90%; padding: 1 2; border: round $primary; background: $panel; }
    #dialog-title { width: 100%; text-align: center; text-style: bold; color: $accent; padding-bottom: 1; }
    #grid-scroll { height: auto; max-height: 24; }
    #grid { grid-size: 2; grid-columns: 18 1fr; grid-gutter: 1 1; height: auto; }
    #grid Label { padding-top: 1; }
    #grid .section { column-span: 2; color: $accent; text-style: bold; padding-top: 1; }
    #buttons { height: auto; align: right middle; padding-top: 1; }
    #buttons Button { margin-left: 2; }
    """

    def __init__(self, cfg, slug: str):
        super().__init__()
        self.cfg = cfg
        self.slug = slug
        self.d = cfg.daemon(slug)
        self.raw = cfg.raw_daemon(slug)
        prov = cfg.input_provenance(slug)
        self.daemon_inputs = prov["daemon"]
        self.profile_inputs = prov["profiles"]
        self.sources = [""] + sorted(
            p.parent.name for p in cfg.profiles_dir().glob("*/profile.toml")
        )
        self.claude_models = models.list_models("claude")

    def _init_model(self, kind: str):
        m = self.d["model"]
        return m.get(kind) if isinstance(m, dict) else m

    def _select(self, wid: str, options: list[str], value):
        safe = value if value in options else (options[0] if options else None)
        return Select.from_values(options, value=safe, id=wid)

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"configure {self.slug}", id="dialog-title")
            with VerticalScroll(id="grid-scroll"), Grid(id="grid"):
                yield from self._framework_fields()
                yield from self._input_fields()
            with Horizontal(id="buttons"):
                yield Button("cancel", id="cancel")
                yield Button("save", variant="primary", id="save")

    def _framework_fields(self) -> ComposeResult:
        d = self.d
        wd = self.raw.get("daemon", {}).get("working_dir", str(d["working_dir"]))
        yield Static("daemon", classes="section")
        yield Label("schedule")
        yield Input(value=schedule_fmt.display(d["schedule"]), id="f-schedule")
        yield Label("working dir")
        yield Input(value=wd, id="f-working-dir")
        yield Label("source")
        yield self._select("f-source", self.sources, d.get("source", ""))
        yield Label("backend")
        yield self._select("f-backend", BACKENDS, d["backend"])
        yield Label("model")
        yield self._select("f-model", self.claude_models, self._init_model("claude"))
        yield Label("run dangerously")
        yield Switch(value=bool(d["danger"]), id="f-danger")
        yield Label("stuck_after (s)")
        yield Input(value=str(d["stuck_after"]), id="f-stuck")

    @staticmethod
    def _show(val) -> str:
        return ", ".join(str(x) for x in val) if isinstance(val, list) else str(val)

    def _input_fields(self) -> ComposeResult:
        if self.daemon_inputs:
            yield Static("inputs", classes="section")
            for key, val in self.daemon_inputs.items():
                yield Label(key)
                yield Input(value=self._show(val), id=f"in-{key}")
        for name, fields in self.profile_inputs.items():
            yield Static(f"profile: {name}  (shared by all {name} daemons)", classes="section")
            for key, val in fields.items():
                yield Label(key)
                yield Input(value=self._show(val), id=f"prof-{name}-{key}")

    def _value(self, wid: str):
        return cast(_HasValue, self.query_one(f"#{wid}")).value

    def _coerce(self, original, value: str):
        if isinstance(original, list):
            return [s.strip() for s in value.split(",") if s.strip()]
        if isinstance(original, int) and not isinstance(original, bool):
            return int(value) if value.strip().lstrip("-").isdigit() else value
        return value

    def _save(self, new_sched: dict) -> None:
        backend = self._value("f-backend")
        daemon = {
            "schedule": new_sched,
            "working_dir": self._value("f-working-dir"),
            "source": self._value("f-source"),
            "backend": backend,
            "model": self._value("f-model"),
            "danger": self._value("f-danger"),
            "stuck_after": int(self._value("f-stuck")),
        }
        inputs = {k: self._coerce(v, self._value(f"in-{k}")) for k, v in self.daemon_inputs.items()}
        self.cfg.update_local(self.slug, daemon, inputs or None)
        for name, fields in self.profile_inputs.items():
            edited = {
                k: self._coerce(v, self._value(f"prof-{name}-{k}")) for k, v in fields.items()
            }
            if edited:
                self.cfg.update_profile_local(name, edited)

    def _apply(self) -> None:
        old_sched = self.cfg.daemon(self.slug)["schedule"]
        new_sched = schedule_fmt.parse(self._value("f-schedule"))
        self._save(new_sched)
        fresh = self.cfg.load()
        if registered(fresh, self.slug):
            ops.regen_plist(fresh, self.slug)
            if new_sched != old_sched and launchd_loaded(label_for(fresh, self.slug)):
                ops.disable(fresh, self.slug)
                ops.enable(fresh, self.slug)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._apply()
        self.dismiss(event.button.id == "save")


class ManageScreen(ModalScreen):
    BINDINGS = [("escape", "dismiss", "close")]
    CSS = """
    ManageScreen { align: center middle; }
    #menu { width: 44; height: auto; padding: 1 2; border: round $primary; background: $panel; }
    #menu-title { width: 100%; text-align: center; text-style: bold; color: $accent; padding-bottom: 1; }
    """

    def __init__(self, items: list[tuple[str, str]]):
        super().__init__()
        self.items = items

    def compose(self) -> ComposeResult:
        with Vertical(id="menu"):
            yield Label("manage  (esc to close)", id="menu-title")
            yield OptionList(*[Option(label, id=action) for action, label in self.items])

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option.id)

    def action_dismiss(self) -> None:
        self.dismiss(None)


class DuplicateScreen(ModalScreen[str]):
    BINDINGS = [("escape", "cancel", "cancel")]
    CSS = """
    DuplicateScreen { align: center middle; }
    #dup { width: 56; height: auto; padding: 1 2; border: round $primary; background: $panel; }
    #dup-title { padding-bottom: 1; text-style: bold; color: $accent; }
    #dup-buttons { height: auto; align: right middle; padding-top: 1; }
    #dup-buttons Button { margin-left: 2; }
    """

    def __init__(self, src: str):
        super().__init__()
        self.src = src

    def compose(self) -> ComposeResult:
        with Vertical(id="dup"):
            yield Label(f"duplicate '{self.src}' as a new daemon:", id="dup-title")
            yield Input(value=f"{self.src}-copy", id="dup-name")
            with Horizontal(id="dup-buttons"):
                yield Button("cancel", id="no")
                yield Button("create", variant="primary", id="yes")

    def _submit(self) -> None:
        self.dismiss(self.query_one("#dup-name", Input).value.strip() or None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self._submit() if event.button.id == "yes" else self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)


class FilesScreen(ModalScreen):
    BINDINGS = [("escape,q", "dismiss", "close")]
    CSS = """
    FilesScreen { align: center middle; }
    #files { width: 90%; height: 85%; padding: 1 2; border: round $primary; background: $panel; }
    #files-title { text-style: bold; color: $accent; padding-bottom: 1; }
    """

    def __init__(self, cfg, slug: str):
        super().__init__()
        self.cfg = cfg
        self.slug = slug

    def compose(self) -> ComposeResult:
        toml_text = self.cfg.daemon_toml_path(self.slug).read_text()
        skill = config.render_skill(self.cfg, self.slug)
        body = f"daemon.toml\n\n{toml_text}\n\n— SKILL.md (rendered) —\n\n{skill}"
        with VerticalScroll(id="files"):
            yield Label(f"{self.slug} files  (esc to close)", id="files-title")
            yield Static(Text(body))

    def action_dismiss(self) -> None:
        self.dismiss(None)


class HelpScreen(ModalScreen):
    BINDINGS = [("escape,q,question_mark", "dismiss", "close")]
    CSS = """
    HelpScreen { align: center middle; }
    #help { width: 56; height: auto; max-height: 90%; padding: 1 2; border: round $primary; background: $panel; }
    #help-title { width: 100%; text-align: center; text-style: bold; color: $accent; padding-bottom: 1; }
    """

    def __init__(self, items: list[tuple[str, str]]):
        super().__init__()
        self.items = items

    def compose(self) -> ComposeResult:
        rows = "\n".join(f"  [bold]{key:<7}[/bold] [dim]{desc}[/dim]" for key, desc in self.items)
        with VerticalScroll(id="help"):
            yield Label("keys  (esc to close)", id="help-title")
            yield Static(rows)

    def action_dismiss(self) -> None:
        self.dismiss(None)


class ConfirmScreen(ModalScreen[bool]):
    BINDINGS = [("escape", "cancel", "cancel")]
    CSS = """
    ConfirmScreen { align: center middle; }
    #confirm { width: 50; height: auto; padding: 1 2; border: round $error; background: $panel; }
    #confirm-msg { padding-bottom: 1; }
    #confirm-buttons { height: auto; align: right middle; }
    #confirm-buttons Button { margin-left: 2; }
    """

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm"):
            yield Static(self.message, id="confirm-msg")
            with Horizontal(id="confirm-buttons"):
                yield Button("cancel", id="no")
                yield Button("confirm", variant="error", id="yes")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")

    def action_cancel(self) -> None:
        self.dismiss(False)


class ProcessScreen(ModalScreen):
    BINDINGS = [("escape", "dismiss", "close")]
    CSS = """
    ProcessScreen { align: center middle; }
    #proc-box { width: 90%; height: 80%; padding: 1 2; border: round $primary; background: $panel; }
    #proc-title { text-style: bold; color: $accent; }
    """

    def __init__(self, install_root, slug: str):
        super().__init__()
        self.install_root = install_root
        self.slug = slug

    def compose(self) -> ComposeResult:
        out = (
            sh("bash", str(self.install_root / "lib" / "ps.sh"), self.slug)
            or "(no running process)"
        )
        with VerticalScroll(id="proc-box"):
            yield Static(f"process tree — {self.slug}  (esc to close)", id="proc-title")
            yield Static(out)

    def action_dismiss(self) -> None:
        self.dismiss(None)
