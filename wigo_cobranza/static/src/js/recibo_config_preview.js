

import { Component, useState, useEffect, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";


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
        this.orm = useService("orm");
        this.state = useState({ loading: true });

      onMounted(() => {
        this._render();
      });

     
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

  
    _getLogoSrc() {
        const d = this.props.record.data;
        const logo = d.logo;
        if (!logo) return null;

    
        if (typeof logo === "object" && logo.data) {
            return `data:image/png;base64,${logo.data}`;
        }
     
        if (typeof logo === "string" && logo.length > 50) {
            return `data:image/png;base64,${logo}`;
        }
       
        const recId = this.props.record.resId;
        if (recId) {
            return `/web/image/wigo.recibo.config/${recId}/logo`;
        }
        return null;
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

      
        const logoSrc = this._getLogoSrc();
        const la = d.logo_ancho || 90;
        const logoHtml = logoSrc
            ? `<img src="${logoSrc}" style="max-height:${la}px;max-width:${la * 2}px;display:block;margin-left:auto;" onerror="this.style.display='none'"/>`
            : `<div style="width:${la}px;height:${Math.round(la*0.5)}px;background:rgba(255,255,255,0.2);border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:9px;color:rgba(255,255,255,0.6);margin-left:auto;">sin logo</div>`;

        const html = `
<div style="font-family:${fuente};font-size:${Math.round(tamBase*0.9)}px;color:${colorTxtP};background:#e5e7eb;padding:6px;border-radius:4px;">
  <div style="background:${colorFondo};border:1px solid ${colorBorde};border-radius:${radius}px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,0.12);">

    <!-- HEADER -->
    <div style="${headerBg}color:${headerTxtColor};padding:8px 12px;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td valign="top" width="62%">
            <div style="font-size:${Math.round(tamTitulo*0.82)}px;font-weight:${titNegrita};">RECIBO DE COBRANZA</div>
            <div style="font-size:${Math.round(tamEmpresa*0.82)}px;font-weight:bold;margin-top:2px;">${empresaNombre}</div>
            ${empresaSlogan ? `<div style="font-size:8px;opacity:0.85;font-style:italic;">${empresaSlogan}</div>` : ""}
            <div style="font-size:8px;margin-top:2px;opacity:0.9;line-height:1.4;">
              ${empresaDireccion}${empresaCiudad ? "<br/>" + empresaCiudad : ""}${empresaCelular ? "<br/>CEL: " + empresaCelular : ""}${empresaNit ? " | NIT: " + empresaNit : ""}
            </div>
          </td>
          <td valign="top" width="38%" align="right">
            ${logoHtml}
            <div style="font-size:13px;font-weight:bold;margin-top:4px;text-align:right;">Nº RC-0001</div>
          </td>
        </tr>
      </table>
    </div>

    <!-- CUERPO -->
    <div style="padding:8px 12px;">
      <!-- Cliente / Fecha -->
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:7px;padding-bottom:6px;border-bottom:1px solid ${colorBorde};">
        <tr>
          <td width="60%" valign="top">
            <div style="font-size:8px;text-transform:uppercase;color:${colorTxtS};letter-spacing:0.8px;margin-bottom:1px;">RECIBIDO DE:</div>
            <div style="font-size:11px;font-weight:bold;">Cliente Ejemplo</div>
            <div style="font-size:9px;color:${colorTxtS};">Código: WIG-001</div>
          </td>
          <td width="40%" valign="top" align="right">
            <div style="font-size:8px;text-transform:uppercase;color:${colorTxtS};letter-spacing:0.8px;margin-bottom:1px;">FECHA:</div>
            <div style="font-size:11px;font-weight:bold;color:${colorP};">01/05/2026</div>            
          </td>
        </tr>
      </table>

      <!-- Tabla -->
      <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:${Math.round(tamBase*0.85)}px;margin-bottom:6px;">
        <thead>
          <tr style="background:${colorP};color:#fff;">
            <th style="padding:5px 8px;text-align:left;">${tablaHdr}</th>
            <th style="padding:5px 8px;text-align:right;width:110px;white-space:nowrap;">${tablaMontoHdr}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:6px 8px;border-bottom:1px solid ${colorBorde};">Servicio Internet Mayo/2026</td>
            <td style="padding:6px 8px;text-align:right;border-bottom:1px solid ${colorBorde};">150,00</td>
          </tr>
        </tbody>
        <tfoot>
          <tr style="background:${colorFondoMonto};">
            <td style="padding:5px 8px;font-size:9px;color:${colorTxtP};"><b>SON:</b> Ciento cincuenta 00/100 Bolivianos</td>
            <td style="padding:5px 8px;text-align:right;font-weight:bold;color:${colorP};border-top:2px solid ${colorP};white-space:nowrap;">TOTAL BS.&nbsp;&nbsp;150,00</td>
          </tr>
        </tfoot>
      </table>

      ${mostrarBanda ? `<div style="background:${colorP};height:${anchoBanda}px;border-radius:2px;margin:6px 0 8px 0;"></div>` : '<div style="margin-bottom:10px;"></div>'}

      <!-- Firmas -->
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td width="44%" valign="bottom">
            <div style="height:20px;"></div>
            <div style="border-top:1px solid ${colorBorde};padding-top:5px;text-align:center;">
              <div style="font-weight:bold;font-size:10px;">${firmaNombre}</div>
              <div style="font-size:9px;color:${colorTxtS};">${firmaCargo}</div>
              ${firmaCel ? `<div style="font-size:8px;color:${colorTxtS};">CEL: ${firmaCel}</div>` : ""}
            </div>
          </td>
          <td width="12%"></td>
          <td width="44%" valign="bottom">
            <div style="height:20px;"></div>
            <div style="border-top:1px solid ${colorBorde};padding-top:5px;text-align:center;">
              <div style="font-weight:bold;font-size:10px;">ENTREGUE CONFORME</div>
              <div style="font-size:9px;color:${colorTxtS};margin-top:3px;text-align:left;">Nombre: ________________</div>
              <div style="font-size:9px;color:${colorTxtS};margin-top:2px;text-align:left;">CI: ________________</div>
            </div>
          </td>
        </tr>
      </table>

      ${mostrarPie && textoPie ? `<div style="text-align:center;margin-top:8px;font-size:9px;color:${colorTxtS};border-top:1px dashed ${colorBorde};padding-top:6px;">${textoPie}</div>` : ""}
    </div>
  </div>

  <div style="text-align:center;margin-top:3px;font-size:9px;color:#999;">
    Vista previa en tiempo real
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
