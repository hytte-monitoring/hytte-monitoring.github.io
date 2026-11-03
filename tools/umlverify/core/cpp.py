"""Parsing a project's C++ headers with libclang; shared by every flow that reads C++.

translation_unit(include_dir) parses every header under include_dir as one unit and
returns (tu, ours): the translation unit, and a predicate telling whether a cursor
was declared in those headers rather than in the standard library.
"""
import os
import pathlib
import subprocess
import sys
from pathlib import Path

import clang.cindex as ci

# Match libclang to the SDK whose headers we parse. The pip wheel ships its own
# LLVM, which chokes on Apple's libc++; the CommandLineTools dylib is the same
# version as the SDK. On Linux/devcontainer the system libclang is already right.
# On Windows the newest MSVC STL needs Clang 20+, newer than the pip wheel: use an installed
# LLVM (winget install LLVM.LLVM) when there is one. LIBCLANG_PATH overrides everything.
for _candidate in (os.environ.get("LIBCLANG_PATH", ""),
                   "/Library/Developer/CommandLineTools/usr/lib/libclang.dylib",
                   r"C:\Program Files\LLVM\bin\libclang.dll"):
    if _candidate and pathlib.Path(_candidate).is_file():
        ci.Config.set_library_file(_candidate)
        break

HEADER_SUFFIXES = {".h", ".hh", ".hpp", ".hxx"}


def headers(include_dir):
    """Every header under include_dir, sorted."""
    include = Path(include_dir)
    return sorted(p for p in include.rglob("*") if p.suffix in HEADER_SUFFIXES)


_UNITS = {}   # resolved include dir -> (tu, ours): one parse per run, however many flows ask


def translation_unit(include_dir):
    """Parse all headers under include_dir as one unit -> (tu, ours).

    Raises RuntimeError with the first compiler error, or when there are no headers.
    """
    include = Path(include_dir)
    key = str(include.resolve())
    if key not in _UNITS:
        _UNITS[key] = _parse(include)
    return _UNITS[key]


def project_classes(include_dir):
    """The names of the classes, structs and class templates the headers define, in order."""
    tu, ours = translation_unit(include_dir)
    names = []

    def walk(cur):
        for c in cur.get_children():
            if c.kind == ci.CursorKind.NAMESPACE:
                walk(c)
            elif (c.kind in (ci.CursorKind.CLASS_DECL, ci.CursorKind.STRUCT_DECL,
                             ci.CursorKind.CLASS_TEMPLATE)
                  and ours(c) and c.is_definition() and c.spelling and c.spelling not in names):
                names.append(c.spelling)
    walk(tu.cursor)
    return names


def _resource_dir():
    """Elsewhere (Linux, CI), the wheel ships without clang's own headers (stddef.h, ...),
    so every standard header fails. Borrow them from an installed clang, if there is one."""
    try:
        found = subprocess.run(["clang", "-print-resource-dir"], capture_output=True,
                               text=True, check=True).stdout.strip()
    except Exception:
        return []
    return [f"-resource-dir={found}"] if (Path(found) / "include" / "stddef.h").exists() else []


def _mingw_args():
    """On Windows, parse against the same GCC the project is built with (MSYS2 UCRT64, see
    toolchain.py): ask g++ for its include search path and give libclang exactly that."""
    from . import toolchain
    toolchain.ensure()
    found = subprocess.run(["g++", "-E", "-x", "c++", "-", "-v"], input="",
                           capture_output=True, text=True).stderr.splitlines()
    dirs, inside = [], False
    for line in found:
        if line.startswith("#include <...>"):
            inside = True
        elif line.startswith("End of search list"):
            break
        elif inside and line.strip():
            dirs.append(line.strip())
    if not dirs:
        raise RuntimeError("g++ did not report its include directories")
    return (["-target", "x86_64-w64-windows-gnu", "-nostdinc", "-nostdinc++"]
            + [f"-isystem{d}" for d in dirs])


def _parse(include):
    found = headers(include)
    if not found:
        raise RuntimeError(f"no C++ headers found under {include}")
    unit = "\n".join(f'#include "{h.relative_to(include).as_posix()}"' for h in found)
    args = ["-std=c++20", f"-I{include}", "-xc++"]
    # The pip libclang wheel is not the platform driver, so on macOS it needs the
    # SDK spelled out. A C++ tool linking the system libclang inherits these.
    if sys.platform == "win32":
        args += _mingw_args()
    else:
        try:
            sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True,
                                 text=True, check=True).stdout.strip()
            args += [f"-isysroot{sdk}", f"-I{sdk}/usr/include/c++/v1", f"-I{sdk}/usr/include"]
        except Exception:
            args += _resource_dir()
    tu =ci.Index.create().parse("all.cpp", args=args, unsaved_files=[("all.cpp", unit)])
    for d in tu.diagnostics:
        if d.severity >= ci.Diagnostic.Error:
            loc = d.location
            where = f"{loc.file.name}:{loc.line}: " if loc.file else ""
            raise RuntimeError(f"{where}{d.spelling}")

    root = include.resolve()

    def ours(c):
        """Only declarations written in this project's headers -- not libc++."""
        f = c.location.file
        if f is None:
            return False
        try:
            return root in Path(f.name).resolve().parents
        except OSError:
            return False

    return tu, ours
