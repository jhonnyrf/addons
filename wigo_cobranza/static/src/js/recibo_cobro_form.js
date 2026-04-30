/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

/**
 * Recibo Cobro Form - Actualiza preview (iframe) al guardar o recargar
 */
patch(FormController.prototype, {
    /**
     * Override de saveRecord para recargar el iframe del preview
     */
    async saveRecord(recordID) {
        const result = await super.saveRecord(recordID);
        
        // Recargar iframe del preview
        const iframe = document.querySelector('#recibo_iframe');
        if (iframe) {
            const currentSrc = iframe.getAttribute('src');
            iframe.src = currentSrc; // Recarga el iframe
        }
        
        return result;
    },

    /**
     * Override de reload para recargar iframe también
     */
    async reload() {
        const result = await super.reload();
        
        // Recargar iframe después de recargar datos
        const iframe = document.querySelector('#recibo_iframe');
        if (iframe) {
            const currentSrc = iframe.getAttribute('src');
            iframe.src = currentSrc;
        }
        
        return result;
    }
});
