/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

/**
 * SemaforoWidget — círculo de color + texto descriptivo
 * para el campo estado_pago en wigo.pago.estado y modelos relacionados.
 */
export class SemaforoWidget extends Component {
    static template = "wigo_cobranza.SemaforoWidget";
    static props = {
        ...standardFieldProps,
    };

    get value() {
        return this.props.record.data[this.props.name];
    }

    get config() {
        const map = {
            al_dia: {
                color: "#22c55e",
                glow: "0 0 8px 2px rgba(34,197,94,0.45)",
                icon: "●",
                label: "Al día",
                textColor: "#15803d",
                bg: "#f0fdf4",
                border: "#86efac",
            },
            pendiente: {
                color: "#f59e0b",
                glow: "0 0 8px 2px rgba(245,158,11,0.40)",
                icon: "●",
                label: "Pendiente",
                textColor: "#92400e",
                bg: "#fffbeb",
                border: "#fcd34d",
            },
            deuda_parcial: {
                color: "#f97316",
                glow: "0 0 8px 2px rgba(249,115,22,0.40)",
                icon: "●",
                label: "Deuda parcial",
                textColor: "#9a3412",
                bg: "#fff7ed",
                border: "#fdba74",
            },
            mora: {
                color: "#ef4444",
                glow: "0 0 10px 3px rgba(239,68,68,0.50)",
                icon: "●",
                label: "En mora",
                textColor: "#991b1b",
                bg: "#fef2f2",
                border: "#fca5a5",
            },
            baja_definitiva: {
                color: "#6b7280",
                glow: "none",
                icon: "●",
                label: "Baja definitiva",
                textColor: "#374151",
                bg: "#f9fafb",
                border: "#d1d5db",
            },
        };
        return map[this.value] || {
            color: "#d1d5db",
            glow: "none",
            icon: "●",
            label: this.value || "—",
            textColor: "#6b7280",
            bg: "#f9fafb",
            border: "#e5e7eb",
        };
    }
}

registry.category("fields").add("semaforo_pago", {
    component: SemaforoWidget,
});
