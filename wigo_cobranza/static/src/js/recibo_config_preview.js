/** @odoo-module **/

import { Component, useState, useEffect, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * ReciboConfigPreview — Widget para la vista de configuración.
 * Renderiza una mini-preview del recibo en tiempo real al editar
 * los campos de color, tipografía, layout, etc.
 */
export class ReciboConfigPreview extends Component {
    static template = "wigo_cobranza.ReciboConfigPreview";

    static props = {
        record: { type: Object },
        readonly: { type: Boolean, optional: true },
        node: { type: Object, optional: true },
        archInfo: { type: Object, optional: true },
        fields: { type: Object, optional: true },
        options: { type: Object, optional: true },
    };

    setup() {
        this.htmlContainer = useRef("configHtmlContainer");
        this.state = useState({ loading: true });

        useEffect(
            () => { this._render(); },
            () => {
                const d = this.props.record.data;
                return [
                    d.empresa_nombre, d.empresa_direccion, d.empresa_ciudad,
                    d.empresa_celular, d.empresa_nit, d.empresa_slogan,
                    d.color_primario, d.color_secundario, d.color_texto_header,
                    d.color_fondo_recibo, d.color_texto_principal,
                    d.color_texto_secundario, d.color_borde, d.color_fondo_monto,
                    d.fuente_familia, d.tamano_fuente_base, d.tamano_titulo,
                    d.tamano_empresa, d.fuente_titulo_negrita,
                    d.estilo_header, d.border_radius,
                    d.mostrar_banda_decorativa, d.ancho_banda,
                    d.mostrar_numero_grande, d.layout_logo,
                    d.tabla_header_texto, d.tabla_monto_texto,
                    d.firma_nombre, d.firma_cargo, d.firma_celular,
                    d.mostrar_pie, d.texto_pie,
                    d.logo,
                ];
            }
        );
    }

    _render() {
        const d = this.props.record.data;

        const colorP   = d.color_primario || "#cc0000";
        const colorS   = d.color_secundario || "#990000";
        const colorHdr = d.color_texto_header || "#ffffff";
        const colorFondo = d.color_fondo_recibo || "#ffffff";
        const colorTxtP  = d.color_texto_principal || "#222222";
        const colorTxtS  = d.color_texto_secundario || "#666666";
        const colorBorde = d.color_borde || "#cccccc";
        const colorFondoMonto = d.color_fondo_monto || "#f9f9f9";
        const fuente   = d.fuente_familia || "Arial, sans-serif";
        const tamBase  = d.tamano_fuente_base || 12;
        const tamTitulo = d.tamano_titulo || 22;
        const tamEmpresa = d.tamano_empresa || 14;
        const titNegrita = d.fuente_titulo_negrita !== false ? "bold" : "normal";
        const radius   = d.border_radius || 0;
        const mostrarBanda = d.mostrar_banda_decorativa !== false;
        const anchoBanda = d.ancho_banda || 8;
        const mostrarPie = d.mostrar_pie !== false;
        const textoPie = d.texto_pie || "";
        const tablaHdr = d.tabla_header_texto || "DESCRIPCIÓN";
        const tablaMontoHdr = d.tabla_monto_texto || "MONTO (Bs.)";
        const empresaNombre = d.empresa_nombre || "WIGO FAST";
        const empresaDireccion = d.empresa_direccion || "";
        const empresaCiudad = d.empresa_ciudad || "";
        const empresaCelular = d.empresa_celular || "";
        const empresaNit = d.empresa_nit || "";
        const empresaSlogan = d.empresa_slogan || "";
        const firmaNombre = d.firma_nombre || "Lic. Patricia Villarroel";
        const firmaCargo = d.firma_cargo || "CONTABILIDAD";
        const firmaCel = d.firma_celular || "";

        const estilo = d.estilo_header || "gradiente";
        let headerBg = "";
        let headerTxtColor = colorHdr;
        if (estilo === "gradiente") {
            headerBg = `background:linear-gradient(135deg,${colorP},${colorS});`;
        } else if (estilo === "solido") {
            headerBg = `background:${colorP};`;
        } else if (estilo === "linea") {
            headerBg = `background:transparent;border-bottom:3px solid ${colorP};`;
            headerTxtColor = colorTxtP;
        } else {
            headerBg = `background:transparent;`;
            headerTxtColor = colorTxtP;
        }

        const html = `
<div style="font-family:${fuente};font-size:${Math.round(tamBase*0.9)}px;color:${colorTxtP};background:#e5e7eb;padding:8px;border-radius:4px;">
  <div style="background:${colorFondo};border:1px solid ${colorBorde};border-radius:${radius}px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,0.12);">

    <div style="${headerBg}color:${headerTxtColor};padding:10px 14px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <div style="font-size:${Math.round(tamTitulo*0.85)}px;font-weight:${titNegrita};">RECIBO DE COBRANZA</div>
          <div style="font-size:${Math.round(tamEmpresa*0.85)}px;font-weight:bold;margin-top:2px;">${empresaNombre}</div>
          ${empresaSlogan ? `<div style="font-size:9px;opacity:0.85;font-style:italic;">${empresaSlogan}</div>` : ""}
          <div style="font-size:9px;margin-top:3px;opacity:0.9;">
            ${[empresaDireccion, empresaCiudad].filter(Boolean).join(" · ")}
            ${empresaCelular ? ` · CEL: ${empresaCelular}` : ""}
            ${empresaNit ? ` · NIT: ${empresaNit}` : ""}
          </div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:13px;font-weight:bold;">Nº 0001</div>
          <span style="background:#22c55e;color:#fff;padding:1px 6px;border-radius:10px;font-size:8px;font-weight:bold;">EMITIDO</span>
        </div>
      </div>
    </div>

    <div style="padding:12px 14px;">
      <div style="display:flex;gap:10px;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid ${colorBorde};">
        <div style="flex:2;">
          <div style="font-size:8px;text-transform:uppercase;color:${colorTxtS};">RECIBIDO DE</div>
          <div style="font-size:12px;font-weight:bold;">Cliente Ejemplo</div>
          <div style="font-size:9px;color:${colorTxtS};">Código: WIG-001</div>
        </div>
        <div style="flex:1;text-align:right;">
          <div style="font-size:8px;text-transform:uppercase;color:${colorTxtS};">FECHA</div>
          <div style="font-size:11px;font-weight:bold;color:${colorP};">01/05/2025</div>
          <div style="font-size:9px;color:${colorTxtS};">Mayo/2025</div>
        </div>
      </div>

      <table style="width:100%;border-collapse:collapse;font-size:${Math.round(tamBase*0.85)}px;margin-bottom:8px;">
        <thead>
          <tr style="background:${colorP};color:#fff;">
            <th style="padding:5px 8px;text-align:left;">${tablaHdr}</th>
            <th style="padding:5px 8px;text-align:right;">${tablaMontoHdr}</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom:1px solid ${colorBorde};">
            <td style="padding:7px 8px;">Servicio Internet Mayo/2025</td>
            <td style="padding:7px 8px;text-align:right;">150.00</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td style="padding:6px 8px;font-weight:bold;">TOTAL</td>
            <td style="padding:6px 8px;text-align:right;font-weight:bold;color:${colorP};border-top:2px solid ${colorP};">150.00 Bs.</td>
          </tr>
        </tfoot>
      </table>

      <div style="background:${colorFondoMonto};border-left:3px solid ${colorP};padding:7px 10px;border-radius:${radius}px;margin-bottom:8px;font-size:9px;">
        <b>SON:</b> Ciento cincuenta 00/100 Bolivianos
      </div>

      ${mostrarBanda ? `<div style="background:${colorP};height:${anchoBanda}px;border-radius:${radius}px;margin-bottom:10px;"></div>` : ""}

      <div style="display:flex;gap:10px;font-size:9px;">
        <div style="flex:1;text-align:center;border-top:1px solid ${colorBorde};padding-top:6px;">
          <div style="font-weight:bold;">${firmaNombre}</div>
          <div style="color:${colorTxtS};">${firmaCargo}</div>
          ${firmaCel ? `<div style="color:${colorTxtS};">CEL: ${firmaCel}</div>` : ""}
        </div>
        <div style="flex:1;text-align:center;border-top:1px solid ${colorBorde};padding-top:6px;">
          <div style="font-weight:bold;">ENTREGUE CONFORME</div>
          <div style="color:${colorTxtS};">Nombre: ___________</div>
          <div style="color:${colorTxtS};">CI: ___________</div>
        </div>
      </div>

      ${mostrarPie && textoPie
        ? `<div style="text-align:center;margin-top:8px;font-size:9px;color:${colorTxtS};border-top:1px dashed ${colorBorde};padding-top:6px;">${textoPie}</div>`
        : ""}
    </div>
  </div>

  <div style="text-align:center;margin-top:4px;font-size:9px;color:#999;">
    ✅ Vista previa en tiempo real · Refleja los cambios al instante
  </div>
</div>`;

        if (this.htmlContainer.el) {
            this.htmlContainer.el.innerHTML = html;
        }
        this.state.loading = false;
    }
}

registry.category("view_widgets").add("recibo_config_preview", {
    component: ReciboConfigPreview,
});
