"""The C++ toolchain on Windows: one fixed GCC toolchain from MSYS2, installed on demand.

The verifier needs a Unix-style toolchain: the sequence-diagram flow compiles with
-finstrument-functions and reads symbols with nm and c++filt, none of which MSVC has, and
libclang parses libstdc++ far more reliably than the newest MSVC standard library. So on
Windows every machine gets the same thing: MSYS2's UCRT64 environment with gcc, cmake and
ninja. ensure() finds it, installs it (winget + pacman) when it is missing, and puts it
first on PATH for this process and its children. On other platforms it does nothing.

Raises RuntimeError with plain-words instructions when it cannot.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGES = ["mingw-w64-ucrt-x86_64-gcc", "mingw-w64-ucrt-x86_64-cmake",
            "mingw-w64-ucrt-x86_64-ninja"]
NEEDED = ("g++.exe", "cmake.exe", "ninja.exe", "nm.exe", "c++filt.exe")
MANUAL = ("Install MSYS2 from https://www.msys2.org (default folder C:\\msys64), open "
          "'MSYS2 UCRT64' and run:  pacman -S --needed " + " ".join(PACKAGES))

_ready = False


def _roots():
    given = os.environ.get("MSYS2_ROOT")
    return [Path(r) for r in (given, r"C:\msys64", str(Path.home() / "msys64")) if r]


def _bin():
    """The ucrt64 bin directory holding the whole toolchain, or None."""
    for root in _roots():
        b = root / "ucrt64" / "bin"
        if all((b / n).exists() for n in NEEDED):
            return b
    return None


def _run(cmd, what):
    print(f"\n  {what}\n        $ {' '.join(map(str, cmd))}", flush=True)
    return subprocess.run(cmd).returncode


def _install():
    print("\n  The C++ toolchain (MSYS2 UCRT64: gcc, cmake, ninja) is not installed.\n"
          "  It is a one-time download of about 1 GB; winget may ask for permission.",
          flush=True)
    if sys.stdin.isatty() and input("  Install it now? [Y/n] ").strip().lower().startswith("n"):
        raise RuntimeError("the toolchain is required. " + MANUAL)
    root = next((r for r in _roots() if (r / "usr" / "bin" / "bash.exe").exists()), None)
    if root is None:
        if shutil.which("winget") is None:
            raise RuntimeError("winget is not available to install MSYS2. " + MANUAL)
        _run(["winget", "install", "--id", "MSYS2.MSYS2", "-e", "--silent",
              "--accept-package-agreements", "--accept-source-agreements"],
             "Installing MSYS2 ...")
        root = next((r for r in _roots() if (r / "usr" / "bin" / "bash.exe").exists()), None)
        if root is None:
            raise RuntimeError("MSYS2 did not install. " + MANUAL)
    code = _run([str(root / "usr" / "bin" / "bash.exe"), "-lc",
                 "pacman -Sy --noconfirm --needed " + " ".join(PACKAGES)],
                "Installing gcc, cmake and ninja into MSYS2 ...")
    if code != 0:
        raise RuntimeError(f"pacman failed (exit {code}). " + MANUAL)


def ensure():
    """Make the toolchain the one this process and its children use."""
    global _ready
    if os.name != "nt" or _ready:
        return
    bin_dir = _bin()
    if bin_dir is None:
        _install()
        bin_dir = _bin()
        if bin_dir is None:
            raise RuntimeError("the toolchain is still incomplete after installing. " + MANUAL)
    os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
    os.environ["CC"] = str(bin_dir / "gcc.exe")
    os.environ["CXX"] = str(bin_dir / "g++.exe")
    _ready = True


def cmake_generator(build_dir):
    """CMake arguments pinning the generator on Windows (Ninja, so the MSVC/Visual Studio
    generators are never picked). A build directory configured with another generator,
    e.g. by an earlier attempt, is deleted: CMake refuses to switch generators in place."""
    if os.name != "nt":
        return []
    cache = Path(build_dir) / "CMakeCache.txt"
    try:
        if cache.exists() and "CMAKE_GENERATOR:INTERNAL=Ninja" not in cache.read_text():
            shutil.rmtree(build_dir, ignore_errors=True)
    except OSError:
        pass
    return ["-G", "Ninja"]
