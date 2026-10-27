"""A project folder, and what one verification flow reads and writes in it.

    <folder>/diagrams/input/<type>.drawio            the design (input)
    <folder>/impl/                                   the implementation (input)
    <folder>/diagrams/output/<type>-<name>           generated diagrams
    <folder>/reports/<type>-report.md                generated report

<type> is the design file's name: `class` for class.drawio, or flow name plus
subject for files like state-door.drawio (flow `state`, subject `door`).
"""
import os
import subprocess
from pathlib import Path

from . import toolchain


class FlowFailed(Exception):
    """A flow could not produce a report. The message says why, in plain words."""

    def __init__(self, message, detail=""):
        super().__init__(message)
        self.detail = detail


class NotReady(FlowFailed):
    """The project has not reached this step yet (e.g. no implementation). Not an error."""


class Context:
    def __init__(self, folder, diagram_type):
        self.folder = Path(folder)
        self.type = diagram_type
        self.flow, _, self.subject = diagram_type.partition("-")
        self.input = self.folder / "diagrams" / "input" / f"{diagram_type}.drawio"
        self.output_dir = self.folder / "diagrams" / "output"
        self.report = self.folder / "reports" / f"{diagram_type}-report.md"
        self.impl = self.folder / "impl"
        self.build = self.folder / "build"
        self.trace_build = self.folder / "build-trace"

    def output(self, name):
        """diagrams/output/<type>-<name>"""
        return self.output_dir / f"{self.type}-{name}"

    def show(self, path):
        """A path as shown to people: relative to the project folder."""
        return Path(path).relative_to(self.folder).as_posix()

    def href(self, path):
        """`path` relative to the report, for use as a link target."""
        return Path(os.path.relpath(path, self.report.parent)).as_posix()

    def link(self, path, label=None):
        """A markdown link from the report to `path`."""
        return f"[`{label or self.show(path)}`]({self.href(path)})"

    def step(self, n, total, text):
        print(f"\n  [{n}/{total}] {text}", flush=True)

    def note(self, text):
        print(f"        {text}", flush=True)

    def write_failure(self, failure):
        self.report.parent.mkdir(parents=True, exist_ok=True)
        detail = f"```\n{failure.detail.strip()}\n```\n" if failure.detail else ""
        self.report.write_text(f"# Verification report\n\n**Not produced:** {failure}\n\n{detail}")


_BUILDS = {}   # build dir -> None (built) or the FlowFailed it raised; one build per run


def build_cmake(ctx):
    """Configure and build impl/ with CMake; the build gate every C++ flow shares.

    Also writes build/compile_commands.json. Compiler errors are printed as-is so
    VS Code's problem matcher can link them to the source. A project with several
    designs is built once; later flows get the same outcome without a second build.
    """
    include = ctx.impl / "include"
    if not any(include.rglob("*.h*")):
        raise NotReady(f"no implementation yet — there are no C++ headers in "
                       f"{ctx.show(include)}/; write one header per class there")
    if ctx.build in _BUILDS:
        if _BUILDS[ctx.build] is not None:
            raise _BUILDS[ctx.build]
        return
    try:
        toolchain.ensure()
    except RuntimeError as e:
        failure = FlowFailed("the C++ toolchain is not available", str(e))
        _BUILDS[ctx.build] = failure
        raise failure
    for cmd in (["cmake", "-S", str(ctx.impl), "-B", str(ctx.build),
                 *toolchain.cmake_generator(ctx.build),
                 "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"],
                ["cmake", "--build", str(ctx.build)]):
        try:
            run = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        except FileNotFoundError:
            raise FlowFailed("CMake is not installed, so the implementation cannot be built")
        if run.returncode != 0:
            print(run.stdout + run.stderr, flush=True)
            failure = FlowFailed("the implementation does not build", run.stdout + run.stderr)
            _BUILDS[ctx.build] = failure
            raise failure
    _BUILDS[ctx.build] = None


RUNTIME = Path(__file__).resolve().parent.parent / "runtime"
_TRACED = {}   # build-trace dir -> None (built) or the FlowFailed it raised


def cxx_compiler(build_dir):
    """The compiler the project's own build used (from its CMakeCache), else `c++`."""
    try:
        for line in (Path(build_dir) / "CMakeCache.txt").read_text().splitlines():
            if line.startswith("CMAKE_CXX_COMPILER:"):
                return line.split("=", 1)[1].strip() or "c++"
    except OSError:
        pass
    return "c++"


def build_traced(ctx):
    """Build impl/ a second time, in build-trace/, with function tracing.

    The project's own CMakeLists.txt is used unchanged: runtime/instrument.cmake is included
    after its project() call and adds the entry/exit hooks to every source and the trace
    runtime to every executable (see runtime/uml_trace.cpp). Built once per run, from
    scratch: a recording must come from the sources as they are now, and an incremental
    build can miss an edit made in the same second as the previous build.
    """
    if ctx.trace_build in _TRACED:
        if _TRACED[ctx.trace_build] is not None:
            raise _TRACED[ctx.trace_build]
        return
    generator = toolchain.cmake_generator(ctx.trace_build)
    ctx.trace_build.mkdir(parents=True, exist_ok=True)
    runtime = ctx.trace_build / "uml_trace.o"
    steps = (
        [cxx_compiler(ctx.build), "-std=c++20", "-c", str(RUNTIME / "uml_trace.cpp"), "-o", str(runtime)],
        ["cmake", "-S", str(ctx.impl), "-B", str(ctx.trace_build),
         *generator,
         f"-DCMAKE_PROJECT_INCLUDE={RUNTIME / 'instrument.cmake'}",
         f"-DUML_TRACE_RUNTIME={runtime}"],
        ["cmake", "--build", str(ctx.trace_build), "--clean-first"],
    )
    for cmd in steps:
        try:
            run = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        except FileNotFoundError:
            raise FlowFailed(f"{cmd[0]} is not installed, so the implementation cannot be traced")
        if run.returncode != 0:
            print(run.stdout + run.stderr, flush=True)
            failure = FlowFailed("the traced build of the implementation failed", run.stdout + run.stderr)
            _TRACED[ctx.trace_build] = failure
            raise failure
    _TRACED[ctx.trace_build] = None
