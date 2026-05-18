# Manual de Usuario — Módulo Contratos

Este manual describe, de forma operativa, las funciones disponibles en el módulo Contratos para la gestión de contratos de clientes ISP. Cada apartado presenta: descripción, flujo de trabajo y datos relevantes.

## 1. Introducción

### 1.1 Propósito

El documento sirve como guía de usuario para: registrar, validar, activar, modificar, cambiar plan, gestionar documentos y finalizar contratos.

### 1.2 Acceso y ubicación en el sistema

- Menú principal: Contratos
- Acción principal: Contratos de Clientes (vista lista con filtros y acceso al formulario)
- Acceso adicional desde la ficha del cliente: botón para ver contratos asociados

## 2. Resumen de vistas y controles

### 2.1 Vista formulario

#### Descripción

Formulario principal que agrupa la información del contrato en pestañas: General, Plan de Servicio, Facturación, Técnico, Documentos e Historial.

#### Controles principales

- Enviar a Pendiente — envía el contrato desde borrador al flujo de verificación.
- Subir / Validar Contrato — registra el contrato firmado y valida la documentación.
- Activar Servicio — activa el servicio cuando el contrato está registrado y la información técnica es completa.
- Cambiar Plan — abre un asistente para ejecutar el cambio de plan y generar el contrato sucesor.
- Ver contrato actualizado — permite acceder al contrato que reemplazó al actual.
- Terminar Contrato — finaliza el contrato activo y registra la fecha de terminación.

#### Condiciones de edición

- La mayoría de campos son editables solo en etapas iniciales del flujo (borrador, pendiente o registrado).
- Los campos de identificación personal o fiscal se muestran según el tipo de cliente (persona o empresa).
- La sección de documentos muestra vista previa de imagen o indicador de PDF según el tipo de archivo cargado.

### 2.2 Vista lista y búsqueda

#### Descripción

Listado de contratos con columnas clave (número, cliente, modalidad de pago, plan, tarifa y estado) y filtros predefinidos por estado, plan y cliente.

## 3. Gestión de contratos (operaciones principales)

### 3.1 Registrar un contrato

#### Descripción

Permite crear un contrato nuevo con datos del cliente, plan, fechas y documentos iniciales.

#### Flujo de trabajo

1. Abrir Contratos → Contratos de Clientes.
2. Crear nuevo registro.
3. Completar la información de cliente, plan, fechas e información de facturación si corresponde.
4. Adjuntar documento(s) del contrato si están disponibles.
5. Guardar el registro.
6. El sistema genera automáticamente el número de contrato si no se indicó uno manualmente.

#### Datos

| Campo                                    | Descripción                                                                       |
| ---------------------------------------- | --------------------------------------------------------------------------------- |
| Nº de Contrato                           | Código identificador del contrato (se genera automáticamente si no se introduce). |
| Cliente / Empresa                        | Titular del contrato.                                                             |
| Persona de contacto                      | Contacto interno o persona referente del cliente.                                 |
| Teléfono / Celular / Correo              | Datos de contacto del cliente.                                                    |
| Dirección                                | Dirección postal o de instalación.                                                |
| Documento (CI/NIT)                       | Identificación del cliente según tipo.                                            |
| Plan de Internet                         | Plan contratado (velocidad, tarifa).                                              |
| Fecha de contrato / Fecha de instalación | Fechas asociadas al inicio del servicio.                                          |
| Fecha de fin prevista                    | Fecha estimada de finalización del contrato.                                      |
| Modalidad de pago                        | Prepago o Postpago.                                                               |
| Archivos del contrato                    | Documentos adjuntos (PDF/JPG/PNG).                                                |

### 3.2 Editar un contrato

#### Descripción

Permite modificar la información del contrato mientras el flujo lo permita; los cambios pueden sincronizar ciertos datos con la ficha del cliente.

#### Flujo de trabajo

1. Abrir la lista de contratos.
2. Seleccionar y abrir el registro a editar.
3. Editar los campos permitidos según la etapa del contrato.
4. Guardar los cambios.
5. El sistema valida la información y sincroniza datos de contacto con la ficha del cliente cuando corresponde.

#### Datos

| Campo                | Descripción                                                                                      |
| -------------------- | ------------------------------------------------------------------------------------------------ |
| Datos del contrato   | Información general y de contacto que puede actualizarse.                                        |
| Datos de facturación | Nombre y teléfono del facturante; opciones para usar datos del cliente o de una tercera persona. |

### 3.3 Eliminar un contrato

#### Descripción

Permite eliminar contratos mediante la acción estándar del sistema, respetando permisos y dependencias.

#### Flujo de trabajo

1. Seleccionar registro en lista o formulario.
2. Ejecutar la acción de eliminación y confirmar.
3. El sistema verifica permisos y dependencias antes de suprimir el registro.

#### Datos

| Campo           | Descripción                                                              |
| --------------- | ------------------------------------------------------------------------ |
| Consideraciones | Verificar dependencias (facturas, recibos, historial) antes de eliminar. |

### 3.4 Listar y filtrar contratos

#### Descripción

Consultar el listado de contratos con opciones de filtrado y agrupación por estado, plan o cliente.

#### Flujo de trabajo

1. Abrir Contratos → Contratos de Clientes.
2. Aplicar filtros o agrupaciones según necesidad.
3. Seleccionar registro para revisar o editar.

#### Datos

| Campo                | Descripción                                                                |
| -------------------- | -------------------------------------------------------------------------- |
| Información mostrada | Nº de contrato, cliente, modalidad de pago, plan, tarifa, fechas y estado. |

### 3.5 Enviar a verificación (Enviar a Pendiente)

#### Descripción

Transición que valida campos mínimos y envía el contrato a etapa de verificación documental.

#### Flujo de trabajo

1. Con contrato en borrador, el usuario selecciona la acción "Enviar a Pendiente".
2. El sistema verifica campos esenciales (contacto, dirección, plan y fechas).
3. Si las validaciones son correctas, el contrato pasa a la etapa de verificación; de lo contrario se muestran errores.

#### Datos

| Campo                        | Descripción                                                         |
| ---------------------------- | ------------------------------------------------------------------- |
| Requeridos para verificación | Celular, dirección, plan, fecha de contrato y fecha de instalación. |

### 3.6 Registro del contrato firmado (Subir / Validar)

#### Descripción

Registro formal del contrato firmado. Comprende la validación de la documentación y los datos del facturante.

#### Flujo de trabajo

1. Con contrato en verificación, adjuntar archivo(s) del contrato si procede.
2. Ejecutar la acción de validación del contrato.
3. El sistema comprueba la existencia y el formato de al menos un documento, valida tamaño y datos de facturación; si todo es correcto, el contrato queda registrado.

#### Datos

| Campo                | Descripción                                              |
| -------------------- | -------------------------------------------------------- |
| Documentos           | Archivo principal o adjuntos en PDF/JPG/PNG (máx. 5 MB). |
| Datos del facturante | Nombre, teléfono y documento del responsable de pago.    |

### 3.7 Activación del servicio

#### Descripción

Permite activar el servicio asociado al contrato tras verificar la documentación y completar datos técnicos de ubicación.

#### Flujo de trabajo

1. Con contrato registrado, completar enlace de ubicación y coordenadas si faltan.
2. Ejecutar la acción de activación.
3. El sistema valida los datos técnicos y cambia el estado del contrato a activo.

#### Datos

| Campo     | Descripción                                                      |
| --------- | ---------------------------------------------------------------- |
| Ubicación | Enlace de ubicación y coordenadas GPS (requeridos para activar). |

### 3.8 Finalizar contrato

#### Descripción

Procedimiento para dar por finalizado un contrato activo, registrando la fecha de terminación.

#### Flujo de trabajo

1. Abrir contrato en estado activo.
2. Ejecutar la acción "Terminar contrato" y confirmar.
3. El sistema registra la fecha de terminación (si no existía) y marca el contrato como finalizado.

#### Datos

| Campo                | Descripción                                   |
| -------------------- | --------------------------------------------- |
| Fecha de terminación | Fecha en la que el contrato queda finalizado. |

### 3.9 Cambio de plan (asistente)

#### Descripción

Asistente que permite realizar un cambio de plan desde un contrato activo. El proceso finaliza creando un nuevo contrato activo y marcando el original como reemplazado.

#### Flujo de trabajo

1. Abrir contrato activo y seleccionar "Cambiar plan".
2. En el asistente, seleccionar el nuevo plan, indicar motivo y adjuntar documentos si procede.
3. Confirmar la operación.
4. El sistema valida que el plan sea distinto y activo, finaliza el contrato actual, crea un nuevo contrato con el plan seleccionado y enlaza ambos registros como historial.

#### Datos

| Campo                         | Descripción                                      |
| ----------------------------- | ------------------------------------------------ |
| Nuevo plan                    | Plan que sustituye al anterior.                  |
| Motivo                        | Justificación operativa del cambio.              |
| Documentos del nuevo contrato | Archivos adjuntos que acompañan la modificación. |

### 3.10 Ver y descargar documentos del contrato

#### Descripción

Acciones para previsualizar o descargar los documentos asociados a un contrato. Si existen varios archivos, el sistema solicita seleccionar uno.

#### Flujo de trabajo

1. Abrir la pestaña Documentos del contrato.
2. Seleccionar Ver en grande o Descargar.
3. Si existen múltiples archivos, elegir el documento deseado y proceder a ver o descargar.

#### Datos

| Campo                | Descripción                                |
| -------------------- | ------------------------------------------ |
| Documentos asociados | Archivos adjuntos al contrato (histórico). |

### 3.11 Acceso desde la ficha del cliente

#### Descripción

Desde la ficha del cliente se accede a un resumen de contratos activos y a la lista completa de contratos asociados.

#### Flujo de trabajo

1. Abrir la ficha del cliente.
2. Pulsar el botón que muestra la cantidad de contratos para abrir la vista filtrada.
3. Si existe un único contrato, el sistema abre directamente el formulario correspondiente.

#### Datos

| Campo                   | Descripción                                                      |
| ----------------------- | ---------------------------------------------------------------- |
| Contadores de contratos | Indicadores de contratos activos y totales asociados al cliente. |

## 4. Validaciones y reglas de negocio

- El flujo de estados (borrador → verificación → registrado → activo → finalizado) exige validaciones específicas en cada transición.
- Se valida la consistencia de fechas (la fecha de instalación no puede ser anterior a la fecha de contrato).
- Los documentos deben ser PDF, JPG o PNG y no superar 5 MB.
- El número de contrato debe ser único entre los contratos vigentes; el sistema genera un número estándar cuando no se especifica.

## 5. Consideraciones operativas y técnicas

- El cambio de plan crea un contrato sucesor y registra el motivo en el contrato original.
- La sincronización de datos de contacto hacia la ficha del cliente se realiza de forma automática salvo que se desactive explícitamente por contexto operativo.
- Verificar dependencias contables y documentales antes de eliminar contratos.

## 6. Anexo — Resumen de datos relevantes

| Elemento                    | Descripción                                             |
| --------------------------- | ------------------------------------------------------- |
| Nº de Contrato              | Identificador del contrato.                             |
| Cliente / Empresa           | Titular del contrato.                                   |
| Persona de contacto         | Referente dentro del cliente.                           |
| Datos de contacto           | Teléfono, celular y correo.                             |
| Dirección                   | Dirección de instalación o facturación.                 |
| Documento de identificación | CI o NIT según el tipo de cliente.                      |
| Plan contratado             | Plan de internet con velocidad y tarifa.                |
| Modalidad de pago           | Prepago o Postpago.                                     |
| Fechas                      | Fecha de contrato, instalación, fin y terminación.      |
| Datos de facturación        | Nombre y teléfono del facturante; opción de tercero.    |
| Documentos                  | Archivos adjuntos del contrato (PDF/JPG/PNG).           |
| Estado operativo            | Borrador, Verificación, Registrado, Activo, Finalizado. |

---

Fin del manual.
