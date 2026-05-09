/** @odoo-module **/

import { Component, useEffect, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class FtthWorkOrderPrintConfigPreview extends Component {
    static template = "wigo_ftth.FtthWorkOrderPrintConfigPreview";

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
            () => {
                this._render();
            },
            () => {
                const d = this.props.record.data;
                return [
                    d.titulo_documento, d.subtitulo_documento, d.mostrar_numero_grande,
                    d.border_radius, d.empresa_nombre, d.empresa_slogan,
                    d.empresa_direccion, d.empresa_ciudad, d.empresa_telefono,
                    d.empresa_email, d.empresa_nit, d.usar_logo_imagen,
                    d.layout_logo, d.logo, d.logo_ancho,
                    d.qr_cobranzas, d.qr_soporte,
                    d.firma_nombre, d.firma_cargo, d.firma_celular,
                    d.mostrar_pie, d.texto_pie,
                    d.color_primario, d.color_secundario, d.color_texto_header,
                    d.color_borde, d.color_fondo, d.color_texto, d.color_fondo_monto,
                    d.fuente_familia, d.tamano_fuente_base, d.tamano_titulo,
                    d.tamano_empresa, d.fuente_titulo_negrita,
                    d.mostrar_banda_decorativa, d.ancho_banda,
                    d.mostrar_columna_codigo, d.mostrar_equipos_instalados,
                    d.mostrar_materiales, d.mostrar_observaciones, d.mostrar_conformidad,
                    d.tabla_header_texto, d.tabla_monto_texto,
                ];
            }
        );
    }

    _binaryToSrc(value, modelFieldName) {
        if (!value) {
            return null;
        }
        if (typeof value === "object" && value.data) {
            return `data:image/png;base64,${value.data}`;
        }
        if (typeof value === "string" && value.length > 50) {
            return `data:image/png;base64,${value}`;
        }
        const recId = this.props.record.resId;
        if (recId) {
            return `/web/image/wigo.ftth.work.order.print.config/${recId}/${modelFieldName}`;
        }
        return null;
    }

    _renderImage(value, modelFieldName, alt, fallbackStyle = "") {
        const src = this._binaryToSrc(value, modelFieldName);
        if (src) {
            return `<img src="${src}" alt="${alt}" style="max-width:100%;max-height:100%;object-fit:contain;${fallbackStyle}" onerror="this.style.display='none'"/>`;
        }
        return `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;border:1px dashed rgba(122,63,152,.25);border-radius:6px;color:#8b8b8b;font-size:11px;background:rgba(255,255,255,.55);">${alt}</div>`;
    }

    _render() {
        const d = this.props.record.data;

        const cp = d.color_primario || "#7a3f98";
        const cs = d.color_secundario || "#b564d6";
        const cht = d.color_texto_header || "#ffffff";
        const cb = d.color_borde || "#cfcfd6";
        const cbg = d.color_fondo || "#ffffff";
        const ct = d.color_texto || "#1f1f1f";
        const cm = d.color_fondo_monto || "#f6eef9";
        const ff = d.fuente_familia || "Arial, sans-serif";
        const fb = d.tamano_fuente_base || 11;
        const ft = d.tamano_titulo || 18;
        const fe = d.tamano_empresa || 14;
        const boldTitle = d.fuente_titulo_negrita !== false ? "800" : "600";
        const radius = d.border_radius || 0;
        const showBand = d.mostrar_banda_decorativa !== false;
        const bandH = d.ancho_banda || 8;
        const showNum = d.mostrar_numero_grande !== false;
        const showFooter = d.mostrar_pie !== false;
        const showEq = d.mostrar_equipos_instalados !== false;
        const showMat = d.mostrar_materiales !== false;
        const showObs = d.mostrar_observaciones !== false;
        const showConform = d.mostrar_conformidad !== false;
        const showCode = d.mostrar_columna_codigo !== false;

        const logoSrc = this._binaryToSrc(d.logo, "logo");
        const qrCobSrc = this._binaryToSrc(d.qr_cobranzas, "qr_cobranzas");
        const qrSupSrc = this._binaryToSrc(d.qr_soporte, "qr_soporte");

        const empresaNombre = d.empresa_nombre || "WIGO FAST";
        const empresaSlogan = d.empresa_slogan || "Tu internet veloz y confiable";
        const empresaDireccion = d.empresa_direccion || "";
        const empresaCiudad = d.empresa_ciudad || "";
        const empresaTelefono = d.empresa_telefono || "";
        const empresaEmail = d.empresa_email || "";
        const empresaNit = d.empresa_nit || "";
        const titulo = d.titulo_documento || "ORDEN DE TRABAJO FTTH";
        const subtitulo = d.subtitulo_documento || "Planilla de instalación / baja";
        const layoutLogo = d.layout_logo || "izquierda";
        const logoWidth = d.logo_ancho || 110;
        const tablaHeader = d.tabla_header_texto || "DESCRIPCIÓN";
        const tablaMonto = d.tabla_monto_texto || "MONTO (Bs.)";
        const pieTexto = d.texto_pie || "La información de esta OT es parte del control técnico.";

        const headerStyle = `background:${cp};color:${cht};`;
        const paperStyle = `font-family:${ff};font-size:${fb}px;color:${ct};background:${cbg};border:1px solid ${cb};border-radius:${radius}px;overflow:hidden;`;
        const titleStyle = `font-size:${ft}px;font-weight:${boldTitle};line-height:1.05;`;
        const companyStyle = `font-size:${fe}px;font-weight:700;line-height:1.05;`;
        const bandHtml = showBand ? `<div style="height:${bandH}px;background:${cp};margin:4px 0 6px 0;border-radius:2px;"></div>` : "";

        const titleBlock = `
            <div style="text-align:center;flex:1;padding:0 10px;min-width:0;">
                <div style="${titleStyle}">${titulo}</div>
                <div style="${titleStyle};font-size:${Math.max(ft - 4, 11)}px;">${subtitulo}</div>
            </div>`;

        const logoCell = logoSrc && d.usar_logo_imagen !== false
            ? `<div style="width:${Math.max(logoWidth * 1.7, 120)}px;height:${Math.max(Math.round(logoWidth * 0.65), 68)}px;display:flex;align-items:center;justify-content:center;">${this._renderImage(d.logo, "logo", "LOGO")}</div>`
            : `<div style="width:${Math.max(logoWidth * 1.7, 120)}px;height:${Math.max(Math.round(logoWidth * 0.65), 68)}px;border:1px dashed rgba(255,255,255,.45);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:11px;opacity:.75;">LOGO</div>`;

        const qrCobHtml = qrCobSrc
            ? this._renderImage(d.qr_cobranzas, "qr_cobranzas", "QR Cobranzas")
            : `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;border:1px dashed ${cb};border-radius:4px;color:#888;">QR</div>`;
        const qrSupHtml = qrSupSrc
            ? this._renderImage(d.qr_soporte, "qr_soporte", "QR Soporte")
            : `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;border:1px dashed ${cb};border-radius:4px;color:#888;">QR</div>`;

        let headerHtml = "";
        if (layoutLogo === "centrado") {
            headerHtml = `
                <div style="${headerStyle};padding:8px 10px 6px 10px;">
                    <div style="display:flex;justify-content:center;align-items:center;margin-bottom:4px;">${logoCell}</div>
                    ${titleBlock}
                    <div style="text-align:center;font-size:8px;line-height:1.35;margin-top:2px;opacity:.9;">${empresaNombre}${empresaSlogan ? ` · ${empresaSlogan}` : ''}</div>
                </div>`;
        } else if (layoutLogo === "derecha") {
            headerHtml = `
                <div style="${headerStyle};padding:8px 10px;">
                    <table style="width:100%;border-collapse:collapse;table-layout:fixed;">
                        <tr>
                            <td style="border:none;width:26%;vertical-align:middle;">${titleBlock}</td>
                            <td style="border:none;width:48%;vertical-align:middle;text-align:center;">
                                <div style="${companyStyle}">${empresaNombre}</div>
                                ${empresaSlogan ? `<div style="font-size:8px;opacity:.9;">${empresaSlogan}</div>` : ''}
                                <div style="font-size:8px;line-height:1.35;margin-top:2px;">${empresaDireccion}${empresaCiudad ? '<br/>' + empresaCiudad : ''}${empresaTelefono ? '<br/>TEL: ' + empresaTelefono : ''}${empresaEmail ? ' | ' + empresaEmail : ''}${empresaNit ? '<br/>NIT: ' + empresaNit : ''}</div>
                            </td>
                            <td style="border:none;width:26%;vertical-align:middle;text-align:right;">${logoCell}</td>
                        </tr>
                    </table>
                </div>`;
        } else {
            headerHtml = `
                <div style="${headerStyle};padding:8px 10px;">
                    <table style="width:100%;border-collapse:collapse;table-layout:fixed;">
                        <tr>
                            <td style="border:none;width:26%;vertical-align:middle;">${logoCell}</td>
                            <td style="border:none;width:48%;vertical-align:middle;">${titleBlock}</td>
                            <td style="border:none;width:26%;vertical-align:middle;text-align:right;">
                                <div style="${companyStyle}">${empresaNombre}</div>
                                ${empresaSlogan ? `<div style="font-size:8px;opacity:.9;">${empresaSlogan}</div>` : ''}
                                <div style="font-size:8px;line-height:1.35;margin-top:2px;">${empresaDireccion}${empresaCiudad ? '<br/>' + empresaCiudad : ''}${empresaTelefono ? '<br/>TEL: ' + empresaTelefono : ''}${empresaEmail ? ' | ' + empresaEmail : ''}${empresaNit ? '<br/>NIT: ' + empresaNit : ''}</div>
                            </td>
                        </tr>
                    </table>
                </div>`;
        }

        const html = `
<div class="wigo-ftth-ot-preview" style="font-family:${ff};color:${ct};background:#e9edf3;padding:8px;border-radius:6px;">
  <div class="wigo-ftth-ot-paper" style="${paperStyle}">
    ${headerHtml}
    <div style="padding:6px 8px 8px 8px;">
      <table style="width:100%;border-collapse:collapse;margin-bottom:4px;table-layout:fixed;font-size:${Math.max(fb - 1, 8)}px;">
        <tr>
          <td style="width:64%;border:1px solid ${cb};padding:3px 4px;vertical-align:top;">
            <div style="font-size:8px;text-transform:uppercase;color:#666;letter-spacing:.6px;">SERVICIO</div>
            <div style="font-weight:700;">Internet PPPoE + Wi Fi</div>
            <div style="margin-top:4px;"><span style="background:#e7d6ff;padding:1px 4px;border-radius:3px;font-weight:700;">Razón Social:</span> <span>Nombre del cliente</span></div>
            <div style="margin-top:2px;"><span style="background:#e7d6ff;padding:1px 4px;border-radius:3px;font-weight:700;">Nombre:</span> <span>Responsable recepción</span></div>
            <div style="margin-top:2px;"><span style="background:#e7d6ff;padding:1px 4px;border-radius:3px;font-weight:700;">Celular:</span> <span>00000000</span> &nbsp; <span style="background:#e7d6ff;padding:1px 4px;border-radius:3px;font-weight:700;">Teléfono:</span> <span>00000000</span></div>
            <div style="margin-top:2px;"><span style="background:#e7d6ff;padding:1px 4px;border-radius:3px;font-weight:700;">Dirección:</span> <span>Calle / zona / referencia</span></div>
            <div style="margin-top:2px;"><span style="background:#e7d6ff;padding:1px 4px;border-radius:3px;font-weight:700;">Coordenadas:</span> <span>17°20'50.9"S 66°09'38.2"W</span></div>
          </td>
          <td style="width:36%;border:1px solid ${cb};padding:0;vertical-align:top;">
            <table style="width:100%;border-collapse:collapse;table-layout:fixed;font-size:${Math.max(fb - 1, 8)}px;">
              <tr><th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;width:40%;">CONTRATO</th><td style="border:1px solid ${cb};padding:3px 4px;text-align:center;font-weight:700;">CF-00350</td></tr>
              <tr><th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">CIUDAD</th><th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">DIA</th><th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">MES</th><th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">AÑO</th></tr>
              <tr><td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">Cochabamba</td><td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">09</td><td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">05</td><td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">2026</td></tr>
              <tr><th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">Hora:</th><td colspan="3" style="border:1px solid ${cb};padding:3px 4px;text-align:center;">08:30</td></tr>
              <tr><th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;text-align:left;" colspan="3">Instalación</th><td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">X</td></tr>
              <tr><th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;text-align:left;" colspan="3">Traslado Interno</th><td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td></tr>
              <tr><th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;text-align:left;" colspan="3">Traslado Externo</th><td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td></tr>
            </table>
          </td>
        </tr>
      </table>

      <table style="width:100%;border-collapse:collapse;table-layout:fixed;margin-bottom:4px;font-size:${Math.max(fb - 1, 8)}px;">
        <tr>
          <th style="width:12%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">SERVICIO</th>
          <td colspan="7" style="border:1px solid ${cb};padding:3px 4px;text-align:center;">Internet PPPoE + Wi Fi</td>
        </tr>
        <tr>
          <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">Razón Social</th>
          <td colspan="3" style="border:1px solid ${cb};padding:3px 4px;text-align:center;">Nombre del cliente</td>
          <th style="width:12%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">Zona</th>
          <td colspan="3" style="border:1px solid ${cb};padding:3px 4px;text-align:center;">04P</td>
        </tr>
        <tr>
          <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">Nombre</th>
          <td colspan="3" style="border:1px solid ${cb};padding:3px 4px;text-align:center;">Nombre del cliente</td>
          <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">email</th>
          <td colspan="3" style="border:1px solid ${cb};padding:3px 4px;text-align:center;">correo@dominio.com</td>
        </tr>
        <tr>
          <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">Celular</th>
          <td colspan="1" style="border:1px solid ${cb};padding:3px 4px;text-align:center;">00000000</td>
          <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">Teléfono</th>
          <td colspan="1" style="border:1px solid ${cb};padding:3px 4px;text-align:center;">00000000</td>
          <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">Dirección</th>
          <td colspan="3" style="border:1px solid ${cb};padding:3px 4px;text-align:center;">Calle / zona / referencia</td>
        </tr>
      </table>

      <div style="text-align:center;background:${cp};color:${cht};font-weight:700;padding:3px 6px;margin-top:2px;">DATOS TÉCNICOS DEL SERVICIO</div>
      <table style="width:100%;border-collapse:collapse;table-layout:fixed;margin-bottom:4px;font-size:${Math.max(fb - 1, 8)}px;">
        <tr>
          <th style="width:14%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">PLAN</th>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">30 Mbps</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;" rowspan="3"><div style="font-weight:700;">ODN-02-PREECTURAL</div></td>
          <th style="width:14%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">RUTA</th>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">ODN_01/04P/08</td>
        </tr>
        <tr>
          <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">LAN USUARIO</th>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">192.168.101.0/24</td>
          <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">NAP</th>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">04P</td>
        </tr>
        <tr>
          <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">RED WI FI</th>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;background:#fffb00;">WIGOFAST_CF-00350</td>
          <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">PUERTO NAP</th>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">08</td>
        </tr>
        <tr>
          <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">CONTRASEÑA</th>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;background:#fffb00;">XPON2383AED0</td>
          <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">W. Rx(-dBm)</th>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td>
        </tr>
      </table>

      ${showEq ? `
      <div style="text-align:center;background:${cp};color:${cht};font-weight:700;padding:3px 6px;margin-top:2px;">EQUIPOS INSTALADOS</div>
      <table style="width:100%;border-collapse:collapse;table-layout:fixed;margin-bottom:4px;font-size:${Math.max(fb - 1, 8)}px;">
        <tr>
          <th style="width:12%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">EQUIPO</th>
          <th style="width:12%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">MARCA</th>
          <th style="width:12%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">MODELO</th>
          <th style="width:24%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">NRO DE SERIE</th>
          <th style="width:24%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">NRO DE SERIE (PON S/N)</th>
        </tr>
        <tr>
          <td style="border:1px solid ${cb};padding:3px 4px;">ONU/ONT</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">LANLY</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">G24A</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">L2511000420</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">XPON2383AED0</td>
        </tr>
        <tr><td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td><td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td><td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td><td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td><td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td></tr>
      </table>` : ''}

      ${showMat ? `
      <div style="text-align:center;background:${cp};color:${cht};font-weight:700;padding:3px 6px;margin-top:2px;">MATERIAL</div>
      <table style="width:100%;border-collapse:collapse;table-layout:fixed;margin-bottom:4px;font-size:${Math.max(fb - 1, 8)}px;">
        <tr>
          <th style="width:18%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">DESCRIPCION</th>
          <th style="width:10%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">CANT.</th>
          <th style="width:34%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">${tablaHeader}</th>
          <th style="width:12%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">Unidad</th>
          <th style="width:10%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">CANT.</th>
          <th style="width:16%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;" rowspan="2">Número de Cobranzas</th>
        </tr>
        <tr>
          <td style="border:1px solid ${cb};padding:3px 4px;">Conectores de campo</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">Cable DROP</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">(metros)</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;" rowspan="4">
            <div style="text-align:center;font-size:11px;">Para Pago de Facturas</div>
            <div style="text-align:center;margin-top:4px;">Comuniquese al:</div>
            <div style="text-align:center;font-weight:700;margin-top:4px;">73802898</div>
            <div style="margin-top:6px;display:flex;justify-content:center;align-items:center;height:126px;">${qrCobHtml}</div>
          </td>
        </tr>
        <tr>
          <td style="border:1px solid ${cb};padding:3px 4px;">Tensores</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">Cable disp./devanar</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">(metros)</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td>
        </tr>
        <tr>
          <td style="border:1px solid ${cb};padding:3px 4px;">Grapas</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">Otros:</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td>
        </tr>
        <tr>
          <td style="border:1px solid ${cb};padding:3px 4px;">Roseta</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td>
        </tr>
        <tr>
          <td style="border:1px solid ${cb};padding:3px 4px;">Acoplador SC APC</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td>
        </tr>
        <tr>
          <td style="border:1px solid ${cb};padding:3px 4px;">Patch Cord SC APC</td>
          <td style="border:1px solid ${cb};padding:3px 4px;text-align:center;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td>
          <td style="border:1px solid ${cb};padding:3px 4px;">&nbsp;</td>
        </tr>
      </table>` : ''}

      ${showObs ? `
      <div style="text-align:center;background:${cp};color:${cht};font-weight:700;padding:3px 6px;margin-top:2px;">OBSERVACIONES</div>
      <div style="border:1px solid ${cb};border-top:none;min-height:70px;padding:6px 8px;font-size:${Math.max(fb - 1, 8)}px;line-height:1.45;">
        <div>...............................................................................................................................................</div>
        <div>...............................................................................................................................................</div>
        <div>...............................................................................................................................................</div>
      </div>` : ''}

      ${showConform ? `
      <div style="margin-top:4px;">
        <table style="width:100%;border-collapse:collapse;table-layout:fixed;font-size:${Math.max(fb - 1, 8)}px;">
          <tr>
            <th style="background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">CONFORMIDAD DEL CLIENTE</th>
            <th style="width:16%;background:#ead1f2;border:1px solid ${cb};padding:3px 4px;">Número de Atención/Soporte</th>
          </tr>
          <tr>
            <td style="border:1px solid ${cb};padding:6px 8px;line-height:1.35;text-align:justify;">
              El cliente/responsable de recepción del servicio, previa verificación, declara haber recibido el servicio de internet WiGo-Fast con las características descritas arriba, además del equipo instalado en sus ambientes, de la misma manera se compromete al cuidado y buen uso de los equipos entregados en calidad de comodato. En conformidad firma al pie.
            </td>
            <td style="border:1px solid ${cb};padding:4px;vertical-align:middle;">
              <div style="text-align:center;">Para</div>
              <div style="text-align:center;font-weight:700;">Soporte Técnico</div>
              <div style="text-align:center;">comuníquese al:</div>
              <div style="text-align:center;font-weight:700;">63888133</div>
              <div style="margin-top:6px;display:flex;justify-content:center;align-items:center;height:92px;">${qrSupHtml}</div>
            </td>
          </tr>
        </table>
      </div>` : ''}

      ${showBand ? bandHtml : ''}

      ${showFooter ? `<div style="margin-top:6px;text-align:center;color:#666;font-size:9px;border-top:1px dashed ${cb};padding-top:5px;">${pieTexto}</div>` : ''}

    </div>
  </div>
</div>`;

        if (this.htmlContainer.el) {
            this.htmlContainer.el.innerHTML = html;
        }
        this.state.loading = false;
    }
}

registry.category("view_widgets").add("ftth_work_order_print_config_preview", {
    component: FtthWorkOrderPrintConfigPreview,
});