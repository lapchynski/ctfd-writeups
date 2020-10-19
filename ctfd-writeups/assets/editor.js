
window.addEventListener('load', () => {
    let simplemde = new SimpleMDE({
        element: document.getElementById("writeup-content-editor"),
        autofocus: true,
        forceSync: true,
        indentWithTabs: false,
    });
})