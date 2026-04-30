/** @odoo-module **/

import { Component, useState, useEffect, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useRecordObserver } from "@web/model/relational_model/utils";

/**
 * ReciboPreviewWidget — Widget OWL que renderiza una previsualización
 * en tiempo real del recibo, leyendo los campos del form sin guardar.
 *
 * Se registra como field widget y como view widget para el formulario.
 */
export class ReciboPreviewWidget extends Component {
    static template = "wigo_cobranza.ReciboPreviewWidget";
    static props = {
        record: { type: Object, optional: true },
        readonly: { type: Boolean, optional: true },
    };

    setup() {
        this.containerRef = useRef("previewContainer");
        this.state = useState({
            html: "",
            loading: true,
            error: null,
        });

        // Cuando los datos del record cambien, regenerar el HTML
        if (this.props.record) {
            useEffect(
                () => {
                    this._buildPreview();
                },
                () => [
                    // Campos que disparan la actualización del preview
                    this.props.record.data.partner_id,
                    this.props.record.data.codigo_cliente,
                    this.props.record.data.periodo,
                    this.props.record.data.monto,
                    this.props.record.data.monto_en_letras,
                    this.props.record.data.descripcion,
                    this.props.record.data.fecha_pago,
                    this.props.record.data.canal_pago,
                    this.props.record.data.numero,
                    this.props.record.data.firma_nombre_override,
                    this.props.record.data.firma_cargo_override,
                    this.props.record.data.firma_celular_override,
                    this.props.record.data.state,
                ]
            );
        }
    }

    async _buildPreview() {
        const rec = this.props.record;
        if (!rec) return;

        this.state.loading = true;
        this.state.error = null;

        try {
            // Leer configuración del servidor (colores, fuentes, etc.)
            const result = await rec.model.orm.call(
                "wigo.recibo.config",
                "get_config_dict",
                [],
                {}
            );
            const cfg = result || {};

            const d = rec.data;
            const partnerName = d.partner_id && d.partner_id[1] ? d.partner_id[1] : "—";
            const numero = d.numero || "NUEVO";
            const fecha = d.fecha_pago
                ? new Date(d.fecha_pago).toLocaleDateString("es-BO", {
                      day: "2-digit",
                      month: "2-digit",
                      year: "numeric",
                  })
                : "—";
            const periodo = d.periodo || "—";
            const monto = typeof d.monto === "number" ? d.monto.toFixed(2) : "0.00";
            const montoLetras = d.monto_en_letras || "";
            const descripcion = d.descripcion || "Servicio Internet";
            const codigoCli = d.codigo_cliente || "—";
            const canal = d.canal_pago || "—";
            const firmaNombre = d.firma_nombre_override || cfg.firma_nombre || "Firmante";
            const firmaCargo = d.firma_cargo_override || cfg.firma_cargo || "";
            const firmaCel = d.firma_celular_override || cfg.firma_celular || "";

            // Colores y estilos desde config
            const colorP = cfg.color_primario || "#cc0000";
            const colorS = cfg.color_secundario || "#990000";
            const colorHeaderTxt = cfg.color_texto_header || "#ffffff";
            const colorFondo = cfg.color_fondo_recibo || "#ffffff";
            const colorTxtP = cfg.color_texto_principal || "#222222";
            const colorTxtS = cfg.color_texto_secundario || "#666666";
            const colorBorde = cfg.color_borde || "#cccccc";
            const colorFondoMonto = cfg.color_fondo_monto || "#f9f9f9";
            const fuente = cfg.fuente_familia || "Arial, sans-serif";
            const tamBase = cfg.tamano_fuente_base || 12;
            const tamTitulo = cfg.tamano_titulo || 22;
            const tamEmpresa = cfg.tamano_empresa || 14;
            const titNegrita = cfg.fuente_titulo_negrita !== false ? "bold" : "normal";
            const radius = cfg.border_radius || 0;
            const mostrarBanda = cfg.mostrar_banda_decorativa !== false;
            const anchoBanda = cfg.ancho_banda || 8;
            const mostrarPie = cfg.mostrar_pie !== false;
            const textoPie = cfg.texto_pie || "";

            // Header style
            let headerBg = "";
            const estiloHeader = cfg.estilo_header || "gradiente";
            if (estiloHeader === "gradiente") {
                headerBg = `background: linear-gradient(135deg, ${colorP}, ${colorS});`;
            } else if (estiloHeader === "solido") {
                headerBg = `background: ${colorP};`;
            } else if (estiloHeader === "linea") {
                headerBg = `background: transparent; border-bottom: 3px solid ${colorP};`;
            } else {
                headerBg = `background: transparent;`;
            }
            const headerTxtColor = estiloHeader === "linea" || estiloHeader === "sin_fondo"
                ? colorTxtP : colorHeaderTxt;

            // Logo
            const logoHtml = cfg.logo_base64
                ? `<img src="data:image/png;base64,${cfg.logo_base64}" style="max-height:${cfg.logo_ancho || 70}px; max-width:${cfg.logo_ancho || 90}px;"/>`
                : `<div style="font-size:10px;color:${colorTxtS};">[Logo]</div>`;

            const empresaNombre = cfg.empresa_nombre || "WIGO FAST";
            const empresaDireccion = cfg.empresa_direccion || "";
            const empresaCiudad = cfg.empresa_ciudad || "";
            const empresaCelular = cfg.empresa_celular || "";
            const empresaSlogan = cfg.empresa_slogan || "";
            const nit = cfg.empresa_nit || "";

            const tablaHdrTxt = cfg.tabla_header_texto || "DESCRIPCIÓN";
            const tablaMontoTxt = cfg.tabla_monto_texto || "MONTO (Bs.)";
            const mostrarCodigo = cfg.mostrar_columna_codigo !== false;

            // Número grande
            const numHtml = cfg.mostrar_numero_grande !== false
                ? `<div style="font-size:18px;font-weight:bold;color:${colorP};margin-top:4px;">Nº ${numero}</div>`
                : `<div style="font-size:12px;">Nº ${numero}</div>`;

            // Estado badge
            const state = d.state || "borrador";
            const stateColors = { borrador: "#f59e0b", emitido: "#22c55e", anulado: "#ef4444" };
            const stateLabels = { borrador: "BORRADOR", emitido: "EMITIDO", anulado: "ANULADO" };
            const stateBadge = `<span style="background:${stateColors[state]||'#888'};color:#fff;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:bold;">${stateLabels[state]||state}</span>`;

            this.state.html = `
<div style="font-family:${fuente};font-size:${tamBase}px;color:${colorTxtP};background:#e5e7eb;padding:12px;min-height:400px;">
  <div style="background:${colorFondo};border:1px solid ${colorBorde};border-radius:${radius}px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.15);max-width:520px;margin:0 auto;">

    <!-- HEADER -->
    <div style="${headerBg} color:${headerTxtColor}; padding:14px 18px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;">
        <div style="flex:1;">
          <div style="font-size:${tamTitulo}px;font-weight:${titNegrita};letter-spacing:-0.5px;">RECIBO DE COBRANZA</div>
          <div style="font-size:${tamEmpresa}px;font-weight:bold;margin-top:4px;">${empresaNombre}</div>
          ${empresaSlogan ? `<div style="font-size:10px;opacity:0.85;font-style:italic;">${empresaSlogan}</div>` : ""}
          <div style="font-size:10px;margin-top:4px;opacity:0.9;">
            ${empresaDireccion}${empresaDireccion && empresaCiudad ? " · " : ""}${empresaCiudad}
            ${empresaCelular ? `<br/>CEL: ${empresaCelular}` : ""}
            ${nit ? ` &nbsp;|&nbsp; NIT: ${nit}` : ""}
          </div>
        </div>
        <div style="text-align:right;">
          ${logoHtml}
          ${numHtml}
          <div style="margin-top:4px;">${stateBadge}</div>
        </div>
      </div>
    </div>

    <!-- CUERPO -->
    <div style="padding:16px 18px;">

      <!-- Datos cliente -->
      <div style="display:flex;gap:12px;margin-bottom:12px;flex-wrap:wrap;">
        <div style="flex:2;min-width:180px;">
          <div style="font-size:9px;text-transform:uppercase;color:${colorTxtS};letter-spacing:0.5px;margin-bottom:2px;">RECIBIDO DE</div>
          <div style="font-size:13px;font-weight:bold;color:${colorTxtP};">${partnerName}</div>
          ${mostrarCodigo ? `<div style="font-size:10px;color:${colorTxtS};">Código: ${codigoCli}</div>` : ""}
        </div>
        <div style="flex:1;min-width:100px;text-align:right;">
          <div style="font-size:9px;text-transform:uppercase;color:${colorTxtS};letter-spacing:0.5px;margin-bottom:2px;">FECHA</div>
          <div style="font-size:12px;font-weight:bold;color:${colorP};">${fecha}</div>
          <div style="font-size:10px;color:${colorTxtS};">${periodo}</div>
        </div>
      </div>

      <!-- Tabla detalle -->
      <table style="width:100%;border-collapse:collapse;margin:10px 0;font-size:${tamBase}px;">
        <thead>
          <tr style="background:${colorP};color:#fff;">
            <th style="padding:7px 10px;text-align:left;font-weight:bold;">${tablaHdrTxt}</th>
            <th style="padding:7px 10px;text-align:right;width:110px;font-weight:bold;">${tablaMontoTxt}</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom:1px solid ${colorBorde};">
            <td style="padding:10px;">${descripcion}</td>
            <td style="padding:10px;text-align:right;">${monto}</td>
          </tr>
          <tr style="border-bottom:1px solid ${colorBorde};">
            <td style="padding:6px 10px;font-size:10px;color:${colorTxtS};">Canal: ${canal}</td>
            <td style="padding:6px 10px;text-align:right;font-size:10px;color:${colorTxtS};">&nbsp;</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td style="padding:10px;font-weight:bold;font-size:${tamBase}px;">TOTAL</td>
            <td style="padding:10px;text-align:right;font-weight:bold;font-size:${parseInt(tamBase)+2}px;color:${colorP};border-top:2px solid ${colorP};">${monto} Bs.</td>
          </tr>
        </tfoot>
      </table>

      <!-- Monto en letras -->
      <div style="background:${colorFondoMonto};border-left:4px solid ${colorP};padding:10px 12px;margin:10px 0;border-radius:${radius}px;">
        <span style="font-size:10px;font-weight:bold;text-transform:uppercase;color:${colorTxtS};">SON: </span>
        <span style="font-size:${tamBase}px;color:${colorTxtP};">${montoLetras}</span>
      </div>

      ${mostrarBanda ? `<div style="background:${colorP};height:${anchoBanda}px;margin:12px 0;border-radius:${radius}px;"></div>` : ""}

      <!-- Firma -->
      <div style="display:flex;gap:20px;margin-top:12px;">
        <div style="flex:1;text-align:center;border-top:1px solid ${colorBorde};padding-top:10px;">
          <div style="font-weight:bold;font-size:${tamBase}px;">${firmaNombre}</div>
          <div style="font-size:10px;color:${colorTxtS};">${firmaCargo}</div>
          ${firmaCel ? `<div style="font-size:9px;color:${colorTxtS};">CEL: ${firmaCel}</div>` : ""}
        </div>
        <div style="flex:1;text-align:center;border-top:1px solid ${colorBorde};padding-top:10px;">
          <div style="font-weight:bold;font-size:${tamBase}px;">ENTREGUE CONFORME</div>
          <div style="font-size:10px;color:${colorTxtS};margin-top:6px;">Nombre: ___________________</div>
          <div style="font-size:10px;color:${colorTxtS};">CI: ___________________</div>
        </div>
      </div>

      ${mostrarPie && textoPie ? `
      <div style="text-align:center;margin-top:12px;font-size:10px;color:${colorTxtS};border-top:1px dashed ${colorBorde};padding-top:8px;">
        ${textoPie}
      </div>` : ""}
    </div>

  </div>
</div>`;
        } catch (e) {
            this.state.error = "Error al cargar la configuración: " + e.message;
        } finally {
            this.state.loading = false;
        }
    }
}

// Template OWL (declarado en XML, referenciado aquí)
registry.category("fields").add("recibo_preview", {
    component: ReciboPreviewWidget,
    supportedTypes: ["char"],
});
