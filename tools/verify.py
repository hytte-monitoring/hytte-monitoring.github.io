#!/usr/bin/env python3
"""Verify projects: regenerate their outputs from design and implementation.

    python3 tools/verify.py                  ask which project (Enter repeats the last choice)
    python3 tools/verify.py project          verify one project, by name or path
    python3 tools/verify.py 2-class-library
    python3 tools/verify.py --all            verify every project

The projects are project/ (your own work) and every folder under examples/. A project's
designs are the files in diagrams/input/; each file's name picks the verification:
class.drawio runs the class-diagram flow, state-<class>.drawio the state-machine flow
for that class. A project without a design yet is listed, and choosing it tells you
where to put one.

Per project, diagrams/output/ and reports/*-report.md are emptied first, so nothing
stale survives. In VS Code this runs as the default build task: Ctrl+Shift+B
(Cmd+Shift+B on macOS).

Exit status is 0 when every design produced a report, whatever the alignment, and 1
when a report could not be made (for example, the implementation does not build).
A project that is not that far yet — no design, or no implementation — is skipped,
not a failure.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def _bootstrap():
    """Make `python tools/verify.py` work from any Python, on any OS, with no setup step:
    when the libclang bindings are missing, create .venv, install requirements.txt into it
    and re-run this script with the venv's Python."""
    if not sys.flags.utf8_mode:
        # Windows defaults to cp1252 for files; the reports and diagrams are UTF-8 (emoji,
        # arrows). UTF-8 mode makes every read and write UTF-8, whatever the platform.
        sys.exit(subprocess.call([sys.executable, "-X", "utf8", *sys.argv]))
    try:
        import clang.cindex  # noqa: F401
        return
    except ImportError:
        pass
    if os.environ.get("UMLVERIFY_BOOTSTRAPPED"):
        return   # already re-run once: let the flow report the real import error
    repo = Path(__file__).resolve().parent.parent
    venv = repo / ".venv"
    py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    print("Setting up the Python environment (first run only) ...", flush=True)
    if not py.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(venv)])
    subprocess.check_call([str(py), "-m", "pip", "install", "--quiet",
                           "-r", str(repo / "requirements.txt")])
    sys.exit(subprocess.call([str(py), "-X", "utf8", *sys.argv],
                             env={**os.environ, "UMLVERIFY_BOOTSTRAPPED": "1"}))


_bootstrap()
sys.path.insert(0, str(Path(__file__).resolve().parent))
import umlverify  # noqa: E402
from umlverify.core.compare import alignment, totals  # noqa: E402
from umlverify.core.project import Context, FlowFailed, NotReady  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
PROJECT = REPO / "project"
EXAMPLES = REPO / "examples"
LAST_CHOICE = REPO / ".cache" / "verify-last-choice"


def projects():
    """Your own project first, then the examples."""
    found = [PROJECT] if PROJECT.is_dir() else []
    if EXAMPLES.is_dir():
        found += sorted(p for p in EXAMPLES.iterdir() if (p / "diagrams").is_dir())
    return found


def label(folder):
    """How a project is named in menus and summaries: its path from the repository root."""
    try:
        return folder.relative_to(REPO).as_posix()
    except ValueError:
        return str(folder)


def designs(folder):
    return sorted((folder / "diagrams" / "input").glob("*.drawio"))


def ask(folders):
    """Terminal menu. Returns the chosen folders."""
    names = [label(f) for f in folders]
    try:
        last = LAST_CHOICE.read_text().strip()
    except OSError:
        last = ""
    default = last if last in names + ["all"] else names[0]

    print("Which project do you want to verify?")
    for n, (folder, name) in enumerate(zip(folders, names), 1):
        print(f"  {n}) {name}" + ("" if designs(folder) else "   (no design yet)"))
    print("  a) all")
    while True:
        answer = input(f"Choice [{default}]: ").strip() or default
        matches = [i for i, name in enumerate(names) if answer in (name, Path(name).name)]
        if answer.lower() in ("a", "all"):
            choice, chosen = "all", folders
        elif answer.isdigit() and 1 <= int(answer) <= len(folders):
            choice, chosen = names[int(answer) - 1], [folders[int(answer) - 1]]
        elif matches:
            choice, chosen = names[matches[0]], [folders[matches[0]]]
        else:
            print(f"  '{answer}' is not one of the choices.")
            continue
        LAST_CHOICE.parent.mkdir(exist_ok=True)
        LAST_CHOICE.write_text(choice)
        return chosen


def resolve(arg):
    """A project named on the command line: a path, a path from the repo root, or an example name."""
    for candidate in (Path(arg), REPO / arg, EXAMPLES / arg):
        if candidate.is_dir():
            return candidate.resolve()
    sys.exit(f"No such project: {arg}")


def clean(folder):
    """Empty diagrams/output/ and remove old reports: every run starts from scratch."""
    output = folder / "diagrams" / "output"
    output.mkdir(parents=True, exist_ok=True)
    stale = [f for f in output.iterdir() if f.is_file() and f.name != ".gitkeep"]
    stale += list((folder / "reports").glob("*-report.md"))
    for f in stale:
        f.unlink()
    return len(stale)


def verify(folder):
    """Run every design in one project. Returns [(status, design file, report, summary)],
    status being "ok", "failed" or "skipped"."""
    name = label(folder)
    print(f"\n━━ {name} " + "━" * max(0, 60 - len(name)))
    removed = clean(folder)
    print(f"  cleaned diagrams/output/ and reports/ ({removed} old files removed)")
    found = designs(folder)
    if not found:
        target = f"{name}/diagrams/input/{umlverify.supported()[0]}"
        print(f"  No design yet. Draw your class diagram in draw.io and save it as\n"
              f"      {target}\n"
              f"  then run this again. In VS Code, create that file and it opens in the\n"
              f"  draw.io editor; the class shapes are under More Shapes › UML.\n"
              f"  A class's state machine goes next to it, as state-<class>.drawio.")
        return [("skipped", "-", None, f"no design yet — save it as {target}")]

    results = []
    for design in found:
        flow = umlverify.flow_for(design)
        if flow is None:
            msg = (f"no verification exists for '{design.name}' "
                   f"(supported: {', '.join(umlverify.supported())})")
            print(f"\n  ✗ {msg}")
            results.append(("failed", design.name, None, msg))
            continue
        print(f"\n  {flow.TITLE}: {design.name}")
        ctx = Context(folder, design.stem)
        try:
            result = flow.run(ctx)
        except NotReady as pending:
            ctx.write_failure(pending)
            print(f"\n  – {pending}")
            results.append(("skipped", design.name, ctx.report, str(pending)))
            continue
        except FlowFailed as failure:
            ctx.write_failure(failure)
            print(f"\n  ✗ {failure}")
            if failure.detail:
                print(f"    {failure.detail}")
            results.append(("failed", design.name, ctx.report, f"not produced: {failure}"))
            continue
        t = totals(result)
        summary = (f"alignment {alignment(t):.1f} % — {t['identical']} identical, "
                   f"{t['changed']} changed, {t['missing']} missing, {t['extra']} extra")
        print(f"\n  ✓ {summary}")
        results.append(("ok", design.name, ctx.report, summary))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("projects", nargs="*", help="project names or paths")
    parser.add_argument("--all", action="store_true", help="verify every project")
    args = parser.parse_args()

    available = projects()
    if not available:
        sys.exit("No projects found: expected project/ or examples/<name>/diagrams/")
    if args.all:
        chosen = available
    elif args.projects:
        chosen = [resolve(arg) for arg in args.projects]
    elif len(available) == 1 or not sys.stdin.isatty():
        chosen = available
    else:
        chosen = ask(available)

    mark = {"ok": "✓", "failed": "✗", "skipped": "–"}
    lines, failed = [], False
    for folder in chosen:
        for status, design, report, summary in verify(folder):
            failed |= status == "failed"
            where = f"\n      {label(report)}" if report else ""
            lines.append(f"  {mark[status]} {label(folder)}/{design}: {summary}{where}"
                         if design != "-" else f"  {mark[status]} {label(folder)}: {summary}")
    print("\n━━ Summary " + "━" * 55)
    print("\n".join(lines))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
