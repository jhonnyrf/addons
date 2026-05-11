import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, {
   
    async saveRecord(recordID) {
        const result = await super.saveRecord(recordID);
        
        const iframe = document.querySelector('#recibo_iframe');
        if (iframe) {
            const currentSrc = iframe.getAttribute('src');
            iframe.src = currentSrc; 
        }
        
        return result;
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
