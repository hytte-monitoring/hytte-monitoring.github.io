#!/usr/bin/env python3
"""Build the showcase site: every project told as an interactive story, for GitHub Pages.

    python3 tools/site/build_site.py                      every project -> _site/
    python3 tools/site/build_site.py --out DIR --start 3-state-simple

Run tools/verify.py first: a story shows the reports and colour-coded comparisons that run
produced. Every project with a design becomes a story (each folder under examples/, and
project/ once it has a drawing); the dropdown at the top of the page switches between
them. A story is data, not a page: _site/data/<name>.json holds everything one story
shows, and static/story.js tells it in four chapters -- the drawings, the C++, the
verdict, and, for state machines and scenarios, the design and the code running side by
side.

Preview:  python3 -m http.server -d _site 8000, then open http://localhost:8000
On GitHub, .github/workflows/pages.yml runs the verifier and this script on every push.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import verify  # noqa: E402  (tools/verify.py: which folders are projects)
from umlverify.core.compare import nname  # noqa: E402
from umlverify.state_diagram import mermaid as state_mermaid  # noqa: E402
from umlverify.state_diagram.mermaid import events  # noqa: E402

REPO = verify.REPO
KINDS = ("class", "state", "sequence")   # the flows a story can tell

# One row of a transition table, as UML-CPP-MAPPING.md writes it:
#   {State::Closed, Event::open, State::Open, nullptr, &Door::log},
ROW = re.compile(r"\{\s*State::(\w+)\s*,\s*Event::(\w+)\s*,\s*State::(\w+)\s*,"
                 r"\s*(?:nullptr|&\s*\w+::(\w+))\s*,\s*(?:nullptr|&\s*\w+::(\w+))\s*\}")
INITIAL = re.compile(r"\bState\s+\w+\s*(?:=\s*|\{\s*)State::(\w+)")


def source_links():
    """Where the sources can be browsed: GitHub's blob URL for this commit, or None."""
    server, repo, sha = (os.environ.get(k) for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY",
                                                     "GITHUB_SHA"))
    if not (server and repo and sha):
        def git(*args):
            return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True,
                                  check=True).stdout.strip()
        try:
            remote, sha = git("remote", "get-url", "origin"), git("rev-parse", "HEAD")
        except (OSError, subprocess.CalledProcessError):
            return None, None
        m = re.match(r"^(?:https://github\.com/|git@github\.com:)(.+?)(?:\.git)?$", remote)
        if not m:
            return None, sha
        server, repo = "https://github.com", m.group(1)
    return f"{server}/{repo}", sha


def readme(folder):
    """-> (title, lead): the README's heading and its first paragraph, as markdown."""
    try:
        text = (folder / "README.md").read_text()
    except OSError:
        return folder.name, ""
    lines = text.splitlines()
    title = next((line[2:].strip() for line in lines if line.startswith("# ")), folder.name)
    body = "\n".join(line for line in lines if not line.startswith("# "))
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    lead = next((p for p in paragraphs if not p.startswith(("#", "|", "```", ">"))), "")
    return title, lead


def section(markdown, heading):
    """The text under `## heading`, up to the next `## ` or the closing rule."""
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |^---\s*$|\Z)", markdown, re.M | re.S)
    return m.group(1).strip() if m else ""


def unlink(markdown):
    """Relative links point into the repository, not the site: keep their text only."""
    return re.sub(r"\[([^\]]*)\]\((?!https?:|#)[^)]*\)", r"\1", markdown)


def report(path):
    """A verification report -> what the verdict chapter shows."""
    if not path.exists():
        return {"produced": False, "reason": "not verified yet: run tools/verify.py"}
    text = path.read_text()
    if "**Not produced:**" in text:
        reason = re.search(r"\*\*Not produced:\*\*\s*(.*)", text).group(1).strip()
        return {"produced": False, "reason": reason}
    m = re.search(r"\*\*Alignment: ([\d.]+) %\*\*\s*—\s*(.*)", text)
    overview = section(text, "Overview")
    counts, _, meaning = overview.partition("### What the numbers mean")
    return {
        "produced": True,
        "alignment": float(m.group(1)) if m else None,
        "summary": m.group(2).strip() if m else "",
        "counts": unlink("\n".join(line for line in counts.splitlines()
                                   if line.startswith("|"))),
        "meaning": unlink(meaning.strip()),
        "differences": unlink(section(text, "Differences")),
    }


def read_text(path, folder):
    return {"path": path.relative_to(folder).as_posix(), "text": path.read_text()}


def transition_table(header, implemented):
    """Where each implemented transition is in the header: its table row's line number."""
    lines = header["text"].splitlines()
    rows = [(n, m.groups()) for n, line in enumerate(lines, 1) for m in [ROW.search(line)] if m]
    for t in implemented["transitions"]:
        want = tuple(nname(t[k]) for k in ("from", "event", "to", "guard", "action"))
        t["line"] = next((n for n, g in rows if tuple(nname(x) for x in g) == want), None)
    implemented["initialLine"] = next(
        (n for n, line in enumerate(lines, 1)
         if (m := INITIAL.search(line)) and nname(m.group(1)) == nname(implemented["initial"])),
        None)


def state_story(folder, ctx, design):
    out = folder / "diagrams" / "output"
    machines = {}
    for side in ("design", "implemented"):
        mmd = out / f"{ctx}-{side}.mmd"
        machines[side] = state_mermaid.parse(mmd.read_text()) if mmd.exists() else None
    if machines["design"] is None or machines["implemented"] is None:
        return
    subject = ctx.partition("-")[2]
    found = sorted((folder / "impl" / "include").rglob(f"{subject}.hpp"))
    header = read_text(found[0], folder) if found else None
    if header:
        transition_table(header, machines["implemented"])
    for machine in machines.values():
        machine["events"] = events(machine)
    design.update(machines=machines, header=header,
                  className="".join(p[:1].upper() + p[1:] for p in subject.split("_")))


def sequence_story(folder, ctx, design):
    program = folder / "impl" / "scenarios" / f"{ctx.partition('-')[2]}.cpp"
    design["program"] = read_text(program, folder) if program.exists() else None


def story(folder):
    """One project -> everything its story shows, or None when it has no design yet."""
    inputs = verify.designs(folder)
    if not inputs:
        return None
    title, lead = readme(folder)
    stories = []
    for drawing in inputs:
        ctx = drawing.stem
        kind, _, subject = ctx.partition("-")
        if kind not in KINDS:
            continue
        comparison = folder / "diagrams" / "output" / f"{ctx}-comparison.drawio"
        design = {
            "file": drawing.name,
            "kind": kind,
            "subject": subject,
            "input": drawing.read_text(),
            "comparison": comparison.read_text() if comparison.exists() else None,
            "report": report(folder / "reports" / f"{ctx}-report.md"),
        }
        if kind == "state":
            state_story(folder, ctx, design)
        elif kind == "sequence":
            sequence_story(folder, ctx, design)
        stories.append(design)
    include = folder / "impl" / "include"
    code = [read_text(p, folder) for p in sorted(include.rglob("*.hpp"))] if include.is_dir() else []
    scenarios = folder / "impl" / "scenarios"
    if scenarios.is_dir():
        code += [read_text(p, folder) for p in sorted(scenarios.glob("*.cpp"))]
    return {"name": folder.name, "path": verify.label(folder), "title": title, "lead": lead,
            "designs": stories, "code": code}


def summary(data):
    """What the dropdown and the index need to know about one story."""
    return {"name": data["name"], "path": data["path"], "title": data["title"],
            "designs": [{"kind": d["kind"], "subject": d["subject"],
                         "alignment": d["report"].get("alignment")} for d in data["designs"]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", default=str(REPO / "_site"), help="output folder (emptied first)")
    parser.add_argument("--start", help="the story shown when the URL names none")
    args = parser.parse_args()

    out = Path(args.out).resolve()
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(HERE / "static", out)
    (out / "data").mkdir()

    stories = []
    for folder in verify.projects():
        data = story(folder)
        if data is None:
            print(f"  – {verify.label(folder)}: no design yet, no story")
            continue
        (out / "data" / f"{data['name']}.json").write_text(json.dumps(data, ensure_ascii=False))
        stories.append(summary(data))
        produced = sum(d["report"]["produced"] for d in data["designs"])
        print(f"  ✓ {verify.label(folder)}: {len(data['designs'])} designs, {produced} verified")
    if not stories:
        sys.exit("No project has a design yet: nothing to show")

    repo, sha = source_links()
    site = {
        "stories": stories,
        "start": args.start if any(s["name"] == args.start for s in stories) else stories[0]["name"],
        "repo": repo,
        "commit": sha,
        "ci": os.environ.get("GITHUB_ACTIONS") == "true",
        "built": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    page = (out / "index.html").read_text()
    payload = json.dumps(site, ensure_ascii=False).replace("</", "<\\/")
    (out / "index.html").write_text(page.replace("{{SITE}}", payload))
    print(f"\n  {len(stories)} stories -> {out}")


if __name__ == "__main__":
    main()
