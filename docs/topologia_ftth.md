# Documentación: Topología FTTH (Wigo addons)

# ==========================================

Este documento describe la configuración y la lógica de la topología FTTH implementada en el módulo `wigo_ftth`. Está escrito en español y resume modelos, campos clave, restricciones, convenciones de nombres, y la lógica de cálculo de cobertura end-to-end (NAP ⇄ OLT). Incluye además un diagrama de flujo en Mermaid.

**Resumen rápido**:

- **Árbol principal**: Regional → Nodo → OLT → Puertos OLT → Subinterfaces
- **Rama de distribución**: OLT → ODN → Grupo de Cajas → Caja (NAP) → Puerto de Caja
- **Cobertura FTTH (wigo.zone)**: determina disponibilidad real end-to-end combinando puertos libres en cajas NAP y subinterfaces libres/ocupadas en OLT.

**Modelos principales y relaciones**

- `wigo.ftth.regional` (Regional)
  - Campos clave: `name`, `prefix`, `active`, `nodo_ids` (One2many)
  - Restricciones: unique `name`, unique `prefix`

- `wigo.ftth.nodo` (Nodo de agregación)
  - Campos clave: `name`, `number`, `node_type` (aggregation/acess), `regional_id` (Many2one), `olt_ids` (One2many)
  - Restricciones: unique(`number`, `regional_id`)
  - Traducción de flujo: un `regional` agrupa varios `nodo`.

- `wigo.ftth.technology` (Tecnología)
  - Campos: `name`, `prefix`, `active`
  - Restricciones: unique `name`, unique `prefix`

- `wigo.ftth.olt` (OLT)
  - Campos clave: `node_id` (Many2one), `olt_number`, `technology_id`, `olt_code` (compute), `port_ids` (One2many), `odn_ids` (One2many)
  - Restricciones: unique(`olt_number`, `node_id`)
  - Cálculos: `regional_prefix`, `node_number`, `technology_prefix` y `olt_code` (combinan prefijos y números para generar el código OLT)

- `wigo.ftth.olt.port` (Puerto PON de OLT)
  - Campos: `olt_id`, `interface_port` (ej. `gpon-olt_1/1/1`), `port_number`, `capacity_max`, `chassis`, `slot`, `prefix` (por defecto `gpon-olt`)
  - Relaciones: `subinterface_ids` (One2many)
  - Restricciones: unicidad en `(olt_id,prefix,chassis,slot,port_number)` y `(olt_id, interface_port)`
  - Cómputos: `used_subinterfaces`, `free_subinterfaces`, `occupancy_percent`

- `wigo.ftth.subinterface` (Subinterface OLT)
  - Campos: `olt_port_id` (Many2one a `wigo.ftth.olt.port`), `state` (por ejemplo: `free`, `occupied`, `active`, etc.)
  - Uso: representa las conexiones lógicas asignables desde OLT hacia NAP/cajas.

- `wigo.ftth.odn` (ODN — Red de Distribución Óptica)
  - Campos: `name`, `olt_id` (Many2one, una OLT puede tener solo una ODN), `odf_port`, `odn_number`, `node_id` (compute desde la OLT)
  - Restricción: unique(`olt_id`) (una ODN por OLT)

- `wigo.ftth.box.group` (Grupo de cajas / Splitters)
  - Campos: `zone_id` (vincula a `wigo.zone`), `olt_port_id`, `odn_id`, `group_number`, `total_ports` (suma de puertos en el grupo), `active`
  - Un grupo de cajas válido para cobertura debe tener `olt_port_id` y `odn_id` definidos (y normalmente `active=True`).

- `wigo.ftth.box` (Caja NAP / Caja física)
  - Campos: `box_group_id`, `name`, `ports` (relación con `wigo.ftth.box.port`)

- `wigo.ftth.box.port` (Puerto de caja NAP)
  - Campos: `box_id`, `state` (`free`, `occupied`, `used`, ...), etc.

- `wigo.zone` (Zona CRM extendida)
  - Campos compute: `has_coverage`, `coverage_status`, `free_box_ports`, `free_subinterfaces`, `used_ports`, `total_boxes`, `total_ports`
  - Implementa lógica para calcular cobertura FTTH a nivel de zona (véase sección Lógica de cobertura).

**Convenciones de nombres y prefijos**

- Prefijos: cada `regional` y `technology` tiene un `prefix` que se usa para construir códigos (ej. `regional_prefix`, `technology_prefix`).
- `interface_port` ejemplo: `gpon-olt_1/1/1` (prefijo + chasis/slot/puerto).
- `olt_code` es un campo computado que combina `regional_prefix`, `node_number`, `olt_number` y `technology_prefix`.

**Reglas importantes / Constraints**

- Un `nodo.number` debe ser único dentro de su `regional`.
- Un `olt.olt_number` debe ser único dentro de su `node`.
- Un `olt` solo puede tener una `odn` asociada (constraint unique on `olt_id` en `wigo.ftth.odn`).
- Un `olt.port` debe tener combinación única `(olt_id, prefix, chassis, slot, port_number)` y `interface_port` único por `olt`.

**Lógica de creación / asignaciones automáticas**

- Existen métodos `_get_next_available_number` y `_get_next_available_olt_number` en `Nodo` y `OLT` respectivamente, para asignar números secuenciales cuando el usuario no especifica uno.
- `olt_code` se calcula automáticamente a partir de prefijos y números (útil para identificadores legibles).
- `port` también puede auto-generar `interface_port` basándose en `prefix`, `chassis`, `slot` y `port_number`.

**Flujo de configuración (pasos típicos)**

1. Crear una `Regional` con `name` y `prefix`.
2. Crear un `Nodo` asociado a la `Regional` (campo `regional_id`). Asignar `number` o dejar vacío para autogenerarlo.
3. Crear una `Technology` (ej. GPON) definiendo `prefix`.
4. Crear una `OLT` asignándola al `Nodo` y a la `Technology`. Si no hay `olt_number`, se asigna uno disponible.
5. Añadir `Puertos OLT` (`wigo.ftth.olt.port`) a la OLT: indicar `chassis`, `slot`, `port_number`, `capacity_max`. Se generará `interface_port`.
6. Crear la `ODN` y asociarla a la `OLT` (solo una por OLT).
7. Crear `BoxGroup` apuntando a `olt_port_id`, `odn_id` y `zone_id` (vinculado a `wigo.zone`). Indicar `group_number` y `total_ports`.
8. Crear `Box` dentro del `BoxGroup`, y sus `BoxPort` (cada puerto con `state` inicial `free`).
9. Crear/validar `Subinterfaces` en puertos OLT, dejando estados `free` o `occupied` según corresponda.

**Diagrama de flujo (Mermaid)**

```mermaid
flowchart LR
    REG[Regional]\n    NODE[Nodo]
    OLT[OLT]
    OLT_PORT[Puerto OLT]
    SUBINT[Subinterface]
    ODN[ODN]
    BOX_GROUP[Grupo de Cajas]
    BOX[Caja NAP]
    BOX_PORT[Puerto Caja]
    ZONE[Zona (wigo.zone)]

    REG --> NODE
    NODE --> OLT
    OLT --> OLT_PORT
    OLT_PORT --> SUBINT
    OLT --> ODN
    ODN --> BOX_GROUP
    BOX_GROUP --> BOX
    BOX --> BOX_PORT
    BOX_GROUP --> ZONE

    BOX_PORT -- estado free/occupied --> FreeBoxPorts["Puertos NAP disponibles"]
    SUBINT -- estado free/occupied --> FreeSubifs["Subinterfaces disponibles"]

    FreeBoxPorts & FreeSubifs --> CoverageCheck["Chequeo Cobertura end-to-end"]
    CoverageCheck -->|si ambos >0| COVERAGE_AVAILABLE["Disponible / available"]
    CoverageCheck -->|si alguno ==0| COVERAGE_SATURATED["Saturado / no capacidad"]
    COVERAGE_AVAILABLE --> ZONE
```

**Lógica de cobertura FTTH (resumen técnico)**

- Un `box_group` es válido si tiene `olt_port_id` y `odn_id` y (opcionalmente) `active=True`.
- Se computan métricas por `zone`:
  - `total_ports`: suma de `total_ports` de `box_group` válidos.
  - `total_boxes`: conteo de cajas NAP relacionadas.
  - `free_box_ports`: puertos de caja en estado `free` o `occupied` (estos dos se consideran disponibles en NAP).
  - `free_subinterfaces`: subinterfaces en OLT vinculadas a los `olt_port_id` de los grupos válidos con estado `free` o `occupied`.
  - `used_ports`: puertos en otros estados (considerados efectivamente usados).
- Reglas de estado final (`coverage_status`):
  - `no_coverage`: no hay grupos válidos o no hay puertos declarados.
  - `saturated`: `free_box_ports == 0` o `free_subinterfaces == 0`.
  - `warning`: ocupación >= 80% (umbral implementado en compute).
  - `available`: hay capacidad suficiente.

**Consultas y búsquedas (search helpers)**

- `wigo.zone` implementa métodos `search` personalizados para filtrar por `has_coverage`, `coverage_status`, `free_box_ports`, `free_subinterfaces`. Estos métodos calculan un snapshot en memoria y devuelven los ids que cumplen la condición.

**Buenas prácticas operacionales**

- Mantener `prefix` legibles y consistentes por `regional` y `technology` para generar `olt_code` coherente.
- Siempre asociar `BoxGroup` a `zone` para que la zona pueda reflejar cobertura real.
- Evitar duplicar `interface_port` o combinaciones chasis/slot/port en la misma OLT (constraints los protegen).

**Ejemplo rápido**

1. Crear Regional: `name=San Miguel`, `prefix=SMG`.
2. Crear Nodo: `name=SMG-Node-1`, `number=1`, `regional_id=San Miguel`.
3. Crear Technology: `name=GPON`, `prefix=GPON`.
4. Crear OLT: `node_id=SMG-Node-1`, `olt_number=1`, `technology_id=GPON` → `olt_code` generado: `SMG-1-1-GPON` (ejemplo).
5. Crear Puerto OLT: `chassis=1`, `slot=1`, `port_number=1`, `prefix=gpon-olt` → `interface_port=gpon-olt_1/1/1`.
6. Crear ODN asociada a la OLT y crear `BoxGroup` apuntando al `olt_port` y `odn` y `zone`.

---

Archivo generado automáticamente a partir del análisis de:

- `wigo_ftth/models/ftth_topology.py`
- `wigo_ftth/views/topology_views.xml`
- `wigo_ftth/models/ftth_zone.py`

Si quieres, puedo:

- añadir ejemplos SQL o búsquedas concretas para filtrar zonas con cobertura baja;
- exportar el diagrama a PNG/SVG (requiere render externo);
- incluir ejemplos de comandos Odoo para crear registros desde CLI.

Fin de la documentación.
