/** @odoo-module **/

console.log("Clipboard upload cargado");

const ACCEPTED_MIME_TYPES = new Set(["image/jpeg", "image/jpg", "image/png", "application/pdf"]);
const ACCEPTED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png"];

function stopEvent(event) {
    event.preventDefault();
    event.stopPropagation();
    if (typeof event.stopImmediatePropagation === "function") {
        event.stopImmediatePropagation();
    }
}

function getClipboardZone() {
    return document.querySelector(".o_contract_clipboard_zone");
}

function getClipboardRoot(referenceElement = null) {
    if (referenceElement instanceof Element) {
        const root = referenceElement.closest('[data-contract-clipboard-root="1"]');
        if (root) {
            return root;
        }
    }

    return document.querySelector('[data-contract-clipboard-root="1"]');
}

function getClipboardZone(referenceElement = null) {
    const root = getClipboardRoot(referenceElement);
    if (root) {
        return root.querySelector(".o_contract_clipboard_zone");
    }

    return document.querySelector(".o_contract_clipboard_zone");
}

function focusClipboardZone(referenceElement = null) {
    const zone = getClipboardZone(referenceElement);
    if (!zone) {
        return;
    }

    // The previous approach depended on focus/selection heuristics and nested DOM
    // inspection. That made paste behavior unstable after context-menu actions.
    // By focusing the zone explicitly, we keep the clipboard target deterministic.
    if (document.activeElement !== zone) {
        zone.focus({ preventScroll: true });
    }
}

function isAcceptedFile(file) {
    if (!file) {
        return false;
    }
    const fileName = (file.name || "").toLowerCase();
    return ACCEPTED_MIME_TYPES.has(file.type) || ACCEPTED_EXTENSIONS.some((ext) => fileName.endsWith(ext));
}

function getContractAttachmentWidget(referenceElement = null) {
    const root = getClipboardRoot(referenceElement);
    const scope = root || document;
    const field = scope.querySelector(".o_contract_attachment_field");
    if (!field) {
        return null;
    }

    const fileInput = field.querySelector('input[type="file"]');
    if (!fileInput) {
        return null;
    }

    return { field, fileInput };
}

function openNativeFilePicker(referenceElement = null) {
    const widget = getContractAttachmentWidget(referenceElement);
    if (!widget) {
        return;
    }

    // Keep this synchronous and inside the user gesture so browsers allow the dialog.
    widget.fileInput.click();
}

function setDraggingState(referenceElement, isDragging) {
    const zone = getClipboardZone(referenceElement);
    if (!zone) {
        return;
    }
    zone.classList.toggle("is-dragover", isDragging);
}

function isDropAllowedTarget(target) {
    if (!(target instanceof Element)) {
        return false;
    }
    return Boolean(target.closest(".o_contract_attachment_field") || target.closest(".o_contract_clipboard_zone"));
}

function dispatchNativeFiles(fileInput, files) {
    try {
        const dataTransfer = new DataTransfer();
        for (const file of files) {
            dataTransfer.items.add(file);
        }
        fileInput.files = dataTransfer.files;
        fileInput.dispatchEvent(new Event("change", { bubbles: true }));
        return true;
    } catch (error) {
        console.error("No se pudo inyectar el archivo en el input nativo:", error);
        return false;
    }
}

async function handleFiles(files, referenceElement = null) {
    const widget = getContractAttachmentWidget(referenceElement);
    if (!widget) {
        return;
    }

    const validFiles = files.filter(isAcceptedFile);
    if (!validFiles.length) {
        return;
    }

    dispatchNativeFiles(widget.fileInput, validFiles);
}

function handleClipboardPaste(event) {
    try {
        const files = Array.from(event.clipboardData?.files || []).filter(isAcceptedFile);
        if (!files.length) {
            return;
        }

        stopEvent(event);
        void handleFiles(files, event.target instanceof Element ? event.target : document.activeElement);
    } catch (error) {
        console.error("Error clipboard:", error);
    }
}

function handleZoneMouseEnter(referenceElement) {
    focusClipboardZone(referenceElement);
}

function handleZoneClick(event) {
    try {
        if (event.target instanceof Element && event.target.closest("a, button, input, textarea, select, label")) {
            return;
        }

        focusClipboardZone(event.target instanceof Element ? event.target : null);
        stopEvent(event);
        openNativeFilePicker(event.target instanceof Element ? event.target : null);
    } catch (error) {
        console.error("Error opening file picker:", error);
    }
}

function handleZoneKeydown(event) {
    try {
        if (event.key !== "Enter" && event.key !== " ") {
            return;
        }

        stopEvent(event);
        openNativeFilePicker(event.target instanceof Element ? event.target : null);
    } catch (error) {
        console.error("Error opening file picker with keyboard:", error);
    }
}

function handleZoneDragEnter(event) {
    try {
        const referenceElement = event.target instanceof Element ? event.target : null;
        focusClipboardZone(referenceElement);
        stopEvent(event);
        setDraggingState(referenceElement, true);
        if (event.dataTransfer) {
            event.dataTransfer.dropEffect = "copy";
        }
    } catch (error) {
        console.error("Error dragenter:", error);
    }
}

function handleZoneDragOver(event) {
    try {
        const referenceElement = event.target instanceof Element ? event.target : null;
        stopEvent(event);
        setDraggingState(referenceElement, true);
        if (event.dataTransfer) {
            event.dataTransfer.dropEffect = "copy";
        }
    } catch (error) {
        console.error("Error dragover:", error);
    }
}

function handleZoneDrop(event) {
    try {
        const referenceElement = event.target instanceof Element ? event.target : null;
        const files = Array.from(event.dataTransfer?.files || []).filter(isAcceptedFile);
        stopEvent(event);
        setDraggingState(referenceElement, false);

        if (!files.length) {
            return;
        }

        void handleFiles(files, referenceElement);
    } catch (error) {
        console.error("Error drag & drop:", error);
    }
}

function handleZoneDragLeave(event) {
    try {
        const referenceElement = event.target instanceof Element ? event.target : null;
        const zone = getClipboardZone(referenceElement);
        if (!zone || !(event.target instanceof Element)) {
            return;
        }

        if (!zone.contains(event.target)) {
            return;
        }

        const relatedTarget = event.relatedTarget;
        if (relatedTarget instanceof Node && zone.contains(relatedTarget)) {
            return;
        }

        setDraggingState(referenceElement, false);
    } catch (error) {
        console.error("Error dragleave:", error);
    }
}

window.addEventListener(
    "paste",
    handleClipboardPaste,
    true
);

window.addEventListener(
    "dragenter",
    (event) => {
        if (!isDropAllowedTarget(event.target)) {
            return;
        }

        handleZoneDragEnter(event);
    },
    true
);

window.addEventListener(
    "dragover",
    (event) => {
        if (!isDropAllowedTarget(event.target)) {
            return;
        }

        handleZoneDragOver(event);
    },
    true
);

window.addEventListener(
    "drop",
    (event) => {
        if (!isDropAllowedTarget(event.target)) {
            return;
        }

        handleZoneDrop(event);
    },
    true
);

window.addEventListener(
    "dragleave",
    handleZoneDragLeave,
    true
);

window.addEventListener(
    "mouseover",
    (event) => {
        if (!(event.target instanceof Element) || !event.target.closest(".o_contract_clipboard_zone")) {
            return;
        }

        handleZoneMouseEnter(event.target);
    },
    true
);

window.addEventListener(
    "click",
    (event) => {
        if (!(event.target instanceof Element) || !event.target.closest(".o_contract_clipboard_zone")) {
            return;
        }

        handleZoneClick(event);
    },
    true
);

window.addEventListener(
    "keydown",
    (event) => {
        const zone = getClipboardZone();
        if (!zone || document.activeElement !== zone) {
            return;
        }

        handleZoneKeydown(event);
    },
    true
);