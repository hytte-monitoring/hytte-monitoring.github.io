#!/usr/bin/env bash
# Builds firmware/MICROBIT.hex: the Hytte Monitoring model in ../project/impl, unchanged, plus
# the board code in src/, on Lancaster University's CODAL runtime for the micro:bit v2.
#
#   ./build.sh            build firmware/MICROBIT.hex
#   ./build.sh --flash    build it and copy it onto a connected micro:bit
#
# Adapted from demos/microbit-library/firmware/build.sh in aiunderstand/ModelDrivenDesign_ex2
# (commit d439b1a). Needs git, python3, cmake and ninja or make. Without arm-none-eabi-gcc on
# the PATH, the Arm GNU toolchain is downloaded once into .build/toolchain. Everything fetched
# or built lives in .build/; delete it to start over.
set -euo pipefail

SAMPLES_URL=https://github.com/lancaster-university/microbit-v2-samples
SAMPLES_TAG=v0.3.0
TOOLCHAIN_VERSION=13.3.rel1

here="$(cd "$(dirname "$0")" && pwd)"
model="$(dirname "$here")/project/impl"
work="$here/.build"
codal="$work/codal"
mkdir -p "$work"

# 1. The compiler.
if ! command -v arm-none-eabi-gcc >/dev/null 2>&1; then
    if [ ! -x "$work/toolchain/bin/arm-none-eabi-gcc" ]; then
        case "$(uname -s)-$(uname -m)" in
            Darwin-arm64)  host=darwin-arm64 ;;
            Darwin-x86_64) host=darwin-x86_64 ;;
            Linux-x86_64)  host=x86_64 ;;
            Linux-aarch64) host=aarch64 ;;
            *) echo "No Arm GNU toolchain download for $(uname -s)-$(uname -m); put arm-none-eabi-gcc on the PATH." >&2; exit 1 ;;
        esac
        name="arm-gnu-toolchain-$TOOLCHAIN_VERSION-$host-arm-none-eabi"
        echo "Downloading $name (about 130 MB, once) ..."
        curl -fSL --progress-bar -o "$work/toolchain.tar.xz" \
            "https://developer.arm.com/-/media/Files/downloads/gnu/$TOOLCHAIN_VERSION/binrel/$name.tar.xz"
        mkdir -p "$work/toolchain"
        tar -xf "$work/toolchain.tar.xz" -C "$work/toolchain" --strip-components=1
        rm "$work/toolchain.tar.xz"
    fi
    export PATH="$work/toolchain/bin:$PATH"
fi

# 2. CODAL: the build system; build.py fetches the runtime libraries on its first run.
if [ ! -d "$codal" ]; then
    git clone --quiet --depth 1 --branch "$SAMPLES_TAG" "$SAMPLES_URL" "$codal"
fi
cp "$here/codal.json" "$codal/codal.json"

# 3. The application: the board code from src/, and the model's headers and sources
#    (not demo.cpp, the scenarios, the tests or the benchmark: they have their own main()).
rm -rf "$codal/source"
mkdir -p "$codal/source/hytte/src"
cp -R "$here/src/." "$codal/source/"
cp -R "$model/include" "$codal/source/hytte/"
for file in "$model"/src/*.cpp; do
    [ "$(basename "$file")" = "demo.cpp" ] || cp "$file" "$codal/source/hytte/src/"
done

# 4. Build. The model's headers include each other as "hytte/<class>.hpp", and the board
#    code includes "io/<file>.hpp", so both parents go on the include path.
(cd "$codal" && CXXFLAGS="-I$codal/source/hytte/include -I$codal/source" python3 build.py)
cp "$codal/MICROBIT.hex" "$here/MICROBIT.hex"
echo "Built $here/MICROBIT.hex"
# The dashboard offers the same file for download, so anyone can flash their own board.
cp "$here/MICROBIT.hex" "$(dirname "$here")/website/dashboard/hytte-monitoring.hex"
if command -v arm-none-eabi-size >/dev/null 2>&1 && [ -f "$codal/build/MICROBIT" ]; then
    arm-none-eabi-size "$codal/build/MICROBIT"
fi

# 5. Flash: a micro:bit shows up as a USB drive called MICROBIT; copying a .hex onto it flashes it.
if [ "${1:-}" = "--flash" ]; then
    drive=""
    for candidate in /Volumes/MICROBIT /media/"$USER"/MICROBIT /run/media/"$USER"/MICROBIT; do
        if [ -d "$candidate" ]; then drive="$candidate"; break; fi
    done
    if [ -z "$drive" ]; then
        echo "No MICROBIT drive found; connect the board over USB, or copy MICROBIT.hex onto it yourself." >&2
        exit 1
    fi
    cat "$here/MICROBIT.hex" > "$drive/MICROBIT.hex"
    echo "Flashed $drive; the board restarts when the yellow LED stops blinking."
fi
