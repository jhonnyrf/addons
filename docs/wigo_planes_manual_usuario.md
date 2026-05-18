# Manual de Usuario

## Módulo Wigo Planes

### 1. Introducción

El módulo Wigo Planes centraliza la administración de planes de Internet, costos de instalación y promociones comerciales asociadas al programa de referidos. Su propósito es permitir el registro, seguimiento y control operativo de la oferta comercial dentro de Odoo, con trazabilidad de estados, métricas y validaciones automáticas.

### 1.1 Listar Planes de Internet

**Descripción**  
Permite que el usuario consulte el catálogo de planes de Internet registrados en el sistema, visualizándolos en formato kanban, lista o formulario.

**Flujo de trabajo**

1. El usuario ingresa al módulo Wigo Planes.
2. El usuario selecciona el menú Planes de Internet.
3. El sistema muestra el listado de planes registrados.
4. El usuario puede alternar entre las vistas kanban, lista y formulario.
5. El usuario identifica el plan por su nombre, identificador, velocidad y tarifa mensual.
6. El sistema muestra el estado activo o archivado del registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Identificador | Código único del plan. |
| Nombre del plan | Denominación comercial del plan. |
| Tipo | Tipo de conexión disponible para el plan. |
| Velocidad | Velocidad principal del servicio en Mbps. |
| Velocidad DOWN | Velocidad de descarga en Mbps. |
| Velocidad UP | Velocidad de subida en Mbps. |
| Tarifa mensual | Precio mensual del plan en bolivianos. |
| Activo | Indica si el plan se encuentra habilitado para uso comercial. |

### 1.2 Registrar Plan de Internet

**Descripción**  
Permite que el usuario cree un nuevo plan de Internet, definiendo su identificación comercial, velocidades, tarifa mensual y descripción general.

**Flujo de trabajo**

1. El usuario ingresa al módulo Wigo Planes.
2. El usuario selecciona el menú Planes de Internet.
3. El usuario presiona la acción de crear un nuevo registro.
4. El sistema muestra el formulario de plan.
5. El usuario completa los campos obligatorios.
6. El usuario define la velocidad del plan y la tarifa mensual.
7. El usuario registra una descripción opcional.
8. El usuario presiona Guardar.
9. El sistema almacena el registro y mantiene el plan activo por defecto.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre del plan | Nombre comercial del servicio. |
| Identificador | Código interno único del plan. |
| Tipo de conexión | Clasificación del plan. En la solución actual se utiliza Fibra óptica. |
| Velocidad | Velocidad principal en Mbps. |
| Velocidad DOWN | Velocidad de descarga en Mbps. |
| Velocidad UP | Velocidad de subida en Mbps. |
| Tarifa mensual | Costo mensual del servicio. |
| Descripción | Texto descriptivo del plan. |
| Activo | Indica si el plan queda disponible para su uso. |

### 1.3 Editar Plan de Internet

**Descripción**  
Permite que el usuario modifique la información de un plan de Internet registrado, actualizando sus velocidades, tarifa, descripción o estado.

**Flujo de trabajo**

1. El usuario ingresa al módulo Wigo Planes.
2. El usuario selecciona el menú Planes de Internet.
3. El sistema muestra el listado de planes registrados.
4. El usuario selecciona el plan que desea editar.
5. El sistema muestra el formulario con la información registrada.
6. El usuario modifica los campos necesarios.
7. El usuario presiona Guardar.
8. El sistema actualiza la información del plan.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre del plan | Nombre comercial del servicio. |
| Identificador | Código interno único del plan. |
| Velocidad | Velocidad principal en Mbps. |
| Velocidad DOWN | Velocidad de descarga en Mbps. |
| Velocidad UP | Velocidad de subida en Mbps. |
| Tarifa mensual | Costo mensual del servicio. |
| Descripción | Información complementaria del plan. |
| Activo | Indica si el plan se encuentra disponible. |

### 1.4 Archivar o reactivar Plan de Internet

**Descripción**  
Permite que el usuario archive un plan de Internet para retirarlo de la operación comercial o lo reactive cuando vuelva a estar disponible.

**Flujo de trabajo**

1. El usuario ingresa al formulario del plan.
2. El usuario utiliza el interruptor de estado ubicado en el encabezado.
3. El sistema marca el registro como archivado o activo.
4. El sistema muestra una cinta visual cuando el plan está archivado.
5. El usuario guarda los cambios.

**Datos**  
| Campo | Descripción |
|---|---|
| Activo | Controla la disponibilidad comercial del plan. |
| Cinta de estado | Indica visualmente si el plan está archivado. |

### 1.5 Eliminar Plan de Internet

**Descripción**  
Permite que el usuario elimine un plan de Internet que ya no sea necesario en el catálogo comercial, siempre que el registro no tenga restricciones operativas en el sistema.

**Flujo de trabajo**

1. El usuario ingresa al listado de planes.
2. El usuario selecciona el plan que desea eliminar.
3. El sistema abre el formulario del registro.
4. El usuario ejecuta la acción de eliminar disponible en Odoo.
5. El sistema solicita confirmación, si corresponde.
6. El usuario confirma la eliminación.
7. El sistema elimina el registro del catálogo.

**Datos**  
| Campo | Descripción |
|---|---|
| Identificador | Código único del plan eliminado. |
| Nombre del plan | Nombre comercial del registro eliminado. |
| Activo | El registro deja de estar disponible en el sistema. |

### 1.6 Listar Costos de Instalación

**Descripción**  
Permite que el usuario consulte los costos de instalación registrados para los planes de Internet.

**Flujo de trabajo**

1. El usuario ingresa al módulo Wigo Planes.
2. El usuario selecciona el menú Costos de Instalación.
3. El sistema muestra el listado de costos registrados.
4. El usuario identifica el concepto de instalación, el monto y el estado del registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre del costo de instalación | Denominación del concepto de cobro. |
| Costo de instalación | Valor monetario del servicio de instalación. |
| Activo | Indica si el costo está habilitado. |
| Descripción | Notas adicionales del costo. |

### 1.7 Registrar Costo de Instalación

**Descripción**  
Permite que el usuario cree un costo de instalación, definiendo su nombre, importe y descripción asociada.

**Flujo de trabajo**

1. El usuario ingresa al módulo Wigo Planes.
2. El usuario selecciona el menú Costos de Instalación.
3. El usuario presiona la acción de crear un nuevo registro.
4. El sistema muestra el formulario correspondiente.
5. El usuario completa el nombre y el importe de instalación.
6. El usuario agrega una descripción opcional.
7. El usuario presiona Guardar.
8. El sistema almacena el registro con estado activo por defecto.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre del costo de instalación | Identificación del concepto. |
| Costo de instalación | Monto cobrado por la instalación. |
| Descripción | Texto explicativo del cargo. |
| Activo | Estado operativo del costo. |

### 1.8 Editar Costo de Instalación

**Descripción**  
Permite que el usuario modifique la información de un costo de instalación ya registrado.

**Flujo de trabajo**

1. El usuario ingresa al menú Costos de Instalación.
2. El sistema muestra el listado correspondiente.
3. El usuario selecciona el costo que desea actualizar.
4. El sistema abre el formulario del registro.
5. El usuario modifica los datos necesarios.
6. El usuario presiona Guardar.
7. El sistema actualiza el costo de instalación.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre del costo de instalación | Denominación del concepto. |
| Costo de instalación | Importe monetario del cargo. |
| Descripción | Detalle adicional del registro. |
| Activo | Estado de disponibilidad. |

### 1.9 Archivar o reactivar Costo de Instalación

**Descripción**  
Permite que el usuario archive un costo de instalación o lo reactive desde el encabezado del formulario.

**Flujo de trabajo**

1. El usuario abre el formulario del costo de instalación.
2. El usuario utiliza el interruptor de estado del encabezado.
3. El sistema cambia el estado del registro.
4. El sistema muestra la cinta visual de archivado cuando corresponde.
5. El usuario guarda la operación.

**Datos**  
| Campo | Descripción |
|---|---|
| Activo | Controla si el costo está disponible para uso operativo. |
| Cinta de estado | Señala que el registro se encuentra archivado. |

### 1.10 Eliminar Costo de Instalación

**Descripción**  
Permite que el usuario elimine un costo de instalación que ya no debe ser utilizado en la operación.

**Flujo de trabajo**

1. El usuario ingresa al listado de costos de instalación.
2. El usuario selecciona el registro que desea eliminar.
3. El sistema abre el formulario del costo.
4. El usuario ejecuta la acción de eliminar.
5. El sistema solicita confirmación, si corresponde.
6. El usuario confirma la eliminación.
7. El sistema suprime el registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre del costo de instalación | Concepto eliminado. |
| Costo de instalación | Valor asociado al registro eliminado. |
| Activo | El costo deja de estar disponible. |

### 1.11 Listar Promociones

**Descripción**  
Permite que el usuario consulte las promociones comerciales registradas, visualizándolas en formato kanban, lista o formulario.

**Flujo de trabajo**

1. El usuario ingresa al módulo Wigo Planes.
2. El usuario selecciona el menú Promociones.
3. El sistema muestra el tablero kanban de promociones.
4. El usuario puede cambiar a vista de lista o formulario.
5. El sistema presenta información resumida como tipo, vigencia, plan asociado, recompensas y estado activo.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre de la promoción | Identificación comercial de la campaña. |
| Tipo | Mecánica de la promoción: referidos, descuento, mes gratis o personalizado. |
| Fecha inicio | Inicio de la vigencia. |
| Fecha fin | Fin de la vigencia. |
| Plan aplicable | Plan al que se limita la promoción, si corresponde. |
| Recompensas | Cantidad de recompensas registradas. |
| Referidos | Cantidad de referidos asociados cuando aplica. |
| Activo | Indica si la promoción se encuentra habilitada. |

### 1.12 Registrar Promoción

**Descripción**  
Permite que el usuario cree una promoción comercial definiendo su nombre, tipo, vigencia, alcance y configuración de beneficio.

**Flujo de trabajo**

1. El usuario ingresa al menú Promociones.
2. El usuario selecciona crear un nuevo registro.
3. El sistema abre el formulario de promoción.
4. El usuario completa la información general.
5. El usuario define la vigencia de la promoción.
6. El usuario configura el beneficio según el tipo seleccionado.
7. El usuario registra una descripción de condiciones.
8. El usuario presiona Guardar.
9. El sistema almacena la promoción.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre de la promoción | Nombre comercial de la campaña. |
| Tipo | Define la lógica de la promoción. |
| Activo | Habilita o deshabilita la promoción. |
| Plan aplicable | Limita la promoción a un plan específico. |
| Fecha inicio | Fecha desde la cual se encuentra vigente. |
| Fecha fin | Fecha hasta la cual permanece vigente. |
| Referidos requeridos | Cantidad mínima de referidos válidos para promociones de tipo referido. |
| Recompensa del referido | Define si la recompensa será mes gratis o descuento. |
| Descuento (%) | Porcentaje de descuento aplicable. |
| Meses gratis | Cantidad de meses bonificados. |
| Beneficio personalizado | Texto libre para promociones personalizadas. |
| Descripción / Condiciones | Información complementaria de la campaña. |

### 1.13 Editar Promoción

**Descripción**  
Permite que el usuario actualice una promoción existente, modificando su vigencia, tipo, plan asociado, condiciones o configuración del beneficio.

**Flujo de trabajo**

1. El usuario ingresa al menú Promociones.
2. El sistema muestra el listado o tablero de promociones.
3. El usuario selecciona la promoción que desea editar.
4. El sistema abre el formulario del registro.
5. El usuario modifica los campos permitidos.
6. El usuario presiona Guardar.
7. El sistema actualiza la promoción.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre de la promoción | Denominación de la campaña. |
| Tipo | Clasificación de la promoción. |
| Activo | Estado operativo de la promoción. |
| Plan aplicable | Plan objetivo, si existe. |
| Fecha inicio | Vigencia inicial. |
| Fecha fin | Vigencia final. |
| Configuración de referidos | Parámetros del programa de referidos. |
| Configuración de descuento | Parámetros del descuento comercial. |
| Configuración de mes gratis | Parámetros de bonificación por tiempo. |
| Configuración personalizada | Campo libre para beneficios especiales. |
| Descripción / Condiciones | Observaciones de la promoción. |

### 1.14 Archivar o reactivar Promoción

**Descripción**  
Permite que el usuario archive una promoción para retirarla de la operación comercial o la reactive cuando deba volver a utilizarse.

**Flujo de trabajo**

1. El usuario abre el formulario de la promoción.
2. El usuario cambia el estado desde el campo Activo.
3. El sistema actualiza el estado del registro.
4. El sistema muestra una cinta visual cuando la promoción se encuentra archivada.
5. El usuario guarda los cambios.

**Datos**  
| Campo | Descripción |
|---|---|
| Activo | Define si la promoción está disponible. |
| Cinta de archivado | Identificación visual del estado inactivo. |

### 1.15 Eliminar Promoción

**Descripción**  
Permite que el usuario elimine una promoción que ya no deba mantenerse en el sistema.

**Flujo de trabajo**

1. El usuario ingresa al listado de promociones.
2. El usuario selecciona la promoción que desea eliminar.
3. El sistema abre el formulario del registro.
4. El usuario ejecuta la acción de eliminar.
5. El sistema solicita confirmación, si corresponde.
6. El usuario confirma la eliminación.
7. El sistema elimina la promoción.

**Datos**  
| Campo | Descripción |
|---|---|
| Nombre de la promoción | Promoción eliminada. |
| Tipo | Tipo de promoción eliminado. |
| Activo | La promoción deja de estar disponible. |

### 1.16 Consultar estadísticas de la Promoción

**Descripción**  
Permite que el usuario visualice indicadores resumidos de la promoción mediante botones estadísticos ubicados en el formulario.

**Flujo de trabajo**

1. El usuario abre una promoción.
2. El sistema muestra los botones estadísticos en la parte superior.
3. El usuario selecciona Recompensas para ver los registros asociados.
4. Si la promoción es de tipo referido, el usuario también puede consultar Referidos.
5. El sistema abre las vistas filtradas correspondientes.

**Datos**  
| Campo | Descripción |
|---|---|
| Recompensas | Total de recompensas registradas para la promoción. |
| Referidos | Total de referidos asociados, visible solo para promociones de tipo referido. |

### 1.17 Listar Referidos

**Descripción**  
Permite que el usuario consulte los referidos registrados dentro de una promoción, con opción de búsqueda, filtrado, agrupación y visualización por lista o formulario.

**Flujo de trabajo**

1. El usuario ingresa al módulo Wigo Planes.
2. El usuario selecciona el menú Referidos.
3. El sistema muestra el listado de referidos.
4. El usuario puede buscar por cliente referente, cliente referido o promoción.
5. El usuario puede filtrar por estado o agrupar la información.
6. El usuario abre el registro para revisar su detalle.

**Datos**  
| Campo | Descripción |
|---|---|
| Fecha | Fecha de registro del referido. |
| Cliente referente | Cliente que recomienda. |
| Cliente referido | Cliente invitado o referido. |
| Promoción | Promoción asociada al referido. |
| Estado | Estado operativo del referido. |
| Fecha de validación | Fecha en que el referido fue validado. |
| Listo desde | Fecha en la que quedó habilitado para recompensa. |
| Fecha recompensa | Fecha en la que se entregó la recompensa. |
| Notas | Observaciones adicionales. |

### 1.18 Registrar Referido

**Descripción**  
Permite que el usuario registre manualmente un referido asociado a una promoción activa de tipo referido.

**Flujo de trabajo**

1. El usuario ingresa al menú Referidos.
2. El usuario selecciona crear un nuevo registro.
3. El sistema abre el formulario del referido.
4. El usuario selecciona la promoción correspondiente.
5. El usuario indica el cliente referente y el cliente referido.
6. El usuario completa la fecha y las notas, si corresponde.
7. El usuario presiona Guardar.
8. El sistema guarda el referido en estado Pendiente.

**Datos**  
| Campo | Descripción |
|---|---|
| Promoción | Promoción que controla el programa de referidos. |
| Cliente referente | Cliente que origina el referido. |
| Cliente referido | Cliente captado mediante la recomendación. |
| Fecha | Fecha de registro del referido. |
| Notas | Observaciones complementarias. |
| Estado | Se establece inicialmente como Pendiente. |

### 1.19 Editar Referido

**Descripción**  
Permite que el usuario modifique un referido mientras permanece en estado Pendiente.

**Flujo de trabajo**

1. El usuario ingresa al listado de referidos.
2. El usuario selecciona el registro requerido.
3. El sistema abre el formulario del referido.
4. El usuario modifica los campos permitidos.
5. El usuario presiona Guardar.
6. El sistema actualiza el registro.

**Datos**  
| Campo | Descripción |
|---|---|
| Promoción | Promoción asociada al registro. |
| Cliente referente | Cliente que recomienda. |
| Cliente referido | Cliente recomendado. |
| Fecha | Fecha de captura del referido. |
| Notas | Comentarios adicionales. |
| Estado | Permite la edición únicamente cuando el estado es Pendiente. |

### 1.20 Validar Referido

**Descripción**  
Permite que el usuario valide un referido para confirmar que cumple con las condiciones operativas del programa.

**Flujo de trabajo**

1. El usuario abre un referido en estado Pendiente.
2. El usuario presiona el botón Validar.
3. El sistema cambia el estado a Válido.
4. El sistema registra la fecha de validación.
5. El sistema verifica automáticamente si el cliente alcanzó el umbral de referidos requeridos.
6. Si se cumple el umbral, el sistema cambia los referidos válidos a Listo para recompensa.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado | Debe ser Pendiente para ejecutar la validación. |
| Fecha de validación | Se registra automáticamente al validar. |
| Referidos requeridos | Umbral configurado en la promoción. |

### 1.21 Marcar referidos como listos para recompensa

**Descripción**  
Permite que el sistema identifique automáticamente los referidos válidos que alcanzaron el mínimo exigido por la promoción y los coloque en estado Listo para recompensa.

**Flujo de trabajo**

1. El usuario valida los referidos correspondientes.
2. El sistema evalúa el total de referidos válidos por cliente y promoción.
3. Cuando se cumple el umbral, el sistema actualiza el estado a Listo para recompensa.
4. El sistema registra la fecha de disponibilidad para recompensa.
5. El sistema notifica al cliente referente mediante el chatter.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado | Cambia de Válido a Listo para recompensa. |
| Listo desde | Fecha automática de disponibilidad. |
| Notificación | Mensaje automático al cliente referente. |

### 1.22 Entregar recompensa de referidos

**Descripción**  
Permite que el usuario entregue la recompensa asociada a un grupo de referidos listos para recompensa. El sistema genera la recompensa y actualiza los referidos como Recompensados.

**Flujo de trabajo**

1. El usuario accede a un referido en estado Listo para recompensa.
2. El usuario presiona el botón Dar Recompensa.
3. El sistema identifica todos los referidos listos del mismo cliente referente y promoción.
4. El sistema crea el registro de recompensa correspondiente.
5. El sistema marca los referidos como Recompensados.
6. El sistema registra la fecha de recompensa.
7. El sistema publica una notificación en el chatter del cliente referente.

**Datos**  
| Campo | Descripción |
|---|---|
| Promoción | Promoción que origina la recompensa. |
| Cliente | Cliente que recibe el beneficio. |
| Tipo de recompensa | Mes gratis, descuento o personalizado, según la configuración. |
| Descuento (%) | Valor usado cuando la recompensa es de tipo descuento. |
| Meses gratis | Valor usado cuando la recompensa es de tipo mes gratis. |
| Notas | Texto generado automáticamente con el detalle del proceso. |
| Estado del referido | Cambia a Recompensado. |
| Fecha recompensa | Fecha en que se ejecuta la entrega. |

### 1.23 Cancelar o reactivar Referido

**Descripción**  
Permite que el usuario cancele un referido que no debe continuar en el flujo o lo reactive cuando sea necesario retornar el proceso a estado Pendiente.

**Flujo de trabajo**

1. El usuario abre el registro del referido.
2. El usuario presiona Cancelar cuando el registro aún no ha sido recompensado.
3. El sistema cambia el estado a Cancelado.
4. Si el registro fue cancelado, el usuario puede presionar Reactivar.
5. El sistema devuelve el estado a Pendiente.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado | Controla el ciclo de vida del referido. |
| Cancelar | No se permite sobre registros Recompensados. |
| Reactivar | Solo disponible cuando el estado es Cancelado. |

### 1.24 Listar Recompensas

**Descripción**  
Permite que el usuario consulte las recompensas generadas en el programa de promociones, con visibilidad del tipo de beneficio, el estado y el plan asociado cuando exista.

**Flujo de trabajo**

1. El usuario ingresa al módulo Wigo Planes.
2. El usuario selecciona el menú Recompensas Entregadas.
3. El sistema muestra el listado de recompensas registradas.
4. El usuario identifica el beneficio, la promoción y el estado del registro.
5. El usuario puede abrir el formulario para revisar el detalle.

**Datos**  
| Campo | Descripción |
|---|---|
| Fecha | Fecha de registro de la recompensa. |
| Cliente | Cliente beneficiario. |
| Promoción | Promoción vinculada al beneficio. |
| Tipo de recompensa | Categoría del beneficio entregado. |
| Descuento (%) | Se utiliza cuando la recompensa es monetaria. |
| Meses gratis | Se utiliza cuando la recompensa corresponde a bonificación de tiempo. |
| Plan | Plan sobre el que aplica la recompensa, si corresponde. |
| Estado | Pendiente, Aplicada o Cancelada. |
| Fecha de aplicación | Fecha en que se marca como aplicada. |
| Notas | Observaciones adicionales. |

### 1.25 Registrar Recompensa

**Descripción**  
Permite que el usuario cree manualmente una recompensa cuando sea necesario, aunque el flujo principal del módulo la genera automáticamente desde el proceso de referidos.

**Flujo de trabajo**

1. El usuario ingresa al menú Recompensas Entregadas.
2. El usuario selecciona crear un nuevo registro.
3. El sistema muestra el formulario de recompensa.
4. El usuario selecciona la promoción y el cliente.
5. El usuario define el tipo de recompensa y sus parámetros.
6. El usuario registra la fecha y las notas correspondientes.
7. El usuario presiona Guardar.
8. El sistema almacena la recompensa en estado Pendiente.

**Datos**  
| Campo | Descripción |
|---|---|
| Promoción | Promoción que origina la recompensa. |
| Cliente | Beneficiario del incentivo. |
| Plan | Plan asociado, si aplica. |
| Tipo de recompensa | Clase del beneficio otorgado. |
| Descuento (%) | Porcentaje de descuento aplicado. |
| Meses gratis | Cantidad de meses bonificados. |
| Detalle del beneficio | Descripción libre del beneficio personalizado. |
| Fecha | Fecha de registro. |
| Fecha de aplicación | Se completa cuando la recompensa se marca como aplicada. |
| Notas | Observaciones del registro. |

### 1.26 Editar Recompensa

**Descripción**  
Permite que el usuario actualice una recompensa registrada mientras su estado lo permita.

**Flujo de trabajo**

1. El usuario abre el listado de recompensas.
2. El usuario selecciona el registro a modificar.
3. El sistema muestra el formulario correspondiente.
4. El usuario ajusta los campos permitidos.
5. El usuario presiona Guardar.
6. El sistema actualiza la información.

**Datos**  
| Campo | Descripción |
|---|---|
| Promoción | Promoción relacionada. |
| Cliente | Cliente beneficiario. |
| Plan | Plan asociado, si aplica. |
| Tipo de recompensa | Tipo del beneficio. |
| Descuento (%) | Valor porcentual de descuento. |
| Meses gratis | Número de meses bonificados. |
| Detalle del beneficio | Descripción del incentivo personalizado. |
| Fecha | Fecha de registro. |
| Notas | Observaciones complementarias. |
| Estado | Define si la recompensa está Pendiente, Aplicada o Cancelada. |

### 1.27 Marcar Recompensa como aplicada

**Descripción**  
Permite que el usuario confirme que la recompensa fue aplicada al cliente.

**Flujo de trabajo**

1. El usuario abre una recompensa en estado Pendiente.
2. El usuario presiona Marcar como aplicada.
3. El sistema cambia el estado a Aplicada.
4. El sistema registra la fecha de aplicación.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado | Solo puede aplicarse si la recompensa está Pendiente. |
| Fecha de aplicación | Se completa automáticamente al ejecutar la acción. |

### 1.28 Cancelar Recompensa

**Descripción**  
Permite que el usuario cancele una recompensa que aún no fue aplicada.

**Flujo de trabajo**

1. El usuario abre una recompensa en estado Pendiente.
2. El usuario presiona Cancelar.
3. El sistema cambia el estado a Cancelada.
4. El sistema impide cancelar recompensas ya aplicadas.

**Datos**  
| Campo | Descripción |
|---|---|
| Estado | Controla el ciclo de vida de la recompensa. |
| Cancelar | No se permite cuando el estado es Aplicada. |

### 1.29 Verificación automática diaria de referidos

**Descripción**  
Permite que el sistema revise diariamente los referidos válidos para identificar promociones que ya alcanzaron el umbral de recompensa.

**Flujo de trabajo**

1. El sistema ejecuta la tarea programada de forma automática.
2. El sistema revisa las promociones activas de tipo referido.
3. El sistema agrupa los referidos válidos por cliente referente.
4. Si se alcanza el mínimo requerido, el sistema actualiza el estado de los referidos.
5. El sistema notifica al cliente referente.

**Datos**  
| Campo | Descripción |
|---|---|
| Promoción activa | Promoción de tipo referido vigente. |
| Referidos válidos | Referidos que cumplen las reglas del programa. |
| Umbral requerido | Cantidad mínima definida en la promoción. |
| Estado objetivo | Listo para recompensa. |

### 1.30 Validaciones del sistema

**Descripción**  
El módulo incorpora validaciones automáticas para garantizar la consistencia de los datos comerciales y operativos.

**Flujo de trabajo**

1. El usuario intenta guardar un registro con datos inválidos.
2. El sistema evalúa las reglas definidas en el modelo.
3. Si la información no cumple las condiciones, el sistema detiene la operación.
4. El sistema muestra el mensaje de validación correspondiente.

**Datos**  
| Campo | Descripción |
|---|---|
| Velocidad | Debe ser mayor que 0. |
| Velocidad DOWN | Debe ser mayor que 0. |
| Velocidad UP | Debe ser mayor que 0. |
| Precio | Debe ser mayor que 0 y menor o igual a 10 000 Bs. |
| Nombre del plan | Debe tener al menos 3 caracteres. |
| Identificador | Debe ser único para cada plan. |
| Referidos requeridos | Debe ser al menos 1 en promociones de tipo referido. |
| Descuento (%) | Debe estar entre 0.01 % y 100 %. |
| Fecha fin | No puede ser anterior a la fecha de inicio. |
| Auto-referido | Un cliente no puede referirse a sí mismo. |
| Referido duplicado | No se permite registrar el mismo cliente referido en un flujo vigente. |
| Recompensa aplicada | No se puede cancelar una recompensa ya aplicada. |
| Referido recompensado | No se puede cancelar un referido ya recompensado. |

### 1.31 Observaciones funcionales

**Descripción**  
El módulo utiliza mensajes automáticos en el chatter, indicadores visuales de estado, filtros de búsqueda y botones estadísticos para facilitar el seguimiento operativo.

**Flujo de trabajo**

1. El usuario consulta un registro desde su formulario.
2. El sistema presenta información contextual en el chatter.
3. El sistema resalta estados mediante badges, ribbons y decoraciones visuales.
4. El usuario navega entre listas, formularios y kanban según la necesidad operativa.

**Datos**  
| Campo | Descripción |
|---|---|
| Chatter | Registro de notificaciones y seguimiento interno. |
| Badge de estado | Representación visual del estado del registro. |
| Ribbon | Indicador de archivado en el formulario. |
| Filtros | Permiten segmentar referidos por estado o agrupación. |
| Botones estadísticos | Accesos rápidos a recompensas y referidos vinculados. |

### 2. Consideraciones finales

Este manual describe las funcionalidades expuestas por los modelos y vistas del módulo Wigo Planes. La documentación refleja el comportamiento funcional disponible en la solución Odoo, incluyendo operaciones de registro, edición, consulta, archivado, validación, automatización y control de estados.
