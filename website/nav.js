// The phone menu: a ☰ button opens and closes the site menu it controls (aria-controls).
// The menu closes again after a link is chosen, or with Escape. On wider screens the button
// is hidden by CSS and the menu is always shown.
for (const button of document.querySelectorAll(".menu-toggle")) {
    const menu = document.getElementById(button.getAttribute("aria-controls"));
    const setOpen = (open) => {
        button.setAttribute("aria-expanded", String(open));
        menu.classList.toggle("open", open);
    };
    button.addEventListener("click", () => setOpen(button.getAttribute("aria-expanded") !== "true"));
    menu.addEventListener("click", (event) => { if (event.target.closest("a")) setOpen(false); });
    document.addEventListener("keydown", (event) => { if (event.key === "Escape") setOpen(false); });
}
