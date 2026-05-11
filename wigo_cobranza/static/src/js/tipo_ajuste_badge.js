import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

export class TipoAjusteBadge extends Component {
    static template = "wigo_cobranza.TipoAjusteBadge";
    static props = {
        ...standardFieldProps,
    };

    get value() {
        return this.props.record.data[this.props.name];
    }

    get label() {
        const value = this.value;
        if (!value) {
            return "—";
        }
        if (typeof value === "string") {
            return value;
        }
        return value.display_name || value.name || value[1] || String(value);
    }

    get colorIndex() {
        const idx = parseInt(this.props.record.data.tipo_ajuste_color, 10);
        return Number.isFinite(idx) ? idx : 0;
    }

    get className() {
        return `o_tag o_tag_color_${this.colorIndex}`;
    }

    get style() {
        return "display:inline-flex;align-items:center;padding:2px 10px;border-radius:999px;white-space:nowrap;";
    }
}

registry.category("fields").add("tipo_ajuste_badge", {
    component: TipoAjusteBadge,
});