let zIndexCounter = 1;
const notes = [];
const TRASH_ZONE = document.getElementById('trash');

let currentDraggedNote = null;
let dragOffsetX = 0;
let dragOffsetY = 0;

const debounceTimers = {};

function loadNotes() {
    fetch("/api/notes")
        .then(res => res.json())
        .then(data => data.forEach(createNoteFromData));
}

function createNoteFromData({id, x, y, content, color}) {
    const note = document.createElement('div');
    note.className = 'note';
    note.style.left = `${x}px`;
    note.style.top = `${y}px`;
    note.style.zIndex = zIndexCounter++;
    note.style.backgroundColor = color;
    note.dataset.id = id;

    const textarea = document.createElement('textarea');
    textarea.value = content;
    textarea.readOnly = true;
    note.appendChild(textarea);

    enableNoteInteractions(note, textarea);
    document.body.appendChild(note);
    notes.push({note, textarea});
}

function createNewNote() {
    const newNoteData = {x: 40, y: 40, content: ""};
    fetch("/api/notes", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(newNoteData)
    })
        .then(res => res.json())
        .then(createNoteFromData);
}

function enableNoteInteractions(note, textarea) {
    let isEditing = false;

    note.addEventListener('dblclick', () => {
        isEditing = true;
        textarea.readOnly = false;
        textarea.focus();
        note.classList.add('editing');
    });

    note._isEditing = () => isEditing;
    note._setEditing = (value) => {
        isEditing = value;
        textarea.readOnly = !value;
        if (value) {
            note.classList.add('editing');
            textarea.focus();
        } else {
            note.classList.remove('editing');
            textarea.blur();
            updateNoteContent(note, textarea);
        }
    };

    note.addEventListener('mousedown', (e) => {
        if (note._isEditing()) return;
        currentDraggedNote = note;
        dragOffsetX = e.clientX - note.offsetLeft;
        dragOffsetY = e.clientY - note.offsetTop;
        note.style.zIndex = zIndexCounter++;
        e.preventDefault();
    });

    textarea.addEventListener('input', () => {
        const id = note.dataset.id;
        clearTimeout(debounceTimers[id]);
        debounceTimers[id] = setTimeout(() => {
            updateNoteContent(note, textarea);
        }, 400);
    });
}

function isOverTrash(note) {
    const trashRect = TRASH_ZONE.getBoundingClientRect();
    const noteRect = note.getBoundingClientRect();
    return !(
        noteRect.right < trashRect.left ||
        noteRect.left > trashRect.right ||
        noteRect.bottom < trashRect.top ||
        noteRect.top > trashRect.bottom
    );
}

function deleteNote(note) {
    const noteId = note.dataset.id;
    fetch(`/api/notes/${noteId}`, {method: "DELETE"});
    note.remove();
}

function updateNotePosition(note) {
    const noteId = note.dataset.id;
    fetch(`/api/notes/${noteId}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            x: parseInt(note.style.left),
            y: parseInt(note.style.top)
        })
    });
}

function updateNoteContent(note, textarea) {
    const noteId = note.dataset.id;
    fetch(`/api/notes/${noteId}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({content: textarea.value})
    });
}

document.addEventListener('click', (e) => {
    notes.forEach(({note}) => {
        if (!note.contains(e.target) && note._isEditing()) {
            note._setEditing(false);
        }
    });
});

document.addEventListener('mousemove', (e) => {
    if (!currentDraggedNote) return;

    currentDraggedNote.style.left = `${e.clientX - dragOffsetX}px`;
    currentDraggedNote.style.top = `${e.clientY - dragOffsetY}px`;

    if (isOverTrash(currentDraggedNote)) {
        TRASH_ZONE.classList.add('drag-over');
    } else {
        TRASH_ZONE.classList.remove('drag-over');
    }
});

document.addEventListener('mouseup', () => {
    if (!currentDraggedNote) return;

    if (isOverTrash(currentDraggedNote)) {
        deleteNote(currentDraggedNote);
    } else {
        updateNotePosition(currentDraggedNote);
    }

    TRASH_ZONE.classList.remove('drag-over');
    currentDraggedNote = null;
});

document.getElementById('addNoteBtn').addEventListener('click', createNewNote);
window.onload = loadNotes;