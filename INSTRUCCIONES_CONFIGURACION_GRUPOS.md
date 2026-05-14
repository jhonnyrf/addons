# 📋 INSTRUCCIONES: CONFIGURACIÓN DE GRUPOS Y PERMISOS EN ODOO

> **Versión**: 1.0  
> **Fecha**: 14 de Mayo 2026  
> **Para**: Persona que configurará grupos y permisos en Odoo  
> **Objetivo**: Guía paso a paso para personalizar acceso de usuarios

---

## 🔄 RESUMEN DE CAMBIOS REALIZADOS

### ✅ **QUÉ SE HIZO**

Se realizaron cambios técnicos en **8 módulos** para habilitar la instalación correcta:

#### **1. Archivos CSV de Seguridad (Modificados)**

```
Módulos: 8 (todos)
Cambio: Se removieron referencias a grupos específicos
Resultado: group_id está VACÍO en todas las líneas
Efecto: Acceso total para todos los usuarios (temporal)
```

**Módulos actualizados:**

- ✅ `wigo_planes/security/ir.model.access.csv`
- ✅ `wigo_crm/security/ir.model.access.csv`
- ✅ `wigo_ftth/security/ir.model.access.csv`
- ✅ `wigo_helpdesk/security/ir.model.access.csv`
- ✅ `wigo_cobranza/security/ir.model.access.csv`
- ✅ `customer_contract/security/ir.model.access.csv`
- ✅ `crm_service_cancellation/security/ir.model.access.csv`
- ✅ `contactos_ext/security/ir.model.access.csv`

#### **2. Archivos XML Eliminados (Removidos)**

```
Archivos que creaban grupos innecesarios:
- ❌ wigo_cobranza/security/security.xml
- ❌ wigo_ftth/security/security.xml
- ❌ wigo_helpdesk/security/helpdesk_security.xml
```

---

## 📊 ESTADO ACTUAL

### **Acceso a Datos**

```
Usuario actual: TODOS pueden acceder a TODOS los modelos
Restricciones: NINGUNA (temporal)
Formato: Los permisos se asignan desde la UI de Odoo, no desde código
```

### **Archivo CSV (Ejemplo)**

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_internet_plan_user,internet.plan user,model_internet_plan,,1,1,1,1
                                                                  ↑ VACÍO
```

---

## 🎯 TU TAREA: PERSONALIZAR ACCESO DESDE ODOO

### **PASO 1: Verificar Instalación de Módulos**

1. Abre Odoo (debe estar reiniciado)
2. **Menú** → Aplicaciones
3. **Buscar**: "wigo" (o ingresa cada módulo)
4. Verifica que estén **INSTALADOS** (sin errores)

```
✅ Planes (wigo_planes) - INSTALADO
✅ CRM (wigo_crm) - INSTALADO
✅ FTTH (wigo_ftth) - INSTALADO
✅ Helpdesk (wigo_helpdesk) - INSTALADO
✅ Cobranza (wigo_cobranza) - INSTALADO
✅ Contratos (customer_contract) - INSTALADO
✅ Cancelación (crm_service_cancellation) - INSTALADO
✅ Contactos (contactos_ext) - INSTALADO
```

**Si alguno falla**: Reportar error específico.

---

### **PASO 2: Crear Grupos de Seguridad**

**Ir a:** Menú → Configuración → Usuarios y Compañías → **Grupos**

#### **Crear Grupo 1: COMERCIAL**

1. Click **"Crear"** (botón azul)
2. Completa:
   ```
   Nombre del grupo: Comercial
   ```
3. **NO COMPLETAR** tab "Permisos de acceso" aún
4. Click **"Guardar"**

#### **Crear Grupo 2: TÉCNICA**

1. Click **"Crear"**
2. Completa:
   ```
   Nombre del grupo: Técnica
   ```
3. Click **"Guardar"**

#### **Crear Grupo 3: COBRANZA**

1. Click **"Crear"**
2. Completa:
   ```
   Nombre del grupo: Cobranza
   ```
3. Click **"Guardar"**

**Resultado:**

```
✅ Grupo "Comercial" creado
✅ Grupo "Técnica" creado
✅ Grupo "Cobranza" creado
```

---

### **PASO 3: Asignar Permisos a Cada Grupo**

#### **Para el Grupo COMERCIAL:**

1. **Ir a:** Menú → Configuración → Usuarios y Compañías → Grupos
2. **Buscar y abrir**: "Comercial"
3. **Click tab**: "Permisos de acceso"
4. Desplázate y **marca estos modelos** con TODAS las opciones ✅:

   ```
   LECTURA | ESCRITURA | CREACIÓN | BORRADO

   ✅ crm.lead (Lead/Oportunidad)
      [ ] → Leer ✅
      [ ] → Escribir ✅
      [ ] → Crear ✅
      [ ] → Borrar ✅

   ✅ customer.contract (Contrato)
      [ ] → Leer ✅
      [ ] → Escribir ✅
      [ ] → Crear ✅
      [ ] → Borrar ✅

   ✅ internet.plan (Plan de Internet)
      [ ] → Leer ✅
      [ ] → Escribir ✅
      [ ] → Crear ✅
      [ ] → Borrar ✅

   ✅ wigo.zone (Zona)
      [ ] → Leer ✅
      [ ] → Escribir ✅
      [ ] → Crear ✅
      [ ] → Borrar ✅

   ✅ wigo.promo (Promoción)
      [ ] → Leer ✅
      [ ] → Escribir ✅
      [ ] → Crear ✅
      [ ] → Borrar ✅

   ⚠️ wigo.pago.estado (Estado de Pago) - **SOLO LECTURA**
      [ ] → Leer ✅
      [ ] → Escribir ❌
      [ ] → Crear ❌
      [ ] → Borrar ❌

   ❌ wigo.ftth (FTTH / Técnica) - SIN ACCESO
      [ ] → Leer ❌
      [ ] → Escribir ❌
      [ ] → Crear ❌
      [ ] → Borrar ❌
   ```

5. Click **"Guardar"**

---

#### **Para el Grupo TÉCNICA:**

1. Abrir grupo: "Técnica"
2. Tab: "Permisos de acceso"
3. Marcar:

   ```
   ✅ helpdesk.ticket (Ticket de Soporte)
      TODOS ✅

   ✅ wigo.ftth.work.order (Orden de Trabajo)
      TODOS ✅

   ✅ wigo.ftth.onu (ONU / Equipo)
      TODOS ✅

   ✅ wigo.ftth.olt (OLT / Concentrador)
      TODOS ✅

   ⚠️ customer.contract (Contrato) - SOLO LECTURA
      [ ] → Leer ✅
      [ ] → Escribir ❌
      [ ] → Crear ❌
      [ ] → Borrar ❌

   ⚠️ wigo.pago.estado (Estado de Pago) - SOLO LECTURA
      [ ] → Leer ✅
      [ ] → Escribir ❌
      [ ] → Crear ❌
      [ ] → Borrar ❌

   ❌ crm.lead - SIN ACCESO
   ❌ wigo_helpdesk - SIN ACCESO ESCRITURA
   ```

4. Click **"Guardar"**

---

#### **Para el Grupo COBRANZA:**

1. Abrir grupo: "Cobranza"
2. Tab: "Permisos de acceso"
3. Marcar:

   ```
   ✅ wigo.pago.estado (Estado de Pago)
      TODOS ✅

   ✅ wigo.recibo.cobro (Recibo de Cobro)
      TODOS ✅

   ✅ wigo.incobrable (Incobrable)
      TODOS ✅

   ⚠️ customer.contract (Contrato) - SOLO LECTURA
      [ ] → Leer ✅
      [ ] → Escribir ❌
      [ ] → Crear ❌
      [ ] → Borrar ❌

   ❌ crm.lead - SIN ACCESO
   ❌ wigo.ftth - SIN ACCESO
   ❌ helpdesk.ticket - SIN ACCESO
   ```

4. Click **"Guardar"**

---

### **PASO 4: Asignar Usuarios a Grupos**

#### **Para cada usuario, asignarle su grupo:**

1. **Ir a:** Menú → Configuración → Usuarios y Compañías → **Usuarios**

2. **Abrir usuario**: Ej: "juan_comercial"

3. **Tab "Grupos de Acceso"**

4. **Marcar checkboxes** según rol:

   ```
   Si es COMERCIAL:
   ✅ Comercial
   ✅ base.group_user (opcional, ya heredado)

   Si es TÉCNICO:
   ✅ Técnica
   ✅ base.group_user (opcional, ya heredado)

   Si es COBRANZA:
   ✅ Cobranza
   ✅ base.group_user (opcional, ya heredado)
   ```

5. Click **"Guardar"**

6. **Repetir** para cada usuario

---

## 📋 TABLA RESUMEN DE PERMISOS

| Modelo              | Comercial | Técnica | Cobranza | Admin   |
| ------------------- | --------- | ------- | -------- | ------- |
| `crm.lead`          | ✅ RWCD   | ❌ -    | ❌ -     | ✅ RWCD |
| `customer.contract` | ✅ RWCD   | ⚠️ R    | ⚠️ R     | ✅ RWCD |
| `internet.plan`     | ✅ RWCD   | ❌ -    | ❌ -     | ✅ RWCD |
| `wigo.zone`         | ✅ RWCD   | ❌ -    | ❌ -     | ✅ RWCD |
| `wigo.promo`        | ✅ RWCD   | ❌ -    | ❌ -     | ✅ RWCD |
| `wigo.ftth.*`       | ❌ -      | ✅ RWCD | ❌ -     | ✅ RWCD |
| `helpdesk.ticket`   | ⚠️ R      | ✅ RWCD | ❌ -     | ✅ RWCD |
| `wigo.pago.estado`  | ⚠️ R      | ⚠️ R    | ✅ RWCD  | ✅ RWCD |
| `wigo.recibo.cobro` | ❌ -      | ❌ -    | ✅ RWCD  | ✅ RWCD |

**Leyenda:**

- ✅ RWCD = Read, Write, Create, Delete (acceso completo)
- ⚠️ R = Solo lectura (Read-only)
- ❌ - = Sin acceso

---

## ❓ PREGUNTAS COMUNES

### **P: ¿Qué pasa si creo un grupo nuevo?**

**R:** Abre el grupo → Tab "Permisos de acceso" → marca modelos que necesita.

### **P: ¿Puedo cambiar permisos después?**

**R:** SÍ. Abre el grupo → Tab "Permisos de acceso" → marca/desmarca → Guardar.

### **P: ¿Un usuario puede tener múltiples grupos?**

**R:** SÍ. Abre usuario → Tab "Grupos de Acceso" → marca múltiples grupos.

### **P: ¿Qué es "base.group_user"?**

**R:** Grupo estándar de Odoo. Todos los usuarios lo tienen por defecto.

### **P: ¿Los cambios son inmediatos?**

**R:** SÍ. Al guardar, los permisos cambian instantáneamente.

### **P: ¿Debo reiniciar Odoo?**

**R:** NO. Los cambios se aplican en vivo.

---

## 🔐 SEGURIDAD

### **Importante:**

- Los permisos se aplican **por grupo**, no por usuario individual
- Si usuario está en grupo "Comercial" → Tiene permisos de Comercial
- Si un usuario está en múltiples grupos → Acceso = UNIÓN de todos los grupos

### **Ejemplo:**

```
Usuario "juan" está en:
  - Grupo "Comercial" → Acceso a crm.lead, customer.contract, etc.
  - Grupo "Cobranza" → Acceso a wigo.pago.estado

Resultado: juan puede ver Y EDITAR ambos
```

---

## ✅ CHECKLIST FINAL

- [ ] Módulos instalados sin errores
- [ ] Grupo "Comercial" creado
- [ ] Grupo "Técnica" creado
- [ ] Grupo "Cobranza" creado
- [ ] Permisos asignados a cada grupo
- [ ] Usuarios asignados a sus grupos
- [ ] Verificar que usuarios acceden solo a su data
- [ ] Documentar cambios si es necesario

---

## 📞 SOPORTE

Si tienes preguntas o problemas durante la configuración:

1. Revisa esta guía (secciones de Preguntas Comunes)
2. Verifica que los grupos estén creados
3. Verifica que los permisos estén marcados correctamente
4. Revisa los logs de Odoo si hay errores

---

**¡Listo para personalizar accesos!** 🚀
