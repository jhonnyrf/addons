import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);

        this._onBeforeUnload = (event) => {
            const root = this.model?.root;
            if (root?.resModel === 'wigo.pago.estado' && root?.data?.contabilidad_editable) {
                event.preventDefault();
                event.returnValue = '';
                // mark to skip autosave during unload sequence
                window._wigo_disable_autosave = true;
                return '';
            }
            return undefined;
        };

        window.addEventListener('beforeunload', this._onBeforeUnload);
        // ensure the flag exists
        if (typeof window._wigo_disable_autosave === 'undefined') {
            window._wigo_disable_autosave = false;
        }
    },

    destroy() {
        if (this._onBeforeUnload) {
            window.removeEventListener('beforeunload', this._onBeforeUnload);
        }
        return super.destroy(...arguments);
    },
   
    async saveRecord(recordID) {
        const root = this.model?.root;

        // If this save is not user-initiated and autosave is disabled
        // during unload, skip saving to avoid accidental persistence on reload.
        if (!this._wigo_save_via_button && window._wigo_disable_autosave && root?.data?.contabilidad_editable) {
            console.log('Skipping autosave: contabilidad_editable and unload in progress');
            // reset flag so future saves behave normally
            window._wigo_disable_autosave = false;
            return Promise.resolve();
        }

        const result = await super.saveRecord(recordID);

        const iframe = document.querySelector('#recibo_iframe');
        if (iframe) {
            const currentSrc = iframe.getAttribute('src');
            iframe.src = currentSrc;
        }

        // After saving and reloading the form, explicitly read the
        // `contabilidad_editable` flag from the server and open the
        // justification wizard if needed. This is more reliable than
        // trying to read transient client-side state before save.
       /*  if (root?.resModel === "wigo.pago.estado" && root?.resId) {
            await this.reload();
            const readResult = await this.env.services.orm.call(
                "wigo.pago.estado",
                "read",
                [[root.resId], ['contabilidad_editable']],
                {}
            );
            const contabilidadEditable = Array.isArray(readResult) && readResult[0] && readResult[0].contabilidad_editable;
            if (contabilidadEditable) {
                const action = {
                    type: 'ir.actions.act_window',
                    name: 'Justificación de edición contable',
                    res_model: 'wigo.pago.estado.contable.justification.wizard',
                    view_mode: 'form',
                    target: 'new',
                    context: { default_pago_id: root.resId },
                };
                await this.env.services.action.doAction(action);
            }
        } */

        return result;
    },
    async saveButtonClicked(params = {}) {
        // mark this save as user-initiated so saveRecord won't treat it as autosave
        this._wigo_save_via_button = true;
        try {
        const root = this.model?.root;
        if (root?.resModel === 'wigo.pago.estado' && root?.resId) {
            // Check the `contabilidad_editable` field directly from root.data
            // (it's included in the form as invisible="1", so it has been computed with context).
            const contabilidadEditable = root.data?.contabilidad_editable;
            if (contabilidadEditable) {
                const action = await this.env.services.orm.call(
                    'wigo.pago.estado',
                    'action_open_contable_justification_wizard',
                    [root.resId],
                    {}
                );

                const confirmed = await new Promise((resolve) => {
                    this.env.services.action.doAction(action, {
                        onClose: (closeInfo) => {
                            resolve(Boolean(closeInfo?.justification_confirmed));
                        },
                    });
                });

                if (!confirmed) {
                    return Promise.resolve();
                }

                return super.saveButtonClicked(params);
            }
        }

        return super.saveButtonClicked(params);
        } finally {
            this._wigo_save_via_button = false;
            // ensure we reset autosave block after user action
            window._wigo_disable_autosave = false;
        }
    },

   
    async reload() {
        const result = await super.reload();
        

        const iframe = document.querySelector('#recibo_iframe');
        if (iframe) {
            const currentSrc = iframe.getAttribute('src');
            iframe.src = currentSrc;
        }
        
        return result;
    }
});
