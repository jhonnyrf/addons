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
