/** @odoo-module **/

import { Component, useState, useEffect, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * ReciboLivePreview — Widget para <widget name="recibo_live_preview"/>
 *
 * Renderiza un HTML del recibo en tiempo real usando innerHTML (no t-out)
 * para que el HTML no sea escapado por OWL. Se actualiza al cambiar
 * cualquier campo relevante del form.
 */
export class ReciboLivePreview extends Component {
    static template = "wigo_cobranza.ReciboLivePreview";

    static props = {
        record: { type: Object },
        readonly: { type: Boolean, optional: true },
        node: { type: Object, optional: true },
        archInfo: { type: Object, optional: true },
        fields: { type: Object, optional: true },
        options: { type: Object, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.htmlContainer = useRef("htmlContainer");

        this.state = useState({
            loading: true,
            error: null,
            cfgLoaded: false,
            cfg: null,
        });

        // Cargar config una vez al montar
        useEffect(
            () => {
                this._loadConfig();
            },
            () => []
        );

        // Redibujar cuando cambien campos relevantes del record
        useEffect(
            () => {
                if (this.state.cfgLoaded) {
                    this._renderHTML();
                }
            },
            () => {
                const d = this.props.record.data;
                return [
                    d.partner_id,
                    d.codigo_cliente,
                    d.periodo,
                    d.monto,
                    d.monto_en_letras,
                    d.descripcion,
                    d.fecha_pago,
                    d.canal_pago,
                    d.numero,
                    d.firma_nombre_override,
                    d.firma_cargo_override,
                    d.firma_celular_override,
                    d.state,
                    this.state.cfgLoaded,
                ];
            }
        );
    }

    async _loadConfig() {
        try {
            const cfg = await this.orm.call("wigo.recibo.config", "get_config_dict", [], {});
            this.state.cfg = cfg;
            this.state.cfgLoaded = true;
            this._renderHTML();
        } catch (e) {
            this.state.error = "No se pudo cargar la configuración del recibo.";
            this.state.loading = false;
        }
    }

    _buildHTML() {
        const cfg = this.state.cfg || {};
        const d = this.props.record.data;

        // --- Datos del recibo ---
        const partnerName = d.partner_id && d.partner_id[1] ? d.partner_id[1] : "—";
        const numero = d.numero || "NUEVO";
        // fecha_pago en Odoo 19 puede ser string "YYYY-MM-DD", objeto Date, o false
        let fecha = "—";
        if (d.fecha_pago) {
            try {
                let dt;
                if (d.fecha_pago instanceof Date) {
                    dt = d.fecha_pago;
                } else if (typeof d.fecha_pago === "string" && d.fecha_pago.includes("-")) {
                    // "YYYY-MM-DD" → forzar interpretación local sin timezone
                    const [y, m, day] = d.fecha_pago.split("-").map(Number);
                    dt = new Date(y, m - 1, day);
                } else {
                    dt = new Date(d.fecha_pago);
                }
                if (!isNaN(dt.getTime())) {
                    fecha = dt.toLocaleDateString("es-BO", {
                        day: "2-digit", month: "2-digit", year: "numeric",
                    });
                }
            } catch (e) { fecha = "—"; }
        }
        const periodo = d.periodo || "—";
        const monto = typeof d.monto === "number" ? d.monto.toFixed(2) : "0.00";
        const montoLetras = d.monto_en_letras || "";
        const descripcion = d.descripcion || "Servicio Internet";
        const codigoCli = d.codigo_cliente || "—";
        // canal_pago es un campo Selection — mapear valor técnico a label
        const canalMap = {
            "efectivo": "Efectivo", "transferencia": "Transferencia",
            "qr": "QR", "deposito": "Depósito", "tarjeta": "Tarjeta",
            "tigo_money": "Tigo Money", "boliviapay": "BoliviaPay",
        };
        const canal = d.canal_pago
            ? (canalMap[d.canal_pago] || d.canal_pago)
            : "—";
        const firmaNombre = d.firma_nombre_override || cfg.firma_nombre || "Firmante";
        const firmaCargo = d.firma_cargo_override || cfg.firma_cargo || "";
        const firmaCel = d.firma_celular_override || cfg.firma_celular || "";

        // --- Estilos desde config ---
        const colorP   = cfg.color_primario || "#cc0000";
        const colorS   = cfg.color_secundario || "#990000";
        const colorHdr = cfg.color_texto_header || "#ffffff";
        const colorFondo = cfg.color_fondo_recibo || "#ffffff";
        const colorTxtP  = cfg.color_texto_principal || "#222222";
        const colorTxtS  = cfg.color_texto_secundario || "#666666";
        const colorBorde = cfg.color_borde || "#cccccc";
        const colorFondoMonto = cfg.color_fondo_monto || "#f9f9f9";
        const fuente   = cfg.fuente_familia || "Arial, sans-serif";
        const tamBase  = cfg.tamano_fuente_base || 12;
        const tamTitulo = cfg.tamano_titulo || 22;
        const tamEmpresa = cfg.tamano_empresa || 14;
        const titNegrita = cfg.fuente_titulo_negrita !== false ? "bold" : "normal";
        const radius   = cfg.border_radius || 0;
        const mostrarBanda = cfg.mostrar_banda_decorativa !== false;
        const anchoBanda = cfg.ancho_banda || 8;
        const mostrarPie = cfg.mostrar_pie !== false;
        const textoPie = cfg.texto_pie || "";
        const mostrarCodigo = cfg.mostrar_columna_codigo !== false;
        const tablaHdr = cfg.tabla_header_texto || "DESCRIPCIÓN";
        const tablaMontoHdr = cfg.tabla_monto_texto || "MONTO (Bs.)";
        const empresaNombre  = cfg.empresa_nombre || "WIGO FAST";
        const empresaDireccion = cfg.empresa_direccion || "";
        const empresaCiudad  = cfg.empresa_ciudad || "";
        const empresaCelular = cfg.empresa_celular || "";
        const empresaNit     = cfg.empresa_nit || "";
        const empresaSlogan  = cfg.empresa_slogan || "";

        // Header background
        const estilo = cfg.estilo_header || "gradiente";
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

        // Logo
        const logoSrc = cfg.logo_base64 && cfg.logo_base64.length > 50
            ? `data:image/png;base64,${cfg.logo_base64}`
            : null;
        const la = cfg.logo_ancho || 90;
        const logoHtml = logoSrc
            ? `<img src="${logoSrc}" style="max-height:${la}px;max-width:${la * 2}px;display:block;margin-left:auto;" onerror="this.style.display='none'"/>`
            : "";

        // Estado badge
        const state = d.state || "borrador";
        const stateColors = { borrador: "#f59e0b", emitido: "#22c55e", anulado: "#ef4444" };
        const stateLabels = { borrador: "BORRADOR", emitido: "EMITIDO", anulado: "ANULADO" };
        const stateBg = stateColors[state] || "#888";
        const stateBadge = `<span style="background:${stateBg};color:#fff;padding:2px 8px;border-radius:12px;font-size:9px;font-weight:bold;">${stateLabels[state] || state}</span>`;

        const numStyle = cfg.mostrar_numero_grande !== false
            ? `font-size:16px;font-weight:bold;color:${(estilo === "gradiente" || estilo === "solido") ? colorHdr : colorP};`
            : `font-size:11px;`;

        return `
<div style="font-family:${fuente};font-size:${tamBase}px;color:${colorTxtP};background:#e5e7eb;padding:10px;">
  <div style="background:${colorFondo};border:1px solid ${colorBorde};border-radius:${radius}px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.15);">

    <!-- HEADER -->
    <div style="${headerBg}color:${headerTxtColor};padding:14px 18px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
        <div style="flex:1;">
          <div style="font-size:${tamTitulo}px;font-weight:${titNegrita};letter-spacing:-0.5px;">RECIBO DE COBRANZA</div>
          <div style="font-size:${tamEmpresa}px;font-weight:bold;margin-top:3px;">${empresaNombre}</div>
          ${empresaSlogan ? `<div style="font-size:10px;opacity:0.85;font-style:italic;">${empresaSlogan}</div>` : ""}
          <div style="font-size:10px;margin-top:4px;opacity:0.9;line-height:1.5;">
            ${[empresaDireccion, empresaCiudad].filter(Boolean).join(" · ")}
            ${empresaCelular ? `<br/>CEL: ${empresaCelular}` : ""}
            ${empresaNit ? ` &nbsp;·&nbsp; NIT: ${empresaNit}` : ""}
          </div>
        </div>
        <div style="text-align:right;flex-shrink:0;">
          ${logoHtml}
          <div style="${numStyle}margin-top:4px;">Nº ${numero}</div>
          <div style="margin-top:4px;">${stateBadge}</div>
        </div>
      </div>
    </div>

    <!-- CUERPO -->
    <div style="padding:16px 18px;">

      <!-- Datos cliente / fecha -->
      <div style="display:flex;gap:12px;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid ${colorBorde};">
        <div style="flex:2;">
          <div style="font-size:9px;text-transform:uppercase;color:${colorTxtS};letter-spacing:0.6px;margin-bottom:2px;">RECIBIDO DE</div>
          <div style="font-size:14px;font-weight:bold;">${partnerName}</div>
          ${mostrarCodigo ? `<div style="font-size:10px;color:${colorTxtS};">Código: ${codigoCli}</div>` : ""}
        </div>
        <div style="flex:1;text-align:right;">
          <div style="font-size:9px;text-transform:uppercase;color:${colorTxtS};letter-spacing:0.6px;margin-bottom:2px;">FECHA</div>
          <div style="font-size:13px;font-weight:bold;color:${colorP};">${fecha}</div>
          <div style="font-size:10px;color:${colorTxtS};">${periodo}</div>
        </div>
      </div>

      <!-- Tabla -->
      <table style="width:100%;border-collapse:collapse;font-size:${tamBase}px;margin-bottom:12px;">
        <thead>
          <tr style="background:${colorP};color:#fff;">
            <th style="padding:8px 10px;text-align:left;">${tablaHdr}</th>
            <th style="padding:8px 10px;text-align:right;white-space:nowrap;">${tablaMontoHdr}</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom:1px solid ${colorBorde};">
            <td style="padding:10px;">${descripcion}</td>
            <td style="padding:10px;text-align:right;">${monto}</td>
          </tr>
          <tr style="border-bottom:1px solid ${colorBorde};">
            <td style="padding:5px 10px;font-size:10px;color:${colorTxtS};">Canal: ${canal}</td>
            <td></td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td style="padding:10px;font-weight:bold;">TOTAL</td>
            <td style="padding:10px;text-align:right;font-weight:bold;font-size:${parseInt(tamBase)+2}px;color:${colorP};border-top:2px solid ${colorP};">
              ${monto} Bs.
            </td>
          </tr>
        </tfoot>
      </table>

      <!-- Monto en letras -->
      <div style="background:${colorFondoMonto};border-left:4px solid ${colorP};padding:10px 12px;border-radius:${radius}px;margin-bottom:12px;">
        <span style="font-size:10px;font-weight:bold;text-transform:uppercase;color:${colorTxtS};">SON:&nbsp;</span>
        <span style="color:${colorTxtP};">${montoLetras || "—"}</span>
      </div>

      ${mostrarBanda ? `<div style="background:${colorP};height:${anchoBanda}px;border-radius:${radius}px;margin-bottom:14px;"></div>` : ""}

      <!-- Firmas -->
      <div style="display:flex;gap:20px;margin-top:8px;">
        <div style="flex:1;text-align:center;border-top:1px solid ${colorBorde};padding-top:10px;">
          <div style="font-weight:bold;">${firmaNombre}</div>
          <div style="font-size:10px;color:${colorTxtS};">${firmaCargo}</div>
          ${firmaCel ? `<div style="font-size:9px;color:${colorTxtS};">CEL: ${firmaCel}</div>` : ""}
        </div>
        <div style="flex:1;text-align:center;border-top:1px solid ${colorBorde};padding-top:10px;">
          <div style="font-weight:bold;">ENTREGUE CONFORME</div>
          <div style="font-size:10px;color:${colorTxtS};margin-top:4px;">Nombre: ___________________</div>
          <div style="font-size:10px;color:${colorTxtS};">CI: ___________________</div>
        </div>
      </div>

      ${mostrarPie && textoPie
        ? `<div style="text-align:center;margin-top:12px;font-size:10px;color:${colorTxtS};border-top:1px dashed ${colorBorde};padding-top:8px;">${textoPie}</div>`
        : ""}

      <!-- Indicador de copia -->
      <div style="margin-top:16px;border-top:1px dashed ${colorBorde};padding-top:6px;text-align:center;font-size:9px;color:${colorTxtS};">
        --- ORIGINAL (vista previa) ---
      </div>

    </div>
  </div>

  <div style="text-align:center;margin-top:4px;font-size:9px;color:#aaa;">
    Vista previa · El PDF incluye dos copias: original + copia cliente
  </div>
</div>`;
    }

    _renderHTML() {
        const html = this._buildHTML();
        // Usar innerHTML directamente para evitar el escape de OWL
        if (this.htmlContainer.el) {
            this.htmlContainer.el.innerHTML = html;
        }
        this.state.loading = false;
        this.state.error = null;
    }
}

registry.category("view_widgets").add("recibo_live_preview", {
    component: ReciboLivePreview,
});
