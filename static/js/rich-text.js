// Custom Offline Rich Text Editor for Law Firm Portal
// Replaces TinyMCE to avoid API warnings and cloud dependencies

class CustomRichTextEditor {
    constructor(textarea) {
        this.textarea = textarea;
        this.init();
    }

    init() {
        // Hide the original textarea
        this.textarea.style.display = 'none';

        // Create container wrapper
        const container = document.createElement('div');
        container.className = 'custom-editor-container';

        // Create toolbar
        const toolbar = document.createElement('div');
        toolbar.className = 'custom-editor-toolbar';

        // Create buttons helper
        const createButton = (icon, title, command, value = null) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'custom-editor-btn';
            btn.title = title;
            btn.innerHTML = `<i class="${icon}"></i>`;
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                if (command === 'createLink') {
                    const url = prompt('Enter the link URL:');
                    if (url) {
                        document.execCommand(command, false, url);
                    }
                } else {
                    document.execCommand(command, false, value);
                }
                this.editorArea.focus();
                this.updateTextarea();
            });
            return btn;
        };

        // Add formatting tools to toolbar
        toolbar.appendChild(createButton('fas fa-undo', 'Undo', 'undo'));
        toolbar.appendChild(createButton('fas fa-redo', 'Redo', 'redo'));
        toolbar.appendChild(createButton('fas fa-bold', 'Bold', 'bold'));
        toolbar.appendChild(createButton('fas fa-italic', 'Italic', 'italic'));
        toolbar.appendChild(createButton('fas fa-underline', 'Underline', 'underline'));
        toolbar.appendChild(createButton('fas fa-list-ul', 'Bullet List', 'insertUnorderedList'));
        toolbar.appendChild(createButton('fas fa-list-ol', 'Numbered List', 'insertOrderedList'));
        toolbar.appendChild(createButton('fas fa-link', 'Insert Link', 'createLink'));

        // Create contenteditable editor area
        const editorArea = document.createElement('div');
        editorArea.className = 'custom-editor-area';
        editorArea.contentEditable = true;
        editorArea.innerHTML = this.textarea.value || '<p><br></p>';

        // Synchronize content back to the original textarea on edits
        const syncContent = () => {
            this.textarea.value = editorArea.innerHTML;
        };

        editorArea.addEventListener('input', syncContent);
        editorArea.addEventListener('blur', syncContent);
        editorArea.addEventListener('keyup', syncContent);
        editorArea.addEventListener('paste', syncContent);

        // Assemble editor components
        container.appendChild(toolbar);
        container.appendChild(editorArea);

        // Place before original textarea
        this.textarea.parentNode.insertBefore(container, this.textarea);
        this.editorArea = editorArea;
    }

    updateTextarea() {
        this.textarea.value = this.editorArea.innerHTML;
    }
}

// Auto-initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('textarea.richtext').forEach(textarea => {
        new CustomRichTextEditor(textarea);
    });
});
