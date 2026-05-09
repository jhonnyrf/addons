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
                    +                    d.numero_cobranzas, d.numero_soporte,
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
        if (!value) return null;
        if (typeof value === "object" && value.data) return `data:image/png;base64,${value.data}`;
        if (typeof value === "string" && value.length > 50) return `data:image/png;base64,${value}`;
        const recId = this.props.record.resId;
        if (recId) return `/web/image/wigo.ftth.work.order.print.config/${recId}/${modelFieldName}`;
        return null;
    }

    _imgTag(value, fieldName, alt, style = "") {
        const src = this._binaryToSrc(value, fieldName);
        if (src) return `<img src="${src}" alt="${alt}" style="max-width:100%;max-height:100%;object-fit:contain;${style}" onerror="this.style.display='none'"/>`;
        return `<span style="color:#aaa;font-size:9px;">[${alt}]</span>`;
    }

    _render() {
        const d = this.props.record.data;

        // --- Colores y tipografía ---
        const cp  = d.color_primario         || "#7a3f98";
        const cht = d.color_texto_header      || "#ffffff";
        const cb  = d.color_borde             || "#cfcfd6";
        const cbg = d.color_fondo             || "#ffffff";
        const ct  = d.color_texto             || "#1f1f1f";
        const ff  = d.fuente_familia          || "Arial, sans-serif";
        const fb  = d.tamano_fuente_base       || 10;
        const ft  = d.tamano_titulo            || 17;
        const la  = d.logo_ancho              || 96;

        // --- Toggles ---
        const showEq       = d.mostrar_equipos_instalados !== false;
        const showMat      = d.mostrar_materiales          !== false;
        const showObs      = d.mostrar_observaciones       !== false;
        const showConform  = d.mostrar_conformidad         !== false;
        const showFooter   = d.mostrar_pie                 !== false;

        // --- Datos empresa ---
        const empNombre   = d.empresa_nombre    || "WIGO FAST";
        const empSlogan   = d.empresa_slogan    || "";
        const empDir      = d.empresa_direccion || "";
        const empCiudad   = d.empresa_ciudad    || "";
        const empTel      = d.empresa_telefono  || "";
        const empEmail    = d.empresa_email     || "";
        const empNit      = d.empresa_nit       || "";
        const titulo      = d.titulo_documento  || "ORDEN DE TRABAJO FTTH";
        const subtitulo   = d.subtitulo_documento || "PLANILLA DE INSTALACIÓN / BAJA";
        const pieTexto    = d.texto_pie         || "La información de esta OT es parte del control técnico.";
        const tablaHeader = d.tabla_header_texto || "DESCRIPCIÓN";
        const tablaMonto = d.tabla_monto_texto || "MONTO (Bs.)";        

        // --- QR ---
          const numCob = d.numero_cobranzas || '73802898';
          const numSop = d.numero_soporte || '63888133';
        const qrCobSrc = this._binaryToSrc(d.qr_cobranzas, "qr_cobranzas");
        const qrSupSrc = this._binaryToSrc(d.qr_soporte, "qr_soporte");

        const qrCobHtml = qrCobSrc
            ? `<img src="${qrCobSrc}" style="max-height:72px;max-width:72px;" onerror="this.style.display='none'"/>`
            : `<div style="border:1px dashed ${cb};width:72px;height:72px;display:flex;align-items:center;justify-content:center;font-size:8px;color:#aaa;">QR</div>`;
        const qrSupHtml = qrSupSrc
            ? `<img src="${qrSupSrc}" style="max-height:72px;max-width:72px;" onerror="this.style.display='none'"/>`
            : `<div style="border:1px dashed ${cb};width:72px;height:72px;display:flex;align-items:center;justify-content:center;font-size:8px;color:#aaa;">QR</div>`;

        // --- Logo ---
        const logoSrc = this._binaryToSrc(d.logo, "logo");
        const logoHtml = (logoSrc && d.usar_logo_imagen !== false)
            ? `<img src="${logoSrc}" style="max-height:${Math.round(la * 0.7)}px;max-width:${Math.round(la * 1.8)}px;object-fit:contain;" onerror="this.style.display='none'"/>`
            : `<div style="width:${Math.round(la * 1.8)}px;height:${Math.round(la * 0.7)}px;border:1px dashed rgba(122,63,152,.4);border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:9px;color:#aaa;">LOGO</div>`;

        // Empresa info líneas para la celda derecha del header
        let empLines = `<div style="font-weight:700;font-size:${fb}px;">${empNombre}</div>`;
        if (empSlogan)  empLines += `<div style="font-size:${Math.max(fb - 1, 7)}px;font-style:italic;">${empSlogan}</div>`;
        if (empDir)     empLines += `<div style="font-size:${Math.max(fb - 1, 7)}px;">${empDir}</div>`;
        if (empCiudad)  empLines += `<div style="font-size:${Math.max(fb - 1, 7)}px;">${empCiudad}</div>`;
        if (empTel)     empLines += `<div style="font-size:${Math.max(fb - 1, 7)}px;">Telf./Fax: ${empTel}</div>`;
        if (empEmail)   empLines += `<div style="font-size:${Math.max(fb - 1, 7)}px;">${empEmail}</div>`;
        if (empNit)     empLines += `<div style="font-size:${Math.max(fb - 1, 7)}px;">NIT: ${empNit}</div>`;

        // ============================================================
        // ESTILOS COMPARTIDOS — replicar exactamente el CSS del PDF
        // ============================================================
        const tblStyle = `width:100%;border-collapse:collapse;table-layout:fixed;`;
        const thStyle  = `background:#ead1f2;border:1px solid ${cb};padding:2px 4px;font-weight:700;text-align:center;vertical-align:middle;`;
        const tdStyle  = `border:1px solid ${cb};padding:2px 4px;vertical-align:middle;`;
        const secStyle = `text-align:center;font-weight:700;padding:3px 6px;background:${cp};color:${cht};margin-top:4px;`;

        const fsBody   = `${Math.max(fb - 1, 8)}px`;

        // ============================================================
        // ENCABEZADO — replica exacta del PDF:
        //   [LOGO 27%] | [Títulos 39%] | [tabla contrato 34%]
        // ============================================================
        const headerHtml = `
<table style="${tblStyle}margin-bottom:4px;">
  <tr>
    <td style="width:27%;border:none;padding:2px 4px;vertical-align:middle;">${logoHtml}</td>
    <td style="width:39%;border:none;padding:2px 4px;text-align:center;vertical-align:middle;">
      <div style="font-weight:800;text-transform:uppercase;font-size:${ft}px;line-height:1.05;">${titulo}</div>
      <div style="font-weight:800;text-transform:uppercase;font-size:${Math.max(ft - 5, 10)}px;line-height:1.05;">${subtitulo}</div>
    </td>
    <td style="width:34%;border:none;padding:0;vertical-align:top;">
      <table style="${tblStyle}font-size:${fsBody};">
        <tr>
          <th style="${thStyle}width:32%;">CONTRATO</th>
          <td style="${tdStyle}text-align:center;font-weight:700;" colspan="3">CF-00350</td>
        </tr>
        <tr>
          <th style="${thStyle}">CIUDAD</th>
          <th style="${thStyle}width:14%;">DIA</th>
          <th style="${thStyle}width:14%;">MES</th>
          <th style="${thStyle}width:20%;">AÑO</th>
        </tr>
        <tr>
          <td style="${tdStyle}text-align:center;">Cochabamba</td>
          <td style="${tdStyle}text-align:center;">09</td>
          <td style="${tdStyle}text-align:center;">05</td>
          <td style="${tdStyle}text-align:center;">2026</td>
        </tr>
        <tr>
          <th style="${thStyle}">Hora:</th>
          <td colspan="3" style="${tdStyle}text-align:center;">08:30</td>
        </tr>
      </table>

      <div style="text-align:center;background:${cp};color:${cht};font-weight:700;padding:3px 6px;margin-top:2px;">DATOS TÉCNICOS DEL SERVICIO</div>
      <table style="width:100%;border-collapse:collapse;table-layout:fixed;margin-bottom:4px;font-size:${Math.max(fb - 1, 8)}px;">
        <tr>
          <th style="${thStyle}text-align:left;" colspan="3">Instalación</th>
          <td style="${tdStyle}text-align:center;">&nbsp;</td>
        </tr>
        <tr>
          <th style="${thStyle}text-align:left;" colspan="3">Traslado Interno</th>
          <td style="${tdStyle}text-align:center;">&nbsp;</td>
        </tr>
        <tr>
          <th style="${thStyle}text-align:left;" colspan="3">Traslado Externo</th>
          <td style="${tdStyle}text-align:center;">&nbsp;</td>
        </tr>
      </table>
    </td>
  </tr>
</table>`;

        // ============================================================
        // TABLA DATOS GENERALES DEL CLIENTE
        // ============================================================
        const clientHtml = `
<table style="${tblStyle}margin-bottom:4px;font-size:${fsBody};">
  <tr>
    <th style="${thStyle}width:12%;">SERVICIO</th>
    <td colspan="7" style="${tdStyle}text-align:center;">Internet PPPoE + Wi Fi</td>
  </tr>
  <tr>
    <th style="${thStyle}">Razón Social</th>
    <td colspan="3" style="${tdStyle}text-align:center;">Nombre del cliente</td>
    <th style="${thStyle}width:10%;">Zona</th>
    <td colspan="3" style="${tdStyle}text-align:center;">04P</td>
  </tr>
  <tr>
    <th style="${thStyle}">Nombre</th>
    <td colspan="3" style="${tdStyle}text-align:center;">Responsable recepción</td>
    <th style="${thStyle}">email</th>
    <td colspan="3" style="${tdStyle}text-align:center;">correo@dominio.com</td>
  </tr>
  <tr>
    <th style="${thStyle}">Celular</th>
    <td style="${tdStyle}text-align:center;">68506287</td>
    <th style="${thStyle}">Teléfono</th>
    <td style="${tdStyle}text-align:center;">72273625</td>
    <th style="${thStyle}">Dirección</th>
    <td colspan="3" style="${tdStyle}text-align:center;">Floresta 04P</td>
  </tr>
  <tr>
    <th style="${thStyle}">Coordenadas</th>
    <td colspan="3" style="${tdStyle}text-align:center;">17°20'50.9"S 66°09'38.2"W</td>
    <th style="${thStyle}">Zona</th>
    <td colspan="3" style="${tdStyle}text-align:center;">04P</td>
  </tr>
</table>`;

        // ============================================================
        // DATOS TÉCNICOS — replica la estructura del PDF con ODN en rowspan
        // ============================================================
        const techHtml = `
<div style="${secStyle}">DATOS TÉCNICOS DEL SERVICIO</div>
<table style="${tblStyle}margin-bottom:4px;font-size:${fsBody};">
  <tr>
    <th style="${thStyle}width:14%;">PLAN</th>
    <td style="${tdStyle}text-align:center;">30 Mbps</td>
    <td style="${tdStyle}text-align:center;font-weight:700;" rowspan="3">ODN-02-PREFECTURAL</td>
    <th style="${thStyle}width:12%;">RUTA:</th>
    <td style="${tdStyle}text-align:center;">ODN_01/04P/08</td>
    <th style="${thStyle}width:12%;">NAP</th>
    <td style="${tdStyle}text-align:center;">04P</td>
  </tr>
  <tr>
    <th style="${thStyle}">LAN USUARIO</th>
    <td style="${tdStyle}text-align:center;">192.168.101.0/24</td>
    <th style="${thStyle}">PUERTO NAP</th>
    <td style="${tdStyle}text-align:center;">08</td>
    <th style="${thStyle}">W. Rx(-dBm)</th>
    <td style="${tdStyle}text-align:center;">&nbsp;</td>
  </tr>
  <tr>
    <th style="${thStyle}">RED Wi Fi</th>
    <td style="${tdStyle}text-align:center;background:#fffb00;font-weight:700;">WIGOFAST_CF-00350</td>
    <th style="${thStyle}">CONTRASEÑA</th>
    <td style="${tdStyle}text-align:center;background:#fffb00;font-weight:700;" colspan="2">XPON2383AED0</td>
  </tr>
</table>`;

        // ============================================================
        // EQUIPOS INSTALADOS
        // ============================================================
        const eqHtml = showEq ? `
<div style="${secStyle}">EQUIPOS INSTALADOS</div>
<table style="${tblStyle}margin-bottom:4px;font-size:${fsBody};">
  <thead>
    <tr>
      <th style="${thStyle}width:14%;">EQUIPO</th>
      <th style="${thStyle}width:14%;">MARCA</th>
      <th style="${thStyle}width:20%;">MODELO</th>
      <th style="${thStyle}width:26%;">NRO DE SERIE</th>
      <th style="${thStyle}">NRO DE SERIE (PON S/N)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="${tdStyle}text-align:center;">ONU/ONT</td>
      <td style="${tdStyle}text-align:center;">LANLY</td>
      <td style="${tdStyle}text-align:center;">G24A</td>
      <td style="${tdStyle}text-align:center;">L2511000420</td>
      <td style="${tdStyle}text-align:center;">XPON2383AED0</td>
    </tr>
    <tr>
      <td style="${tdStyle}height:16px;">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
    </tr>
    <tr>
      <td style="${tdStyle}height:16px;">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
    </tr>
  </tbody>
</table>` : '';

        // ============================================================
        // MATERIAL — replica estructura del PDF con QR en rowspan
        // ============================================================
        const matHtml = showMat ? `
<div style="${secStyle}">MATERIAL</div>
<table style="${tblStyle}margin-bottom:4px;font-size:${fsBody};">
  <thead>
    <tr>
      <th style="${thStyle}width:18%;">DESCRIPCION</th>
      <th style="${thStyle}width:8%;">CANT.</th>
      <th style="${thStyle}width:22%;">${tablaHeader}</th>
      <th style="${thStyle}width:10%;">Unidad</th>
      <th style="${thStyle}width:8%;">CANT.</th>
      <th style="${thStyle}width:16%;" rowspan="2">
        <div>Número de</div>
        <div>Cobranzas</div>
      </th>
    </tr>   
  </thead>
  <tbody>
    <tr>
      <td style="${tdStyle}">Conectores de campo</td>
      <td style="${tdStyle}text-align:center;">&nbsp;</td>
      <td style="${tdStyle}text-align:center;">Cable DROP</td>
      <td style="${tdStyle}text-align:center;">(metros)</td>
      <td style="${tdStyle}text-align:center;">&nbsp;</td>
      <td style="${tdStyle}text-align:center;" rowspan="6">
        <div style="font-size:8px;font-weight:700;">Para Pago de Facturas</div>
        <div style="font-size:8px;margin-top:2px;">Comuniquese al:</div>
        <div style="font-weight:700;margin:2px 0;">${numCob}</div>
        <div style="display:flex;justify-content:center;margin-top:4px;">${qrCobHtml}</div>
      </td>
    </tr>
    <tr>
      <td style="${tdStyle}">Tensores</td>
      <td style="${tdStyle}text-align:center;">&nbsp;</td>
      <td style="${tdStyle}text-align:center;">Cable disp./devanar</td>
      <td style="${tdStyle}text-align:center;">(metros)</td>
      <td style="${tdStyle}text-align:center;">&nbsp;</td>
    </tr>
    <tr>
      <td style="${tdStyle}">Grapas</td>
      <td style="${tdStyle}text-align:center;">&nbsp;</td>
      <td style="${tdStyle}">Otros:</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
    </tr>
    <tr>
      <td style="${tdStyle}">Roseta</td>
      <td style="${tdStyle}text-align:center;">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
    </tr>
    <tr>
      <td style="${tdStyle}">Acoplador SC APC</td>
      <td style="${tdStyle}text-align:center;">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
    </tr>
    <tr>
      <td style="${tdStyle}">Patch Cord SC APC</td>
      <td style="${tdStyle}text-align:center;">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
      <td style="${tdStyle}">&nbsp;</td>
    </tr>
  </tbody>
</table>` : '';

        // ============================================================
        // OBSERVACIONES
        // ============================================================
        const obsHtml = showObs ? `
<div style="${secStyle}">OBSERVACIONES</div>
<div style="border:1px solid ${cb};border-top:none;min-height:58px;padding:4px 6px;font-size:${fsBody};line-height:1.45;margin-bottom:4px;">
  <div>&nbsp;</div><div>&nbsp;</div><div>&nbsp;</div>
</div>` : '';

        // ============================================================
        // CONFORMIDAD DEL CLIENTE
        // ============================================================
        const conformHtml = showConform ? `
<table style="${tblStyle}margin-top:4px;font-size:${fsBody};">
  <tr>
    <th style="${thStyle}width:72%;">CONFORMIDAD DEL CLIENTE</th>
    <th style="${thStyle}">Número de Atención/Soporte</th>
  </tr>
  <tr>
    <td style="${tdStyle}padding:5px 6px;text-align:justify;vertical-align:top;">
      El cliente/responsable de recepción del servicio, previa verificación, declara haber recibido el servicio de
      internet WiGo-Fast de ASISCORP S.R.L. con las características descritas arriba, además del equipo instalado
      en sus ambientes, de la misma manera se compromete al cuidado y buen uso de los equipos entregados en calidad
      de comodato. En conformidad firma al pie.
    </td>
    <td style="${tdStyle}padding:5px 6px;text-align:center;vertical-align:middle;">
      <div style="font-size:8px;">Para</div>
      <div style="font-weight:700;font-size:9px;">Soporte Técnico</div>
      <div style="font-size:8px;">comuníquese al:</div>
      <div style="font-weight:700;font-size:11px;">${numSop}</div>
      <div style="display:flex;justify-content:center;margin-top:4px;">${qrSupHtml}</div>
    </td>
  </tr>
</table>` : '';

        // ============================================================
        // FIRMAS
        // ============================================================
        const firmasHtml = `
<table style="${tblStyle}margin-top:10px;font-size:${fsBody};">
  <tr>
    <td style="width:50%;border:none;padding-top:16px;text-align:center;vertical-align:bottom;">
      <div style="border-top:1px solid #3d73c9;margin:0 20px 3px;"></div>
      <div style="font-weight:700;">Firma Cliente / Responsable</div>
      <div style="margin-top:2px;text-align:left;font-weight:700;">Nombre y Apellido:</div>
      <div style="margin-top:2px;text-align:left;font-weight:700;">Documento de Identidad:</div>
    </td>
    <td style="width:50%;border:none;padding-top:16px;text-align:center;vertical-align:bottom;">
      <div style="border-top:1px solid #3d73c9;margin:0 20px 3px;"></div>
      <div style="font-weight:700;">Firma Responsable ASISCORP S.R.L.</div>
      <div style="margin-top:2px;text-align:left;font-weight:700;">Nombre y Apellido:</div>
    </td>
  </tr>
</table>`;

        // ============================================================
        // PIE DE PÁGINA
        // ============================================================
        const footerHtml = showFooter ? `
<div style="margin-top:6px;text-align:center;color:#666;font-size:8px;border-top:1px dashed ${cb};padding-top:4px;">${pieTexto}</div>` : '';

        // ============================================================
        // WRAPPER COMPLETO — simula el papel A4
        // ============================================================
        const html = `
<div style="font-family:${ff};color:${ct};background:#e0e0e0;padding:12px;border-radius:4px;min-height:300px;">
  <div style="background:#555;color:#fff;text-align:center;font-size:9px;padding:3px 6px;margin-bottom:2px;border-radius:2px 2px 0 0;letter-spacing:.5px;">
    PREVISUALIZACIÓN — Réplica del PDF impreso
  </div>
  <div style="background:${cbg};border:1px solid ${cb};padding:5px 6px;font-family:${ff};font-size:${fb}px;color:${ct};">
    ${headerHtml}
    ${clientHtml}
    ${techHtml}
    ${eqHtml}
    ${matHtml}
    ${obsHtml}
    ${conformHtml}
    ${firmasHtml}
    ${footerHtml}
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
