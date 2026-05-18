# Manual de Usuario

## Módulo Wigo Cobranza

### 1. Introducción

El módulo Wigo Cobranza centraliza el registro, control y seguimiento de los cobros mensuales de clientes con contrato activo. El módulo administra la planilla de pagos, la emisión de recibos, la facturación de cobranza, la gestión de deuda vencida e incobrable, la configuración de recibos y las reglas operativas de generación automática.

### 1.1 Estructura funcional del módulo

**Descripción**  
Permite que el usuario navegue por las áreas de gestión de cobros, facturación, incobrables, reportes y configuración desde un único menú principal.

**Flujo de trabajo**

1. El usuario ingresa al módulo Wigo Cobranza.
2. El sistema muestra el menú principal con sus secciones operativas.
3. El usuario selecciona el proceso requerido.
4. El sistema abre la vista correspondiente en formato lista, formulario, kanban, pivote o gráfico.

**Datos**  
| Campo | Descripción |
|---|---|
| Gestión de Cobros | Acceso a clientes con contrato, planilla general y registros de pago. |
| Recibos de Cobro | Administración de recibos emitidos a partir de los pagos confirmados. |
| Facturación | Registro de facturas de cobranza asociadas a un pago. |
| Incobrables | Seguimiento de deuda vencida, corte, baja y recuperación. |
| Gráficos y Reportes | Indicadores analíticos por estado, plan, ajuste e incobrables. |
| Configuración | Reglas de cobranza, tipos de ajuste y diseño del recibo. |

## 2. Planilla General de Cobros

### 2.1 Listar planilla general

**Descripción**  
Permite que el usuario consulte la planilla general de cobros, mostrando los pagos pagados, pendientes y en mora del período seleccionado.

**Flujo de trabajo**

1. El usuario ingresa al módulo Wigo Cobranza.
2. El usuario selecciona el menú Gestión de Cobros > Planilla General.
3. El sistema muestra el listado de pagos con colores por estado.
4. El usuario aplica filtros por cliente, plan, año, tipo de ajuste o modalidad.
5. El usuario puede agrupar la información por año, mes, estado, plan o ajuste.

**Datos**  
| Campo | Descripción |
|---|---|
| Año | Año del período de cobro. |
| Mes | Mes del período de cobro. |
| Código CF | Código del cliente o servicio. |
| Cliente | Titular del contrato. |
| Plan | Plan asociado al cobro. |
| Tipo de ajuste | Ajuste aplicado al cobro mensual. |
| Monto a cobrar | Valor facturado para el período. |
| Monto pagado | Valor efectivamente registrado. |
| Fecha de pago | Fecha de registro del pago. |
| Estado de pago | Estado actual del registro. |
| Registrado por | Usuario que confirmó el cobro. |

### 2.2 Registrar un cobro mensual

**Descripción**  
Permite que el usuario cree un registro mensual de pago para un cliente con contrato activo. El sistema completa datos relacionados del contrato, servicio y período cuando corresponde.

**Flujo de trabajo**

1. El usuario abre un contrato, un cliente o la planilla general.
2. El usuario ejecuta la acción de crear un nuevo cobro.
3. El sistema propone el cliente, contrato, servicio y período sugerido.
4. El usuario valida el tipo de ajuste y los importes.
5. El usuario guarda el registro.
6. El sistema crea el cobro en estado Pendiente.

**Datos**  
| Campo | Descripción |
|---|---|
| Cliente | Cliente con contrato activo. |
| Contrato | Contrato origen del cobro. |
| Servicio (CF) | Servicio FTTH vinculado, cuando existe. |
| Año | Año del período. |
| Mes | Mes del período. |
| Tipo de ajuste | Clasificación operativa del cobro. |
| Monto prorrateo | Monto proporcional del primer mes o ajuste habilitado. |
| Motivo | Justificación del ajuste cuando se requiere. |
| Monto a cobrar | Importe final a facturar. |
| Monto pagado | Importe recibido. |
| Fecha de pago | Fecha del registro de pago. |
| Canal de pago | Medio utilizado para el pago. |
| Comprobante | Referencia o número de comprobante. |
| Comprobante adjunto | Imagen, PDF o archivos de respaldo. |
| Notas | Observaciones operativas. |

### 2.3 Editar un cobro mensual

**Descripción**  
Permite que el usuario actualice un registro de cobro mientras las reglas de estado y contabilidad lo permitan. Cuando el cobro ya fue confirmado, la edición de valores contables exige una justificación.

**Flujo de trabajo**

1. El usuario abre un cobro existente.
2. El sistema muestra el formulario con estado y acciones disponibles.
3. El usuario modifica campos permitidos según el estado del registro.
4. Si el cobro ya fue confirmado, el usuario debe ingresar una justificación de edición contable.
5. El usuario guarda los cambios.
6. El sistema registra la trazabilidad en el chatter.

**Datos**  
| Campo | Descripción |
|---|---|
| Tipo de ajuste | Puede modificar la lógica de cálculo del cobro. |
| Monto prorrateo | Ajuste proporcional cuando el tipo lo permite. |
| Monto a cobrar | Valor facturado, editable con control. |
| Monto pagado | Valor recibido, editable con control. |
| Fecha de pago | Fecha del pago registrado. |
| Canal de pago | Medio de pago. |
| Justificación de edición contable | Texto obligatorio para cambios contables posteriores a la confirmación. |

### 2.4 Eliminar un cobro mensual

**Descripción**  
Permite que el usuario elimine un cobro mensual cuando el registro no sea necesario y sus permisos lo autoricen. La eliminación debe usarse con criterio operativo para evitar inconsistencias en la trazabilidad de pagos.

**Flujo de trabajo**

1. El usuario abre el registro de cobro.
2. El usuario ejecuta la opción de eliminar, si está disponible por permisos.
3. El sistema verifica los permisos del usuario.
4. El sistema elimina el registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Cobro mensual | Registro que se elimina del histórico. |
| Relación con recibo o factura | Debe revisarse antes de eliminar para evitar referencias huérfanas. |

### 2.5 Confirmar pago

**Descripción**  
Permite que el usuario confirme el cobro recibido y cambie el estado del registro a Pagado o Pendiente según el importe registrado.

**Flujo de trabajo**

1. El usuario abre un cobro en estado Pendiente.
2. El usuario completa monto pagado, fecha y canal de pago.
3. El usuario presiona Confirmar Pago.
4. El sistema valida la información obligatoria.
5. El sistema actualiza el estado a Pagado cuando el importe cubre el cobro o a Pendiente cuando existe saldo.
6. El sistema registra el usuario responsable.
7. El sistema actualiza incobrables y servicio FTTH cuando corresponde.

**Datos**  
| Campo | Descripción |
|---|---|
| Monto pagado | Requerido para confirmar el pago. |
| Fecha de pago | Requerida para confirmar el pago. |
| Canal de pago | Requerido para confirmar el pago. |
| Estado de pago | Se actualiza a Pagado o Pendiente. |
| Registrado por | Usuario que ejecuta la confirmación. |

### 2.6 Marcar un cobro en mora

**Descripción**  
Permite que el usuario marque manualmente un cobro como Mora cuando el registro fue creado de forma manual, venció y pertenece a un período anterior.

**Flujo de trabajo**

1. El usuario abre un cobro elegible.
2. El sistema habilita la acción Marcar en Mora solo si el registro cumple la condición.
3. El usuario ejecuta la acción.
4. El sistema cambia el estado a Mora.
5. El sistema registra una nota en el chatter.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado previo | Debe ser Pendiente. |
| Fecha de vencimiento | Debe estar vencida. |
| Período | Debe corresponder a un período anterior. |
| Generación automática | El registro no debe haber sido generado automáticamente. |

### 2.7 Editar valores contables

**Descripción**  
Permite que el usuario edite los valores contables de un cobro confirmado mediante un modo especial de edición.

**Flujo de trabajo**

1. El usuario abre un cobro con estado Pagado.
2. El usuario ejecuta la opción Editar valores contables.
3. El sistema abre el mismo formulario con contexto de edición contable.
4. El usuario modifica montos o datos autorizados.
5. El usuario guarda la información.
6. El sistema registra una nota de auditoría con la justificación.

**Datos**  
| Campo | Descripción |
|---|---|
| Monto a cobrar | Puede ajustarse con justificación. |
| Monto pagado | Puede ajustarse con justificación. |
| Justificación de edición contable | Obligatoria cuando el pago ya fue confirmado. |

### 2.8 Gestionar comprobantes de pago

**Descripción**  
Permite que el usuario cargue, consulte o descargue comprobantes del cobro en formato imagen o PDF.

**Flujo de trabajo**

1. El usuario abre la pestaña Comprobante.
2. El usuario adjunta uno o varios archivos de respaldo.
3. El sistema identifica si el archivo es imagen o PDF.
4. El usuario puede usar Ver en grande o Descargar.
5. Si existen varios archivos, el sistema solicita seleccionar uno.

**Datos**  
| Campo | Descripción |
|---|---|
| Comprobante adjunto | Archivo de respaldo del pago. |
| Nombre del archivo | Nombre del adjunto, usado para identificar el tipo de documento. |
| Vista previa | Imagen visible si el comprobante es gráfico. |
| Documento PDF | Indicador de archivo PDF cargado correctamente. |

### 2.9 Generar recibo desde el cobro

**Descripción**  
Permite que el usuario genere un recibo a partir de un cobro confirmado o pendiente.

**Flujo de trabajo**

1. El usuario abre un cobro en estado Pagado o Pendiente.
2. El usuario presiona Generar Recibo.
3. El sistema crea el recibo si no existe uno vigente.
4. El sistema abre el formulario del recibo generado.

**Datos**  
| Campo | Descripción |
|---|---|
| Cobro origen | Fuente del recibo. |
| Estado del cobro | Debe ser Pagado o Pendiente. |
| Recibo asociado | Se crea o reutiliza según exista un registro vigente. |

### 2.10 Abrir, imprimir o registrar factura desde el cobro

**Descripción**  
Permite que el usuario consulte el recibo asociado, lo imprima o registre una factura de cobranza a partir del pago.

**Flujo de trabajo**

1. El usuario abre el cobro confirmado.
2. El usuario selecciona Ver Recibo, Imprimir Recibo o Registrar Factura.
3. El sistema abre el documento relacionado o el formulario de factura con datos prellenados.
4. El usuario completa la información faltante cuando corresponde.

**Datos**  
| Campo | Descripción |
|---|---|
| Recibo de cobro | Documento emitido desde el pago. |
| Factura de cobranza | Documento contable asociado al cobro. |
| Período facturado | Se toma del cobro origen. |
| Monto total | Se propone desde el monto pagado. |

### 2.11 Abrir cliente o CRM desde el cobro

**Descripción**  
Permite que el usuario navegue desde el cobro hacia la ficha del cliente o hacia el lead ganado del CRM cuando existe relación comercial.

**Flujo de trabajo**

1. El usuario abre un cobro vinculado a un cliente.
2. El usuario selecciona Abrir Cliente o Abrir CRM.
3. El sistema abre el registro correspondiente en una nueva vista.
4. El usuario revisa datos complementarios del cliente o contrato.

**Datos**  
| Campo | Descripción |
|---|---|
| Cliente | Registro de res.partner asociado. |
| Lead CRM | Oportunidad o lead ganado relacionado. |
| Zona, dirección y ubicación CRM | Datos de referencia comercial y operativa. |

## 3. Clientes con Contrato

### 3.1 Listar clientes con contrato

**Descripción**  
Permite que el usuario consulte los clientes que poseen contratos activos, con vistas kanban, lista y formulario.

**Flujo de trabajo**

1. El usuario ingresa a Gestión de Cobros > Clientes con Contrato.
2. El sistema muestra los clientes filtrados con contrato activo.
3. El usuario revisa los contadores de contratos activos y totales.
4. El usuario puede abrir la ficha del cliente o consultar sus contratos.

**Datos**  
| Campo | Descripción |
|---|---|
| Cliente | Nombre del contacto. |
| CI | Documento de identidad del cliente. |
| Celular | Número móvil del cliente. |
| Zona | Zona de cobranza. |
| Dirección | Dirección de referencia. |
| Contratos activos | Cantidad de contratos habilitados. |
| Total contratos | Cantidad total de contratos no sustituidos. |

### 3.2 Consultar ficha de cliente

**Descripción**  
Permite que el usuario revise la ficha de cobranza de un cliente con sus datos resumidos y sus contratos activos.

**Flujo de trabajo**

1. El usuario abre la vista formulario del cliente.
2. El sistema muestra los datos de contacto y la lista de contratos activos.
3. El usuario puede abrir los cobros mensuales del contrato o consultar más detalles del contacto.

**Datos**  
| Campo | Descripción |
|---|---|
| CI | Documento de identidad. |
| Celular | Número de contacto. |
| Dirección | Dirección principal para cobranza. |
| Contratos | Contratos activos del cliente. |
| Plan | Plan asociado a cada contrato. |
| Estado | Estado contractual actual. |

### 3.3 Registrar factura o incobrable desde el cliente

**Descripción**  
Permite que el usuario inicie una factura de cobranza o una declaración de incobrable desde la ficha del cliente.

**Flujo de trabajo**

1. El usuario abre la ficha del cliente.
2. El usuario selecciona Registrar Factura o Declarar Incobrable.
3. El sistema abre el formulario correspondiente con datos prellenados.
4. El usuario completa la información restante y guarda.

**Datos**  
| Campo | Descripción |
|---|---|
| Cliente | Titular del registro. |
| Contrato | Contrato activo o disponible. |
| Servicio FTTH | Servicio relacionado cuando existe. |

## 4. Recibos de Cobro

### 4.1 Listar recibos

**Descripción**  
Permite que el usuario consulte los recibos emitidos, en borrador o anulados, con vistas kanban, lista y formulario.

**Flujo de trabajo**

1. El usuario ingresa a Gestión de Cobros > Recibos de Cobro.
2. El sistema muestra el listado con tarjetas y estados visuales.
3. El usuario aplica filtros por estado, cliente o período.
4. El usuario abre el recibo requerido.

**Datos**  
| Campo | Descripción |
|---|---|
| Nº Recibo | Número secuencial del recibo. |
| Cliente | Cliente origen del cobro. |
| Código CF | Código del servicio o contrato. |
| Período | Período facturado. |
| Monto cobrado | Valor registrado en el pago. |
| Canal de pago | Medio utilizado. |
| Fecha de pago | Fecha del cobro origen. |
| Estado | Borrador, Emitido o Anulado. |

### 4.2 Emitir un recibo

**Descripción**  
Permite que el usuario confirme un recibo en estado Borrador y lo pase a Emitido.

**Flujo de trabajo**

1. El usuario abre un recibo en borrador.
2. El usuario presiona Emitir Recibo.
3. El sistema valida que el recibo se encuentre en borrador.
4. El sistema cambia el estado a Emitido.
5. El sistema actualiza el cobro origen.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado | Debe ser Borrador para emitir. |
| Número de recibo | Se mantiene como identificador final. |

### 4.3 Editar o regresar a borrador

**Descripción**  
Permite que el usuario devuelva un recibo emitido a borrador para corregir información antes de volver a emitirlo.

**Flujo de trabajo**

1. El usuario abre un recibo emitido.
2. El usuario presiona Editar.
3. El sistema devuelve el registro a borrador.
4. El usuario modifica los datos permitidos.
5. El usuario emite nuevamente el recibo.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado | Debe ser Emitido para volver a borrador. |
| Descripción del servicio | Puede seguir editándose según la interfaz. |
| Firmante | Puede personalizarse por recibo. |

### 4.4 Anular un recibo

**Descripción**  
Permite que el usuario anule un recibo emitido o en borrador cuando el documento ya no debe utilizarse.

**Flujo de trabajo**

1. El usuario abre el recibo.
2. El usuario presiona Anular.
3. El sistema cambia el estado a Anulado.
4. El sistema bloquea la modificación posterior del recibo.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado | Pasa a Anulado. |
| Motivo operativo | Debe definirse según la gestión interna. |

### 4.5 Imprimir y previsualizar recibos

**Descripción**  
Permite que el usuario imprima el recibo en formato PDF o utilice la vista previa del documento.

**Flujo de trabajo**

1. El usuario abre un recibo.
2. El usuario selecciona Imprimir o una variante de impresión.
3. El sistema genera el PDF QWeb.
4. El sistema usa la configuración de diseño activa.

**Datos**  
| Campo | Descripción |
|---|---|
| Monto en letras | Valor total expresado en texto. |
| Empresa | Datos visuales del encabezado. |
| Logo | Imagen corporativa del recibo. |
| Firmante | Firma principal y datos complementarios. |
| Pie de página | Texto opcional de cierre. |

### 4.6 Eliminar un recibo

**Descripción**  
Permite que el usuario elimine un recibo cuando el flujo operativo y los permisos lo permitan. La eliminación debe evaluarse con cuidado por su relación con el cobro origen y la trazabilidad documental.

**Flujo de trabajo**

1. El usuario abre el recibo.
2. El usuario ejecuta la opción de eliminar, si está disponible.
3. El sistema valida permisos y dependencias.
4. El sistema elimina el registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Cobro origen | Debe revisarse antes de eliminar. |
| Estado del recibo | Debe validarse para evitar pérdida de trazabilidad. |

## 5. Facturación

### 5.1 Listar facturas de cobranza

**Descripción**  
Permite que el usuario consulte las facturas de cobranza registradas, con análisis por estado y período.

**Flujo de trabajo**

1. El usuario ingresa a Gestión de Cobros > Facturación.
2. El sistema muestra el listado de facturas.
3. El usuario aplica filtros por cliente, código, período o estado.
4. El usuario abre la factura para revisar sus datos.

**Datos**  
| Campo | Descripción |
|---|---|
| Nº Factura | Número de factura de cobranza. |
| Nº Autorización SIAT | Autorización fiscal opcional. |
| Cliente | Cliente al que se factura. |
| Contrato | Contrato asociado al registro. |
| Código CF | Código del servicio. |
| Razón social | Nombre o razón social del cliente. |
| NIT / CI | Identificación fiscal o personal. |
| Fecha de emisión | Fecha del documento. |
| Período facturado | Período cubierto por la factura. |
| Monto total | Total bruto. |
| Descuento | Descuento aplicado. |
| Monto neto | Total neto resultante. |
| Estado | Pendiente, Emitido o Anulada. |

### 5.2 Registrar factura de cobranza

**Descripción**  
Permite que el usuario cree una factura asociada a un pago y complete sus datos fiscales o comerciales.

**Flujo de trabajo**

1. El usuario abre un cobro o un cliente.
2. El usuario ejecuta Registrar Factura.
3. El sistema propone datos del pago, del cliente y del contrato.
4. El usuario ajusta número de factura, autorización y montos si corresponde.
5. El usuario guarda el registro.
6. El sistema marca la factura como Emitida cuando procede.

**Datos**  
| Campo | Descripción |
|---|---|
| Pago asociado | Cobro de origen. |
| Cliente | Titular de la factura. |
| Contrato | Contrato vinculado. |
| Razón social | Nombre o razón social. |
| NIT / CI | Documento fiscal o de identidad. |
| Monto total | Importe base. |
| Descuento | Descuento aplicado. |
| Monto neto | Importe final. |

### 5.3 Emitir, anular o eliminar una factura

**Descripción**  
Permite que el usuario actualice el estado de una factura de cobranza o la elimine cuando la operación lo permita.

**Flujo de trabajo**

1. El usuario abre la factura.
2. El usuario ejecuta Marcar Emitida o Anular según corresponda.
3. El sistema actualiza el estado del documento.
4. Si la eliminación está permitida, el usuario puede suprimir el registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado | Cambia entre Pendiente, Emitido y Anulada. |
| Notas | Observaciones complementarias. |

## 6. Incobrables

### 6.1 Listar incobrables

**Descripción**  
Permite que el usuario consulte los registros de deuda incobrable, con indicadores visuales por estado y vistas de análisis.

**Flujo de trabajo**

1. El usuario ingresa a Gestión de Cobros > Incobrables.
2. El sistema muestra la lista de registros.
3. El usuario puede abrir un formulario o cambiar a vistas pivote y gráfico.
4. El usuario filtra por estado, cliente, plan o meses adeudados.

**Datos**  
| Campo | Descripción |
|---|---|
| Cliente | Cliente afectado. |
| Contrato | Contrato asociado. |
| Servicio (CF) | Servicio FTTH asociado. |
| Meses adeudados | Períodos pendientes descritos por el usuario. |
| Monto total adeudado | Total de deuda acumulada. |
| Monto cobrado | Monto efectivamente recuperado. |
| Monto incobrable definitivo | Diferencia entre deuda y cobro. |
| Fecha de declaración | Fecha de registro del incobrable. |
| Fecha baja de servicio | Fecha de baja del servicio, si aplica. |
| Estado | En gestión, En corte, Baja - Incobrable o Recuperado. |

### 6.2 Marcar un incobrable en corte

**Descripción**  
Permite que el usuario pase el caso a estado En corte y cree o actualice la suspensión FTTH correspondiente.

**Flujo de trabajo**

1. El usuario abre un registro activo de incobrable.
2. El usuario presiona Marcar en corte.
3. El sistema valida que el caso no esté ya recuperado o dado de baja.
4. El sistema cambia el estado a En corte.
5. El sistema busca o crea la suspensión FTTH asociada.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado | Debe permitir transición a corte. |
| Suspensión FTTH | Se asocia o actualiza automáticamente. |

### 6.3 Declarar baja incobrable

**Descripción**  
Permite que el usuario registre la baja definitiva por incobrable y ajuste el servicio FTTH cuando exista relación técnica.

**Flujo de trabajo**

1. El usuario abre el registro incobrable.
2. El usuario presiona Baja Incobrable.
3. El sistema cambia el estado del incobrable.
4. El sistema registra la fecha de baja del servicio si no existe.
5. El sistema marca el servicio FTTH como baja definitiva cuando corresponde.

**Datos**  
| Campo | Descripción |
|---|---|
| Fecha baja de servicio | Se completa automáticamente si está vacía. |
| Estado del servicio | Puede cambiar a baja. |
| Estado de pago | Se actualiza a baja definitiva en el servicio FTTH. |

### 6.4 Marcar un incobrable como recuperado

**Descripción**  
Permite que el usuario declare recuperado un caso cuando al menos uno de los meses adeudados ya figura pagado.

**Flujo de trabajo**

1. El usuario abre un incobrable con contrato asociado.
2. El usuario presiona Marcar recuperado.
3. El sistema valida la existencia de pagos pagados para los períodos adeudados.
4. El sistema cambia el estado a Recuperado.

**Datos**  
| Campo | Descripción |
|---|---|
| Contrato | Requerido para validar la recuperación. |
| Meses adeudados | Deben poder identificarse con claridad. |
| Pago pagado | Debe existir al menos un período recuperado. |

### 6.5 Abrir suspensión o pagos del contrato

**Descripción**  
Permite que el usuario navegue a la suspensión FTTH o a la lista completa de pagos del contrato desde el incobrable.

**Flujo de trabajo**

1. El usuario abre el incobrable.
2. El usuario selecciona Ver suspensión o Ver pagos.
3. El sistema abre el registro relacionado.

**Datos**  
| Campo | Descripción |
|---|---|
| Suspensión FTTH | Registro de corte/reconexión. |
| Cobros del contrato | Historial mensual asociado. |

### 6.6 Eliminar un incobrable

**Descripción**  
Permite que el usuario elimine un registro incobrable cuando la operación y los permisos lo autoricen.

**Flujo de trabajo**

1. El usuario abre el registro.
2. El usuario ejecuta la opción de eliminar, si está habilitada.
3. El sistema valida dependencias y permisos.
4. El sistema suprime el registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Contrato | Debe revisarse antes de eliminar. |
| Suspensión asociada | Debe evaluarse antes de eliminar. |

## 7. Reglas de Cobranza

### 7.1 Listar reglas de cobranza

**Descripción**  
Permite que el usuario consulte las reglas operativas que determinan la generación automática de cobros, la mora y la creación de incobrables.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Reglas de Cobranza.
2. El sistema muestra las reglas registradas.
3. El usuario reordena la prioridad si corresponde.
4. El usuario abre la regla para revisar sus criterios.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre | Nombre funcional de la regla. |
| Modalidad de pago | Aplica a prepago, postpago o todas. |
| Día de generación | Día del mes para generar el debe automáticamente. |
| Generación automática | Controla si la regla se usa en cron. |
| Criterio de mora | Días o meses. |
| Días para mora | Umbral cuando se usa criterio por días. |
| Meses para mora | Umbral cuando se usa criterio por meses. |
| Criterio de incobrable | Días o meses. |
| Días para incobrable | Umbral cuando se usa criterio por días. |
| Meses consecutivos para incobrable | Umbral cuando se usa criterio por meses. |
| Estado inicial del debe | Pendiente o Pagado. |

### 7.2 Crear o editar una regla de cobranza

**Descripción**  
Permite que el usuario defina nuevas reglas de negocio o ajuste las existentes según la política de cobranza.

**Flujo de trabajo**

1. El usuario abre el formulario de regla.
2. El usuario completa el nombre y la modalidad.
3. El usuario define la generación automática y el día de generación.
4. El usuario configura los criterios de mora e incobrable.
5. El usuario guarda la regla.

**Datos**  
| Campo | Descripción |
|---|---|
| Prioridad | Orden de evaluación de la regla. |
| Día de generación | Debe estar entre 1 y 28. |
| Días/Meses de mora | Deben ser valores no negativos. |
| Días/Meses de incobrable | Deben ser valores no negativos. |

### 7.3 Eliminar una regla de cobranza

**Descripción**  
Permite que el usuario elimine una regla cuando ya no sea necesaria y no exista dependencia operativa.

**Flujo de trabajo**

1. El usuario abre la regla.
2. El usuario ejecuta la opción de eliminar, si está disponible.
3. El sistema valida permisos.
4. El sistema elimina el registro.

## 8. Tipos de Ajuste

### 8.1 Listar tipos de ajuste

**Descripción**  
Permite que el usuario consulte los tipos de ajuste disponibles para clasificar prorrateos, motivos y reglas de cobro.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Tipos de ajustes.
2. El sistema muestra la lista ordenada por tipo por defecto y nombre.
3. El usuario identifica si el ajuste es activo, requiere motivo o habilita prorrateo.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre | Denominación del ajuste. |
| Por defecto | Marca el ajuste principal del sistema. |
| Requiere motivo | Obliga a capturar una justificación. |
| Habilita prorrateo | Activa el cálculo proporcional. |
| Color | Identificador visual para listas y badges. |
| Activo | Permite habilitar o deshabilitar el ajuste. |

### 8.2 Crear o editar un tipo de ajuste

**Descripción**  
Permite que el usuario registre un nuevo tipo de ajuste o modifique uno existente.

**Flujo de trabajo**

1. El usuario abre el formulario de tipos de ajuste.
2. El usuario define el nombre.
3. El usuario activa o desactiva las opciones de negocio.
4. El usuario selecciona el color visual.
5. El usuario guarda el registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre | Campo obligatorio. |
| Por defecto | Solo un registro puede mantener este valor. |
| Requiere motivo | Controla la obligación de justificar el ajuste. |
| Habilita prorrateo | Controla la habilitación del monto proporcional. |
| Color | Se usa en badges y listas. |

### 8.3 Eliminar un tipo de ajuste

**Descripción**  
Permite que el usuario elimine un tipo de ajuste cuando ya no tenga uso operativo.

**Flujo de trabajo**

1. El usuario abre el tipo de ajuste.
2. El usuario ejecuta eliminar, si corresponde.
3. El sistema valida permisos y dependencias.
4. El sistema elimina el registro.

## 9. Configurar Recibo

### 9.1 Editar la configuración del recibo

**Descripción**  
Permite que el usuario personalice el diseño y contenido visual del recibo de cobranza.

**Flujo de trabajo**

1. El usuario ingresa a Configuración > Configurar Recibo.
2. El sistema abre un único registro global de configuración.
3. El usuario ajusta datos de empresa, logo, firma, colores, tipografía y layout.
4. El sistema actualiza la vista previa en tiempo real.
5. El usuario guarda los cambios.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre empresa | Nombre mostrado en el recibo. |
| Dirección | Dirección corporativa. |
| Ciudad | Ciudad de emisión. |
| CEL empresa | Número de contacto de la empresa. |
| Email empresa | Correo corporativo. |
| NIT | Identificador tributario. |
| Slogan | Texto promocional opcional. |
| Logo | Imagen corporativa del recibo. |
| Usar logo imagen | Controla si se usa la imagen cargada. |
| Ancho del logo | Tamaño máximo en píxeles. |
| Nombre firmante | Firma principal. |
| Cargo | Cargo del firmante. |
| CEL firmante | Número de contacto del firmante. |
| Texto pie de página | Mensaje final del recibo. |
| Mostrar pie de página | Activa o desactiva el pie. |
| Colores | Definen el encabezado, fondo, texto y bordes. |
| Fuente del recibo | Familia tipográfica. |
| Tamaño fuente base | Tamaño general del documento. |
| Estilo del encabezado | Gradiente, sólido, línea o sin fondo. |
| Mostrar banda decorativa | Control visual del recibo. |
| Tabla de detalle | Textos de cabecera y columna de monto. |

### 9.2 Restaurar diseño por defecto

**Descripción**  
Permite que el usuario restablezca los valores visuales originales del recibo.

**Flujo de trabajo**

1. El usuario abre la configuración del recibo.
2. El usuario presiona Restaurar diseño por defecto.
3. El sistema devuelve los valores predeterminados.
4. El usuario confirma la acción si el sistema lo solicita.

## 10. Reportes y análisis

### 10.1 Planilla general

**Descripción**  
Permite que el usuario analice la planilla de cobros por período y estado.

**Uso**

- Lista detallada de pagos.
- Filtros por cliente, contrato, plan, ajuste, modalidad, estado y período.
- Agrupación por año, mes, estado, plan o ajuste.

### 10.2 Recaudación mensual

**Descripción**  
Permite que el usuario analice los montos realmente recaudados por mes y por plan.

**Uso**

- Vista gráfico de barras.
- Vista pivote por año, mes y plan.
- Métrica principal: monto pagado.

### 10.3 Deuda pendiente

**Descripción**  
Permite que el usuario analice la deuda pendiente por período y plan.

**Uso**

- Vista gráfico.
- Vista pivote.
- Métrica principal: monto a cobrar.

### 10.4 Deuda en mora

**Descripción**  
Permite que el usuario analice la deuda vencida y su evolución mensual.

**Uso**

- Vista gráfica.
- Vista pivote.
- Métrica principal: monto a cobrar de registros en mora.

### 10.5 Análisis de estado de pago

**Descripción**  
Permite que el usuario observe la distribución de registros pagados, pendientes y en mora.

**Uso**

- Gráfico de tipo pastel.
- Vista pivote de distribución.

### 10.6 Ingresos por plan

**Descripción**  
Permite que el usuario compare la recaudación por tipo de plan.

**Uso**

- Gráfico de barras.
- Vista pivote por plan.

### 10.7 Análisis por tipo de ajuste

**Descripción**  
Permite que el usuario observe la cantidad de registros agrupados por tipo de ajuste en cada período.

**Uso**

- Gráfico de barras apiladas.
- Vista pivote por año, mes y tipo de ajuste.

### 10.8 Reporte de incobrables

**Descripción**  
Permite que el usuario analice la cartera incobrable mediante lista, pivote y gráfico.

**Uso**

- Conteo y montos por estado.
- Agrupación por plan.
- Seguimiento de diferencias entre deuda y cobro.

## 11. Automatización y validaciones

### 11.1 Generación automática de cobros

**Descripción**  
El sistema puede generar cobros mensuales de manera automática según la regla de cobranza, el día configurado y la modalidad del contrato.

**Flujo de trabajo**

1. El cron del módulo evalúa las reglas activas.
2. El sistema busca contratos elegibles.
3. El sistema crea el cobro del mes cuando no existe un registro previo.
4. El sistema asigna el estado inicial definido en la regla.

### 11.2 Validaciones del cobro

**Descripción**  
El sistema controla que no existan duplicados por cliente, contrato, servicio y período.

**Reglas principales**

- El año debe contener cuatro dígitos numéricos.
- El período no puede duplicarse para la misma relación contractual.
- El cliente debe tener contrato activo.
- El tipo de ajuste puede exigir motivo o prorrateo.
- La edición contable sobre cobros confirmados requiere justificación.

### 11.3 Seguimiento de estado

**Descripción**  
El sistema actualiza estados y relaciones operativas según el cobro y sus documentos asociados.

**Comportamientos principales**

- Un pago confirmado puede activar el estado Pagado.
- Un pago parcial puede permanecer como Pendiente.
- El cobro puede pasar a Mora manualmente cuando cumple condiciones.
- El recibo y la factura se enlazan con el cobro origen.
- Un pago confirmado puede reactivar servicios FTTH suspendidos cuando aplique.

## 12. Consideraciones operativas

### 12.1 Vista de comprobantes

El sistema permite revisar uno o varios archivos adjuntos del pago. Cuando existen varios comprobantes, el usuario debe seleccionar el archivo a visualizar o descargar.

### 12.2 Relación con FTTH y contratos

El módulo se integra con contratos, clientes, servicios FTTH, CRM e indicadores de cobranza. Por esa razón, los cambios en un cobro pueden impactar en suspensiones, incobrables, facturación y registros comerciales relacionados.

### 12.3 Trazabilidad

El módulo utiliza el chatter para registrar confirmaciones, anulaciones, ediciones contables y cambios de estado relevantes, manteniendo trazabilidad operativa y contable.
