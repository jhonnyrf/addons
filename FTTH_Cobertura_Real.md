# Cobertura FTTH real (end-to-end) en Zonas (wigo.zone)

Este documento describe **qué se considera** y **cómo se calcula** la cobertura FTTH “real” (con capacidad disponible de extremo a extremo) para el modelo **wigo.zone**.

La cobertura **NO** se define solo por “existen cajas”; se valida disponibilidad en:

1. **Última milla (NAP):** puertos de caja libres.
2. **OLT:** subinterfaces libres en los puertos asociados a la zona.

---

## 1. Modelos involucrados

Topología relevante:

- Regional → Nodo → OLT → Puerto PON → Subinterfaz (VLAN) → Box Group (splitter) → Caja (NAP) → Puerto de caja

Modelos consultados por el cómputo:

- **wigo.zone**
- **wigo.ftth.box.group** (zone_id, olt_port_id, odn_id, total_ports)
- **wigo.ftth.box** (box_group_id, port_capacity)
- **wigo.ftth.box.port** (state: free, occupied, allocated, reserved, active)
- **wigo.ftth.subinterface** (olt_port_id, state: free, occupied, allocated, reserved, active)

---

## 2. ¿Qué infraestructura se considera “válida”?

Para evaluar cobertura en una zona, primero se identifican **box groups válidos**.

Un **box group válido** es un registro de **wigo.ftth.box.group** que cumple:

- Pertenece a la zona (`zone_id = zona`)
- Tiene **olt_port_id** definido (no vacío)
- Tiene **odn_id** definido (no vacío)
- Si el modelo trae campo `active`, además debe estar activo (`active = True`)

Si una zona **no tiene box groups válidos**, entonces:

- `coverage_status = no_coverage`
- `has_coverage = False`

---

## 3. Capacidad medida (end-to-end)

La cobertura real se valida por **capacidad disponible** en los dos puntos críticos.

### 3.1 Capacidad NAP (puertos de caja)

En **wigo.ftth.box.port** se contabilizan puertos únicamente dentro de **box groups válidos**.

Estados considerados:

- **Puertos libres (NAP):** `state = free` → `free_box_ports`
- **Puertos usados (NAP):** `state in {occupied, allocated, reserved, active}` → `used_ports`

### 3.2 Capacidad OLT (subinterfaces)

En **wigo.ftth.subinterface** se contabilizan subinterfaces:

- `state = free`
- `olt_port_id` pertenece a alguno de los puertos OLT asociados a los box groups válidos de la zona

→ `free_subinterfaces`

---

## 4. Regla de “cobertura real”

Una zona se considera con cobertura **real end-to-end** solo si hay capacidad en ambos lados:

- `free_box_ports > 0` **y**
- `free_subinterfaces > 0`

Si cualquiera de los dos es 0, la zona no tiene cupo real para nuevas instalaciones.

---

## 5. Estados de cobertura (coverage_status)

Se define el estado así:

### 5.1 `no_coverage`

- No hay infraestructura válida (no hay box groups válidos), o
- No hay puertos útiles en absoluto (caso extremo):
  - `total_ports <= 0` **y** `(used_ports + free_box_ports) <= 0`

### 5.2 `saturated`

- Hay infraestructura válida pero **no hay capacidad end-to-end**, es decir:
  - `free_box_ports == 0` **o**
  - `free_subinterfaces == 0`

### 5.3 `warning`

- Hay capacidad, pero la ocupación NAP es alta (riesgo):
  - `used_ports / total_ports >= 0.80`

### 5.4 `available`

- Hay capacidad end-to-end y ocupación < 80%.

---

## 6. Métricas calculadas en wigo.zone

Los campos calculados (no almacenados) que quedan disponibles son:

- `total_ports`: suma de `wigo.ftth.box.group.total_ports` (solo box groups válidos)
- `total_boxes`: cantidad de `wigo.ftth.box` en box groups válidos
- `used_ports`: puertos NAP usados (occupied/allocated/reserved/active)
- `free_box_ports`: puertos NAP libres (free)
- `free_subinterfaces`: subinterfaces libres en OLT para los puertos asociados a la zona
- `has_coverage`: booleano de cobertura real
- `coverage_status`: estado (no_coverage / saturated / warning / available)

---

## 7. Seguridad (usuarios CRM)

Las lecturas a los modelos FTTH se hacen con **sudo()** para evitar que usuarios CRM sin permisos en topología FTTH rompan el cálculo.

---

## 8. Performance (optimización de consultas)

Para evitar loops por zona y reducir consultas:

- Se usan agregaciones con `read_group()` cuando es posible.
- Se evita agrupar por rutas relacionales “dotted” (ej. `box_group_id.zone_id`) por compatibilidad.
- Se agrupa por campos directos (ej. `box_id`, `box_group_id`) y se mapea a `zone_id` en Python.

---

## 9. API pública de diagnóstico

Método en **wigo.zone**:

- `check_ftth_coverage()`

Retorna un snapshot compacto:

```json
{
  "has_coverage": true,
  "status": "available",
  "free_box_ports": 12,
  "free_subinterfaces": 4
}
```

---

## 10. Notas importantes

- Todos los campos son `store=False`: se recalculan cuando la vista/cliente los lee.
- La cobertura es “real” porque exige capacidad libre tanto en NAP como en OLT.
