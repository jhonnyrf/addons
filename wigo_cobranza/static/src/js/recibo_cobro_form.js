/** Formulario de Recibo Cobro - Actualiza preview al guardar */
odoo.define('wigo_cobranza.recibo_form', function(require) {
    "use strict";

    const FormController = require('web.FormController');

    FormController.include({
        /**
         * Override de saveRecord para recargar el iframe del preview
         */
        saveRecord: function(recordID) {
            const self = this;
            return this._super.apply(this, arguments).then(function(result) {
                // Recargar iframe del preview
                const iframe = document.querySelector('#recibo_iframe');
                if (iframe) {
                    const currentSrc = iframe.getAttribute('src');
                    iframe.src = currentSrc; // Recarga el iframe
                }
                return result;
            });
        },

        /**
         * Override de reload para recargar iframe también
         */
        reload: function() {
            const self = this;
            const result = this._super.apply(this, arguments);
            
            // Recargar iframe después de recargar datos
            if (result && result.then) {
                return result.then(function() {
                    const iframe = document.querySelector('#recibo_iframe');
                    if (iframe) {
                        const currentSrc = iframe.getAttribute('src');
                        iframe.src = currentSrc;
                    }
                });
            }
            return result;
        }
    });
});
