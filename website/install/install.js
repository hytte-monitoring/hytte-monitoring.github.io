// The install page: fills in the terminal commands and their Copy buttons.

const $ = (id) => document.getElementById(id);

// Commands that download the firmware from this page and copy it onto the MICROBIT drive.
// The URL comes from the page's own address, so they work locally and on GitHub Pages.
function drawFlashCommands() {
    const hex = new URL("hytte-monitoring.hex", location.href).href;
    $("cmd-windows").textContent =
        `$hex = "$env:TEMP\\hytte-monitoring.hex"; Invoke-WebRequest "${hex}" -OutFile $hex; ` +
        `$drive = (Get-Volume -FileSystemLabel MICROBIT).DriveLetter; Copy-Item $hex "\${drive}:\\"; "Flashed \${drive}:"`;
    $("cmd-mac").textContent =
        `curl -fL -o /tmp/hytte-monitoring.hex "${hex}" && cat /tmp/hytte-monitoring.hex > /Volumes/MICROBIT/hytte-monitoring.hex && echo Flashed`;
    $("cmd-linux").textContent =
        `curl -fL -o /tmp/hytte-monitoring.hex "${hex}" && for d in /media/$USER/MICROBIT /run/media/$USER/MICROBIT; do ` +
        `[ -d "$d" ] && cp /tmp/hytte-monitoring.hex "$d/" && sync && echo "Flashed $d"; done`;
}

document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
        await navigator.clipboard.writeText($(button.dataset.copy).textContent);
        button.textContent = "Copied";
        setTimeout(() => { button.textContent = "Copy"; }, 1500);
    });
});

drawFlashCommands();
