
window.addEventListener('load', () => {
    console.log('hello from editor.js')
    let simplemde = new SimpleMDE({
        element: document.getElementById("writeup-content-editor"),
        autofocus: true,
        forceSync: true,
        indentWithTabs: false,
        initialValue: "# Title\n\ncontent..."
    });
})