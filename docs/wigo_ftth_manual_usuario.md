# Manual de Usuario

## Módulo Wigo FTTH

## 1. Introducción

El módulo Wigo FTTH gestiona la operación técnica de red GPON/FTTH en Odoo. Incluye topología de red, inventario de ONUs y accesorios, órdenes de trabajo, fichas técnicas de cliente, suspensiones, reportes operativos y configuración de impresión de planillas OT.

## 1.1 Estructura funcional del módulo

**Descripción**  
Permite que el usuario navegue por las áreas de operación técnica: Órdenes de Trabajo, Clientes, Suspensiones, Inventario, Reportes y Configuración.

**Flujo de trabajo**

1. El usuario ingresa al módulo FTTH.
2. El sistema muestra el menú principal con sus secciones.
3. El usuario selecciona el proceso operativo requerido.
4. El sistema abre la vista configurada (lista, formulario, gráfico o pivote) según la opción seleccionada.

**Datos**  
| Campo | Descripción |
|---|---|
| Órdenes de Trabajo | Gestión del ciclo operativo de instalaciones y bajas. |
| Clientes | Fichas técnicas del servicio FTTH activo/histórico. |
| Suspensiones | Gestión de cortes y reconexiones. |
| Inventario ONUs y Accesorios | Equipos ONU, marcas, modelos y catálogo de materiales. |
| Reportes | Indicadores por estado, plan, instalador, nodo y ocupación. |
| Configuración | Parámetros de topología GPON y operación técnica. |

## 2. Órdenes de Trabajo FTTH

### 2.1 Listar Órdenes de Trabajo

**Descripción**  
Permite que el usuario consulte las órdenes de trabajo registradas, con filtros por estado, tipo e instalador.

**Flujo de trabajo**

1. El usuario ingresa a FTTH.
2. El usuario selecciona Órdenes de Trabajo > Todas las OTs.
3. El sistema muestra el listado con decoraciones por estado.
4. El usuario aplica filtros o agrupaciones desde la búsqueda.
5. El usuario abre la orden para revisar detalle técnico y comercial.

**Datos**  
| Campo | Descripción |
|---|---|
| Referencia OT | Identificador único de la orden. |
| Tipo | Instalación o Baja/Retiro. |
| Cliente | Titular del servicio. |
| Código cliente | Código comercial/contractual. |
| Plan | Plan de Internet asociado al contrato. |
| Instalador | Responsable operativo asignado. |
| Estado | Fase del flujo operativo de la OT. |

### 2.2 Registrar Orden de Trabajo

**Descripción**  
Permite que el usuario registre una OT de instalación y complete datos de cliente, planificación y ruta técnica.

**Flujo de trabajo**

1. El usuario accede al listado de OTs.
2. El usuario crea una nueva orden.
3. El sistema genera automáticamente la referencia OT por secuencia.
4. El usuario selecciona contrato y datos operativos.
5. El sistema completa datos relacionados del contrato.
6. El usuario define instalador y componentes técnicos.
7. El usuario guarda la orden en estado Pendiente.

**Datos**  
| Campo | Descripción |
|---|---|
| Tipo | Por defecto instalación. |
| Contrato | Contrato activo origen de la OT. |
| Fecha programada | Fecha/hora objetivo de ejecución. |
| Instalador | Técnico o empresa instaladora. |
| Zona/Grupo/OLT/NAP | Ruta técnica FTTH de aprovisionamiento. |
| ONU | Equipo ONU a instalar. |

### 2.3 Editar Orden de Trabajo

**Descripción**  
Permite que el usuario actualice datos de una OT mientras el estado operativo lo permita.

**Flujo de trabajo**

1. El usuario abre una OT existente.
2. El sistema muestra pestañas de cliente, datos técnicos, ONU, accesorios y notas.
3. El usuario modifica información autorizada.
4. El usuario guarda los cambios.
5. El sistema actualiza la OT y mantiene trazabilidad en chatter.

**Datos**  
| Campo | Descripción |
|---|---|
| Dirección y contacto | Datos de intervención en sitio. |
| Ruta técnica | Zona, grupo de caja, caja, puerto y subinterfaz. |
| ONU | Equipo asignado y datos técnicos asociados. |
| Accesorios OT | Materiales consumidos durante instalación. |
| Observaciones | Registro operativo adicional. |

### 2.4 Eliminar Orden de Trabajo

**Descripción**  
Permite que el usuario elimine una OT. El sistema ejecuta liberación de recursos para evitar inconsistencias de topología.

**Flujo de trabajo**

1. El usuario abre la OT a eliminar.
2. El usuario ejecuta eliminar.
3. El sistema aplica la lógica de cancelación/liberación de recursos según corresponda.
4. El sistema elimina el registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Subinterfaz | Se libera según estado y vínculo existente. |
| Puerto de caja | Se libera cuando aplica. |
| ONU | Se devuelve a disponibilidad cuando aplica. |

### 2.5 Asignar Orden de Trabajo

**Descripción**  
Permite que el usuario pase una OT de Pendiente a Asignada, validando instalador y recursos técnicos.

**Flujo de trabajo**

1. El usuario abre una OT en estado Pendiente.
2. El usuario verifica instalador y recursos técnicos.
3. El usuario presiona Asignar.
4. El sistema valida reglas de disponibilidad.
5. El sistema cambia estado a Asignada.
6. El sistema marca recursos técnicos como Asignada a OT.

**Datos**  
| Campo | Descripción |
|---|---|
| Instalador | Requerido para asignar. |
| Subinterfaz | Debe estar en estado Infraestructura para instalación. |
| Puerto NAP | Debe estar en estado Infraestructura para instalación. |
| ONU | Cambia a estado En campo durante asignación. |

### 2.6 Ejecutar flujo operativo de instalación y baja

**Descripción**  
Permite que el usuario avance la OT por los estados operativos hasta activar cliente o ejecutar baja.

**Flujo de trabajo**

1. El usuario presiona Enviar a campo en estado Asignada.
2. El sistema cambia a En campo y registra fecha de ejecución.
3. Para instalaciones, el usuario presiona Equipo instalado y luego Activar cliente.
4. El sistema crea/actualiza ficha técnica y sincroniza recursos.
5. Para bajas, el usuario presiona Ejecutar baja en estado En campo.
6. El sistema libera subinterfaz, puerto y ONU, y marca baja ejecutada.

**Datos**  
| Campo | Descripción |
|---|---|
| Estados instalación | Pendiente, Asignada, En campo, Instalado, Activo. |
| Estados baja | Pendiente, Asignada, En campo, Baja ejecutada. |
| Fecha ejecución | Se registra al enviar a campo o ejecutar baja. |
| Ficha técnica | Se crea automáticamente al activar cliente. |

### 2.7 Cancelar Orden de Trabajo

**Descripción**  
Permite que el usuario cancele una OT no finalizada, liberando recursos vinculados.

**Flujo de trabajo**

1. El usuario abre la OT.
2. El usuario presiona Cancelar OT.
3. El sistema solicita confirmación.
4. El sistema libera recursos según tipo de OT.
5. El sistema cambia estado a Cancelada.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado final | Cancelada. |
| Motivo de cancelación | Puede registrarse desde asistente de cancelación. |
| Recursos | Se liberan subinterfaz, puerto y ONU en instalaciones. |

### 2.8 Imprimir OT en PDF

**Descripción**  
Permite que el usuario genere la planilla PDF de una OT asignada usando la configuración de diseño vigente.

**Flujo de trabajo**

1. El usuario abre una OT en estado Asignada.
2. El usuario presiona Imprimir OT.
3. El sistema genera el reporte PDF con plantilla configurable.
4. El usuario descarga o imprime el documento.

**Datos**  
| Campo | Descripción |
|---|---|
| Diseño de planilla | Se toma de configuración de Planilla OT PDF. |
| Información comercial | Datos del cliente y contrato. |
| Información técnica | Ruta FTTH, ONU, materiales y observaciones. |

## 3. Fichas Técnicas de Cliente

### 3.1 Listar Fichas Técnicas

**Descripción**  
Permite que el usuario consulte las fichas técnicas generadas desde las OTs activadas.

**Flujo de trabajo**

1. El usuario ingresa a Clientes > Fichas Técnicas.
2. El sistema muestra lista con estado de servicio.
3. El usuario filtra por estado, plan, instalador o agrupaciones.
4. El usuario abre la ficha para detalle técnico completo.

**Datos**  
| Campo | Descripción |
|---|---|
| Código cliente | Identificador de ficha técnica. |
| Plan | Plan contratado. |
| Estado servicio | Activo, Suspendido, En corte, Baja o Cancelado. |
| Instalador | Técnico asignado en origen. |
| Topología | Nodo, OLT, subinterfaz, NAP y puerto. |

### 3.2 Editar Ficha Técnica

**Descripción**  
Permite que el usuario actualice datos de configuración, topología visible y observaciones según permisos.

**Flujo de trabajo**

1. El usuario abre la ficha técnica.
2. El sistema presenta pestañas de servicio, topología, ONU, incidencias, suspensiones y configuración.
3. El usuario edita campos habilitados por rol.
4. El usuario guarda cambios.
5. El sistema sincroniza parámetros ONU cuando corresponde.

**Datos**  
| Campo | Descripción |
|---|---|
| PPPoE/VLAN | Parámetros técnicos del servicio. |
| WiFi | SSID y contraseña del equipo. |
| Observaciones | Registro técnico operativo. |
| Equipos adicionales | Equipamiento complementario asignado. |

### 3.3 Eliminar Ficha Técnica

**Descripción**  
Permite que el usuario elimine una ficha técnica existente desde la vista de lista/formulario.

**Flujo de trabajo**

1. El usuario abre la ficha a eliminar.
2. El usuario ejecuta eliminar.
3. El sistema remueve el registro según reglas de integridad de Odoo.

**Datos**  
| Campo | Descripción |
|---|---|
| Ficha técnica | Registro de servicio técnico del cliente. |
| Vínculos | Puede afectar navegación con OT/suspensiones relacionadas. |

### 3.4 Sincronizar ficha desde OT origen

**Descripción**  
Permite que el usuario actualice la ficha técnica con datos de la OT origen sin sobrescribir datos históricos no vacíos.

**Flujo de trabajo**

1. El usuario abre la ficha con OT vinculada.
2. El usuario presiona Actualizar datos.
3. El sistema toma campos técnicos y comerciales desde la OT.
4. El sistema completa campos faltantes y preserva datos existentes.

**Datos**  
| Campo | Descripción |
|---|---|
| OT origen | Fuente de sincronización de datos. |
| Campos técnicos | Topología, ONU, credenciales y parámetros de servicio. |
| Política de escritura | No borra valores existentes con nulos. |

### 3.5 Crear OT de baja desde ficha técnica

**Descripción**  
Permite que el usuario inicie una baja formal del servicio desde una ficha activa.

**Flujo de trabajo**

1. El usuario abre una ficha en estado Activo.
2. El usuario presiona Dar de baja.
3. El sistema crea una OT de tipo Baja/Retiro con datos técnicos heredados.
4. El sistema abre la OT generada para su ejecución.

**Datos**  
| Campo | Descripción |
|---|---|
| Tipo OT | Baja/Retiro. |
| Recursos heredados | OLT, subinterfaz, NAP, puerto y ONU vinculados. |
| Estado inicial OT | Pendiente. |

## 4. Suspensiones FTTH

### 4.1 Listar Suspensiones

**Descripción**  
Permite que el usuario consulte registros de suspensión y reconexión asociados a contratos/fichas técnicas.

**Flujo de trabajo**

1. El usuario ingresa a Suspensiones > Registros de suspensión.
2. El sistema muestra la lista con estado y fechas clave.
3. El usuario filtra por estado o agrupa por contrato.
4. El usuario abre el registro para gestión puntual.

**Datos**  
| Campo | Descripción |
|---|---|
| Contrato | Contrato afectado por suspensión. |
| Ficha técnica | Servicio técnico vinculado. |
| Fecha corte | Fecha de ejecución de corte. |
| Fecha reconexión | Fecha de restitución del servicio. |
| Estado | Pendiente, En corte, Reconexión. |

### 4.2 Registrar Suspensión

**Descripción**  
Permite que el usuario cree manualmente un registro de suspensión para control operativo.

**Flujo de trabajo**

1. El usuario abre Registros de suspensión.
2. El usuario crea un registro nuevo.
3. El usuario selecciona contrato y ficha técnica.
4. El usuario guarda en estado Pendiente.

**Datos**  
| Campo | Descripción |
|---|---|
| Contrato | Campo requerido. |
| Ficha técnica | Relación opcional pero recomendada. |
| Fecha registro | Se genera automáticamente. |
| Estado inicial | Pendiente. |

### 4.3 Editar Suspensión

**Descripción**  
Permite que el usuario actualice fechas y relaciones de la suspensión.

**Flujo de trabajo**

1. El usuario abre el registro.
2. El usuario modifica los campos habilitados.
3. El usuario guarda cambios.
4. El sistema actualiza el historial del registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Fecha corte | Editable según estado. |
| Fecha reconexión | Editable según estado. |
| Ficha técnica | Puede vincularse/desvincularse. |

### 4.4 Eliminar Suspensión

**Descripción**  
Permite que el usuario elimine un registro de suspensión cuando proceda administrativamente.

**Flujo de trabajo**

1. El usuario abre la suspensión.
2. El usuario ejecuta eliminar.
3. El sistema elimina el registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Registro suspensión | Documento operativo de corte/reconexión. |
| Trazabilidad | La eliminación elimina su historial asociado en ese registro. |

### 4.5 Marcar en corte y reconexión

**Descripción**  
Permite que el usuario mueva el estado de suspensión y sincronice el estado de la ficha técnica.

**Flujo de trabajo**

1. El usuario abre una suspensión pendiente.
2. El usuario presiona Marcar en corte.
3. El sistema cambia estado a En corte y actualiza ficha técnica a corte.
4. El usuario presiona Marcar reconexión cuando aplica.
5. El sistema cambia estado a Reconexión y ficha técnica a activa.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado suspensión | Pendiente, En corte, Reconexión. |
| Estado ficha técnica | Se sincroniza con corte/activo. |
| Fechas | Corte y reconexión se completan automáticamente si faltan. |

## 5. Inventario ONU y Catálogos

### 5.1 Listar ONUs

**Descripción**  
Permite que el usuario consulte el inventario de ONUs por estado, marca y asignación.

**Flujo de trabajo**

1. El usuario ingresa a Inventario ONUs y Accesorios > Equipos ONU.
2. El sistema muestra la lista de ONUs.
3. El usuario filtra por estado o agrupa por marca/estado.
4. El usuario abre el formulario para detalle técnico.

**Datos**  
| Campo | Descripción |
|---|---|
| Número de serie | Identificador principal de ONU. |
| Marca/Modelo | Catálogo técnico del equipo. |
| Estado | Disponible, En campo, Asignado, Retirado, Dañado. |
| Cliente | Ficha técnica vinculada cuando existe. |
| Instalador | Responsable asociado. |

### 5.2 Registrar ONU

**Descripción**  
Permite que el usuario registre un nuevo equipo ONU en inventario.

**Flujo de trabajo**

1. El usuario abre Inventario ONUs.
2. El usuario crea nuevo registro.
3. El usuario completa número de serie, marca y modelo.
4. El usuario agrega parámetros PON/PPPoE/WiFi si corresponde.
5. El usuario guarda el registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Número de serie | Obligatorio y único en el sistema. |
| Marca/Modelo | Referencia catalogada. |
| Estado inicial | Disponible. |
| Parámetros técnicos | PON SN, VLAN, PPPoE, WiFi, T-CONT, GEM Port y V-Port. |

### 5.3 Editar ONU

**Descripción**  
Permite que el usuario modifique datos técnicos y administrativos de la ONU.

**Flujo de trabajo**

1. El usuario abre la ONU.
2. El usuario edita campos permitidos.
3. El usuario guarda cambios.
4. El sistema mantiene trazabilidad de estado y asignación.

**Datos**  
| Campo | Descripción |
|---|---|
| Perfil OLT | Perfil técnico del equipo. |
| Credenciales | Datos PPPoE y gestión. |
| WiFi | SSID y contraseña. |
| Estado | Ciclo operativo de inventario. |

### 5.4 Eliminar ONU

**Descripción**  
Permite que el usuario elimine un equipo ONU del inventario.

**Flujo de trabajo**

1. El usuario abre la ONU a eliminar.
2. El usuario ejecuta eliminar.
3. El sistema elimina el registro según integridad de vínculos.

**Datos**  
| Campo | Descripción |
|---|---|
| ONU | Registro de inventario técnico. |
| Vínculos | Deben respetar reglas relacionales de Odoo. |

### 5.5 Retirar ONU de inventario

**Descripción**  
Permite que el usuario marque una ONU como Retirada y limpie sus vínculos operativos.

**Flujo de trabajo**

1. El usuario abre la ONU.
2. El usuario presiona Retirar del inventario.
3. El sistema cambia estado a Retirado.
4. El sistema limpia cliente y subinterfaz asociados.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado final | Retirado. |
| Cliente/Subinterfaz | Se desvinculan automáticamente. |

### 5.6 Listar/Registrar/Editar/Eliminar Marcas FTTH

**Descripción**  
Permite que el usuario mantenga el catálogo de marcas para inventario ONU.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Operación > Marcas.
2. El sistema muestra listado con estado activo/archivado.
3. El usuario crea, edita o elimina registros según necesidad.
4. El usuario guarda cambios.

**Datos**  
| Campo | Descripción |
|---|---|
| Marca | Nombre de fabricante. |
| Activo | Habilita/archiva la marca. |
| Notas | Observaciones del catálogo. |

### 5.7 Listar/Registrar/Editar/Eliminar Modelos FTTH

**Descripción**  
Permite que el usuario mantenga el catálogo de modelos para inventario ONU.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Operación > Modelos.
2. El sistema muestra listado de modelos.
3. El usuario crea, edita o elimina modelos.
4. El usuario guarda los cambios.

**Datos**  
| Campo | Descripción |
|---|---|
| Modelo | Nombre técnico/comercial del modelo. |
| Activo | Estado de disponibilidad del modelo. |
| Notas | Información complementaria. |

## 6. Accesorios y Equipos Complementarios

### 6.1 Listar/Registrar/Editar/Eliminar Catálogo de Accesorios

**Descripción**  
Permite que el usuario gestione el catálogo de materiales utilizados en instalaciones FTTH.

**Flujo de trabajo**

1. El usuario ingresa a Inventario ONUs y Accesorios > Accesorios > Catálogo.
2. El sistema muestra el catálogo con unidad y estado.
3. El usuario crea, edita o elimina accesorios.
4. El usuario guarda cambios.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre | Nombre del accesorio. |
| Código SKU | Código interno opcional. |
| Tipo de unidad | Metros o Unidades. |
| Activo | Disponibilidad en formularios operativos. |

### 6.2 Listar/Registrar/Editar/Eliminar Accesorios de OT

**Descripción**  
Permite que el usuario registre cantidades utilizadas de accesorios en una OT o ficha técnica.

**Flujo de trabajo**

1. El usuario abre una OT o ficha con pestaña de accesorios.
2. El usuario agrega líneas de accesorio.
3. El usuario define cantidad.
4. El sistema toma unidad desde catálogo.
5. El usuario guarda cambios o elimina líneas no válidas.

**Datos**  
| Campo | Descripción |
|---|---|
| Accesorio | Material seleccionado del catálogo activo. |
| Cantidad | Debe ser mayor a cero. |
| Unidad | Derivada del tipo del accesorio. |
| OT/Ficha | Relación de uso operativo. |

### 6.3 Listar/Registrar/Editar/Eliminar Equipos Adicionales

**Descripción**  
Permite que el usuario gestione equipos adicionales asociados a servicios de cliente.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Operación > Equipos Adicionales.
2. El sistema muestra lista por estado y servicio asignado.
3. El usuario crea o edita registro.
4. El sistema sincroniza estado según exista servicio asignado.
5. El usuario elimina el registro cuando ya no aplica.

**Datos**  
| Campo | Descripción |
|---|---|
| Equipo adicional | Nombre del equipo complementario. |
| Marca/Rótulo/SN | Identificación técnica del activo. |
| Servicio asignado | Ficha técnica relacionada. |
| Estado | Disponible o Asignado (derivado de relación). |

## 7. Topología GPON/FTTH

### 7.1 Listar/Registrar/Editar/Eliminar Regionales

**Descripción**  
Permite que el usuario administre regionales de despliegue FTTH.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Ubicación y segmentación > Regionales.
2. El sistema muestra listado con prefijo y cantidad de nodos.
3. El usuario crea, edita o elimina una regional.
4. El sistema aplica validaciones de unicidad.

**Datos**  
| Campo | Descripción |
|---|---|
| Ciudad/Regional | Nombre de la regional. |
| Prefijo | Prefijo técnico único. |
| Activo | Estado de uso. |
| Nodos | Relación de nodos asociados. |

### 7.2 Listar/Registrar/Editar/Eliminar Nodos

**Descripción**  
Permite que el usuario administre nodos de agregación/acceso y su vínculo con OLTs.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Nodos.
2. El sistema muestra listado con tipo, regional y cantidad de OLTs.
3. El usuario crea, edita o elimina nodo.
4. El sistema valida numeración y unicidad por regional.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre del nodo | Identificador operativo del nodo. |
| Nº Nodo | Número secuencial del nodo. |
| Tipo de nodo | Agregación o Acceso. |
| Regional | Regional propietaria. |
| OLTs | Equipos OLT asociados. |

### 7.3 Listar/Registrar/Editar/Eliminar Tecnologías

**Descripción**  
Permite que el usuario gestione tecnologías FTTH usadas en codificación de equipos.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Red GPON > Tecnologías.
2. El sistema muestra listado de tecnología y prefijo.
3. El usuario crea, edita o elimina registros.
4. El sistema valida unicidad de nombre y prefijo.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre | Nombre de tecnología. |
| Prefijo | Prefijo técnico único para codificación. |
| Activo | Estado operativo del catálogo. |

### 7.4 Listar/Registrar/Editar/Eliminar OLTs

**Descripción**  
Permite que el usuario administre OLTs por nodo y tecnología, con código técnico generado.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Red GPON > OLTs.
2. El sistema muestra OLTs con código, nodo y puertos.
3. El usuario crea, edita o elimina OLT.
4. El sistema calcula código OLT y número secuencial por nodo.

**Datos**  
| Campo | Descripción |
|---|---|
| Código OLT | Composición regional-nodo-OLT-tecnología. |
| Nodo | Nodo de pertenencia. |
| Tecnología | Tecnología asociada. |
| Marca/Modelo/SN | Datos de inventario del equipo. |
| Puertos | Total de puertos PON vinculados. |

### 7.5 Generar puertos PON (asistente)

**Descripción**  
Permite que el usuario genere puertos PON masivamente para una OLT.

**Flujo de trabajo**

1. El usuario abre una OLT.
2. El usuario presiona Generar Puertos.
3. El sistema abre asistente con tecnología, prefijo, chasis, slot y cantidad.
4. El usuario completa parámetros.
5. El usuario confirma generación.
6. El sistema crea puertos secuenciales sin duplicidad física.

**Datos**  
| Campo | Descripción |
|---|---|
| Prefijo | Prefijo técnico de interfaz (ej. gpon-olt). |
| Chasis/Slot/Puerto | Estructura física de interface_port. |
| Cantidad | Número de puertos a crear. |
| Tecnología | Tecnología asociada al puerto. |

### 7.6 Listar/Registrar/Editar/Eliminar Puertos PON

**Descripción**  
Permite que el usuario administre puertos PON y su ocupación de subinterfaces.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Red GPON > Puertos PON.
2. El sistema muestra indicadores de capacidad, usadas, libres y ocupación.
3. El usuario crea, edita o elimina puerto.
4. El sistema valida capacidad, rangos y unicidad técnica.

**Datos**  
| Campo | Descripción |
|---|---|
| Interfaz PON | Identificador físico del puerto. |
| Capacidad máxima | Límite de subinterfaces admitidas. |
| Usadas/Libres | Métricas operativas por estado. |
| Ocupación % | Indicador visual de saturación. |

### 7.7 Generar subinterfaces OLT (asistente)

**Descripción**  
Permite que el usuario genere subinterfaces masivamente hasta una capacidad objetivo.

**Flujo de trabajo**

1. El usuario abre un puerto PON.
2. El usuario presiona Generar Subinterfaces.
3. El sistema abre asistente con capacidad actual y objetivo.
4. El usuario define prefijo y VLAN.
5. El usuario confirma.
6. El sistema crea subinterfaces faltantes y valida límites.

**Datos**  
| Campo | Descripción |
|---|---|
| Generar hasta | Capacidad total objetivo del puerto. |
| VLAN | VLAN para nuevas subinterfaces (1-4094). |
| Prefijo | Prefijo del código de subinterfaz. |
| Existentes | Conteo actual previo a generar. |

### 7.8 Listar/Registrar/Editar/Eliminar ODN

**Descripción**  
Permite que el usuario administre ODN por OLT y nodo, con número ODN único por nodo.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Red GPON > ODN.
2. El sistema muestra listado con nodo, OLT y puerto ODF.
3. El usuario crea, edita o elimina ODN.
4. El sistema valida unicidad y numeración.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre ODN | Nombre identificador de red de distribución. |
| Nº ODN | Número de ODN por nodo. |
| OLT asociada | Solo una ODN por OLT. |
| ODF/Puerto | Puerto físico ODF relacionado. |

### 7.9 Listar/Registrar/Editar/Eliminar Grupos de Cajas

**Descripción**  
Permite que el usuario administre grupos (zonas técnicas) de cajas NAP y splitters.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Ubicación y segmentación > Zonas / Grupos de Cajas.
2. El sistema muestra grupo, zona, OLT, ODN y capacidad.
3. El usuario crea, edita o elimina grupo.
4. El sistema valida número de grupo y capacidad total.

**Datos**  
| Campo | Descripción |
|---|---|
| Nº Grupo | Identificador numérico del grupo. |
| Zona | Zona geográfica asociada. |
| OLT/Puerto/ODN | Relación de red principal. |
| Splitter 1/2 nivel | Configuración óptica del grupo. |
| Total puertos | Suma total de capacidad de NAPs del grupo. |

### 7.10 Generar cajas NAP (asistente)

**Descripción**  
Permite que el usuario genere cajas NAP masivamente en un grupo y cree sus puertos automáticamente.

**Flujo de trabajo**

1. El usuario abre un grupo de cajas.
2. El usuario presiona Generar Cajas.
3. El sistema abre asistente de cantidad y capacidad por caja.
4. El usuario confirma.
5. El sistema valida límites por PON/splitter/subinterfaces.
6. El sistema crea cajas y puertos asociados.

**Datos**  
| Campo | Descripción |
|---|---|
| Cantidad | Número de cajas a crear. |
| Capacidad por caja | 8 o 16 puertos. |
| Límite efectivo | Mínimo entre capacidad PON y splitters. |
| Validación subinterfaces | Verifica disponibilidad libre para puertos solicitados. |

### 7.11 Listar/Registrar/Editar/Eliminar Cajas NAP

**Descripción**  
Permite que el usuario administre cajas NAP y su estado de ocupación.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Red GPON > Cajas NAP.
2. El sistema muestra identificador, grupo, capacidad y puertos libres.
3. El usuario crea, edita o elimina cajas.
4. El sistema calcula estado disponible/parcial/ocupada.

**Datos**  
| Campo | Descripción |
|---|---|
| Identificador NAP | Código del tipo 01A, 01B, etc. |
| Grupo de caja | Grupo técnico al que pertenece. |
| Capacidad | Total de puertos de la caja. |
| Puertos libres | Conteo dinámico por estados no usados. |
| Estado | Disponible, Parcial u Ocupada. |

### 7.12 Listar/Registrar/Editar/Eliminar Puertos de Caja

**Descripción**  
Permite que el usuario administre puertos NAP y su vinculación con subinterfaces.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Red GPON > Puertos de Caja.
2. El sistema muestra estados y relaciones técnicas.
3. El usuario crea, edita o elimina puertos.
4. El sistema sincroniza vínculo con subinterfaces cuando corresponde.

**Datos**  
| Campo | Descripción |
|---|---|
| Caja NAP | Caja propietaria del puerto. |
| Nº Puerto | Número secuencial del puerto. |
| Estado | Libre, Infraestructura, Asignada, Reservada o Activa. |
| Subinterfaz OLT | Vinculación de extremo a extremo. |

### 7.13 Listar/Registrar/Editar/Eliminar Subinterfaces OLT

**Descripción**  
Permite que el usuario administre subinterfaces de puertos PON y su relación con cliente/ONU/NAP.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Red GPON > Subinterfaces OLT.
2. El sistema muestra código, VLAN, estado y vínculos.
3. El usuario crea, edita o elimina subinterfaces.
4. El sistema valida unicidad, VLAN y sincronización con puerto NAP.

**Datos**  
| Campo | Descripción |
|---|---|
| Código | Identificador técnico de subinterfaz. |
| VLAN | VLAN operativa (1-4094). |
| Puerto OLT | Puerto físico de pertenencia. |
| Estado | Libre, Infraestructura, Asignada, Reservada o Activa. |
| Cliente/ONU | Vínculos operativos cuando existe servicio activo. |

## 8. Zonas y Cobertura FTTH

### 8.1 Listar/Registrar/Editar/Eliminar Zonas

**Descripción**  
Permite que el usuario administre zonas con indicadores de cobertura FTTH real end-to-end.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Ubicación y segmentación > Zonas.
2. El sistema muestra estados de cobertura y capacidad disponible.
3. El usuario crea, edita o elimina zona.
4. El sistema recalcula métricas de cobertura real.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre | Nombre de la zona. |
| Estado cobertura | Disponible, En riesgo, Saturado o Sin cobertura. |
| Puertos NAP disponibles | Puertos no usados en la zona válida. |
| Subinterfaces disponibles | Capacidad libre OLT asociada a la zona. |
| Cobertura real | Requiere disponibilidad en NAP y subinterfaces. |

## 9. Instaladores

### 9.1 Listar/Registrar/Editar/Eliminar Instaladores

**Descripción**  
Permite que el usuario mantenga catálogo de instaladores individuales o empresas subcontratistas.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Operación > Instaladores/Técnicos.
2. El sistema muestra listado con tipo y cantidad de OTs.
3. El usuario crea, edita o elimina instalador.
4. El usuario guarda cambios.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre/Razón social | Identificación del instalador. |
| Tipo | Persona o Empresa subcontratista. |
| Encargado responsable | Visible cuando el tipo es empresa. |
| Teléfono | Contacto operativo. |
| Estado | Activo o Inactivo. |

## 10. Reportes y Analítica

### 10.1 Consultar reportes por estado, plan, instalación, instalador y nodo

**Descripción**  
Permite que el usuario analice cartera FTTH mediante vistas lista, gráfico y pivote sobre fichas técnicas.

**Flujo de trabajo**

1. El usuario ingresa a Reportes.
2. El usuario selecciona el reporte requerido.
3. El sistema abre vista con agrupación por defecto según reporte.
4. El usuario ajusta filtros o dimensiones para análisis.

**Datos**  
| Campo | Descripción |
|---|---|
| Clientes por estado | Distribución por estado de servicio. |
| Clientes por plan | Segmentación por plan contratado. |
| Instalaciones por mes | Tendencia temporal de altas. |
| Por instalador | Carga/resultado por técnico. |
| Por nodo/OLT | Distribución técnica por infraestructura. |

### 10.2 Consultar ocupación de puertos OLT

**Descripción**  
Permite que el usuario monitoree saturación de puertos PON y tome decisiones de expansión.

**Flujo de trabajo**

1. El usuario ingresa a Reportes > Ocupación de Puertos.
2. El sistema muestra lista con porcentaje de ocupación.
3. El usuario filtra por rangos (alta/media/baja) o agrupa por OLT/tecnología.
4. El usuario identifica puertos críticos.

**Datos**  
| Campo | Descripción |
|---|---|
| Capacidad máxima | Límite técnico del puerto. |
| Subinterfaces usadas/libres | Indicadores de utilización. |
| Ocupación % | Métrica de saturación del puerto. |
| Semáforo visual | Colores por umbral de ocupación. |

## 11. Configuración de Planilla OT PDF

### 11.1 Editar configuración de diseño de planilla

**Descripción**  
Permite que el usuario administrador configure diseño, textos, colores, QR y secciones del PDF de OT.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Operación > Planilla OT PDF.
2. El sistema abre formulario único de configuración.
3. El usuario modifica parámetros de encabezado, empresa, tipografía y layout.
4. El usuario revisa vista previa en tiempo real.
5. El usuario guarda cambios.

**Datos**  
| Campo | Descripción |
|---|---|
| Encabezado | Título, subtítulo y formato superior del documento. |
| Empresa | Datos institucionales y de contacto. |
| QR | Imágenes QR para cobranzas y soporte. |
| Colores/Fuentes | Estilo visual del reporte. |
| Secciones | Activación/desactivación de bloques del PDF. |

### 11.2 Restaurar diseño por defecto

**Descripción**  
Permite que el usuario restablezca todos los parámetros de planilla OT a valores predeterminados.

**Flujo de trabajo**

1. El usuario abre configuración de planilla.
2. El usuario presiona Restaurar diseño por defecto.
3. El sistema solicita confirmación.
4. El sistema restablece los valores estándar y notifica éxito.

**Datos**  
| Campo | Descripción |
|---|---|
| Acción de restauración | Restituye parámetros visuales y textuales base. |
| Notificación | Mensaje de confirmación en pantalla. |

## 12. Campos condicionales, estados y comportamiento dinámico

### 12.1 Comportamiento condicional en formularios

**Descripción**  
Permite que el sistema muestre, oculte o habilite campos y botones según estado, tipo de proceso y permisos.

**Flujo de trabajo**

1. El usuario abre un formulario de FTTH.
2. El sistema evalúa condiciones de estado/tipo/rol.
3. El sistema aplica visibilidad condicional a acciones y campos.
4. El usuario opera con interfaz contextual al proceso actual.

**Datos**  
| Campo | Descripción |
|---|---|
| Botones de OT | Se habilitan por estado y tipo (instalación/baja). |
| Statusbar | Muestra flujo de estados según proceso. |
| Ribbons | Señalizan incidentes, bajas, cancelaciones y estados técnicos. |
| Campos por rol | Datos sensibles técnicos restringidos por grupos FTTH. |

## 13. Validaciones clave del módulo

### 13.1 Reglas de integridad funcional

**Descripción**  
Permite que el sistema proteja consistencia de topología, inventario y flujo operativo mediante validaciones automáticas.

**Flujo de trabajo**

1. El usuario intenta guardar o ejecutar una acción.
2. El sistema valida reglas del modelo correspondiente.
3. Si la validación falla, el sistema bloquea operación y muestra mensaje.
4. Si la validación cumple, el sistema confirma la acción.

**Datos**  
| Campo | Descripción |
|---|---|
| ONU serial | Debe ser único. |
| Subinterfaz | VLAN válida y unicidad por puerto/código. |
| Puerto PON | Unicidad física y límites de capacidad. |
| Grupo/Caja | Control de capacidad total por grupo. |
| OT de baja | No se crea manualmente desde lista general; se inicia desde ficha técnica. |
| Accesorios OT | Cantidad debe ser positiva y con vínculo válido. |

## 14. Nota de presentación y capturas

### 14.1 Reutilización de evidencias visuales

**Descripción**  
Permite mantener consistencia documental al reutilizar capturas de vistas comunes (lista, formulario, búsqueda y estado) entre funcionalidades similares.

**Flujo de trabajo**

1. El usuario documenta una funcionalidad base con capturas.
2. Para funcionalidades homólogas, el usuario referencia las figuras ya presentadas.
3. El documento evita duplicidad visual y mantiene uniformidad de estilo.

**Datos**  
| Campo | Descripción |
|---|---|
| Vistas homólogas | Lista/formulario/search reutilizables por patrón. |
| Referencias cruzadas | Uso de figuras previas para procesos equivalentes. |
| Consistencia editorial | Uniformidad para exportación a Word/PDF. |

---

### Alcance del manual

Este manual fue elaborado a partir de los modelos Python y vistas XML del módulo Wigo FTTH, documentando únicamente funcionalidades existentes en el código analizado.
