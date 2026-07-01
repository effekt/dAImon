"""Per-panel content for the selected daemon, as Textual markup. Status is
conveyed by symbol + text (never colour alone)."""

import state
from _lib import schedule_fmt


def render_config(cfg, slug: str) -> str:
    d = cfg.daemon(slug)
    lines = [
        f"[dim]backend [/dim] {d['backend']}",
        f"[dim]model   [/dim] {d['model']}",
        f"[dim]source  [/dim] {d.get('source') or '—'}",
        f"[dim]schedule[/dim] {schedule_fmt.display(d['schedule'])}",
        f"[dim]danger  [/dim] {'on' if d['danger'] else 'off'}",
        f"[dim]stuck   [/dim] {d['stuck_after']}s",
        f"[dim]command [/dim] {d['command']}",
        f"[dim]workdir [/dim] {d['working_dir']}",
    ]
    prov = cfg.input_provenance(slug)
    if prov["daemon"]:
        lines.append("[dim]── inputs ──────[/dim]")
        lines += [f"[dim]{k:<12}[/dim] {v}" for k, v in prov["daemon"].items()]
    for name, fields in prov["profiles"].items():
        lines.append(f"[dim]── profile: {name} ──[/dim]")
        lines += [f"[dim]{k:<12}[/dim] {v}" for k, v in fields.items()]
    return "\n".join(lines)


def render_status(cfg, slug: str) -> str:
    def mark(ok):
        return "[green]✓[/green]" if ok else "[dim]·[/dim]"

    reg = mark(state.registered(cfg, slug))
    loaded = mark(state.launchd_loaded(state.label_for(cfg, slug)))
    run = "[green]● running[/green]" if state.running_session(cfg, slug) else "[dim]— idle[/dim]"
    return f"registered {reg}   loaded {loaded}   {run}"


def render_procs(cfg, slug: str) -> str:
    procs = state.session_procs(cfg, slug)
    if not procs:
        return "[dim]— not running[/dim]"
    total = sum(rss for _, rss, _ in procs)
    rows = [
        f"[dim]{pid:>6}[/dim] {label:<7}[dim]{rss:>6.0f} MB[/dim]"
        for pid, rss, label in sorted(procs, key=lambda p: -p[1])[:6]
    ]
    return "\n".join([f"[dim]{len(procs)} procs · {total:.0f} MB total[/dim]"] + rows)


def render_log(cfg, slug: str, n: int = 200) -> str:
    path = cfg.state_dir / "logs" / f"{slug}.log"
    if not path.exists():
        return "[dim](no log yet)[/dim]"
    tail = path.read_text(errors="replace").splitlines()[-n:]
    return "\n".join(f"[dim]{ln}[/dim]" for ln in tail) or "[dim](empty)[/dim]"
