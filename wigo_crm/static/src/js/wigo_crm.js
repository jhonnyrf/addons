/** @odoo-module **/

/**
 * Wigo CRM
 * Intercepta la creación rápida del kanban para abrir el formulario completo.
 * - Botón "Nuevo" del panel superior → abre formulario completo
 * - Botón "+" de cada columna → abre formulario completo
 */

import { patch } from "@web/core/utils/patch";
import { KanbanController } from "@web/views/kanban/kanban_controller";

patch(KanbanController.prototype, {
    /**
     * openQuickCreate se llama cuando el usuario pulsa "Nuevo" o "+"
     * en el kanban. Lo reemplazamos para abrir directamente el formulario.
     */
    async openQuickCreate(group) {
        // Solo interceptar en vistas de crm.lead (el kanban del pipeline)
        if (this.props.resModel !== "crm.lead") {
            return super.openQuickCreate(...arguments);
        }
        // Abrir el formulario completo de creación
        await this.createRecord();
    },
});

// Ocultar botón Pivot en vistas del modelo crm.lead
function hidePivotButtonIfCrmLead() {
    const candidates = document.querySelectorAll("button, a");
    for (const el of candidates) {
        const dataViewType = (el.getAttribute("data-view-type") || "").toLowerCase();
        const className = (el.className || "").toString().toLowerCase();
        const title = (el.getAttribute("title") || "").toLowerCase();
        const aria = (el.getAttribute("aria-label") || "").toLowerCase();
        const text = (el.textContent || "").toLowerCase();
        const looksLikePivot =
            dataViewType === "pivot" ||
            className.includes("pivot") ||
            title.includes("tabla dinámica") ||
            title.includes("pivot") ||
            aria.includes("tabla dinámica") ||
            aria.includes("pivot") ||
            text.includes("tabla dinámica") ||
            text.includes("pivot");

        if (looksLikePivot && (className.includes("switch") || className.includes("cp_"))) {
            el.style.display = "none";
        }
    }
}

function bootPivotHider() {
    hidePivotButtonIfCrmLead();
    if (!document.body) {
        return;
    }
    const observer = new MutationObserver(() => hidePivotButtonIfCrmLead());
    observer.observe(document.body, { childList: true, subtree: true });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootPivotHider, { once: true });
} else {
    bootPivotHider();
}
