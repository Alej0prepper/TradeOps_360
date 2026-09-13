# Primera fase: contrato funcional y de seguridad

## Resultado y límites

El operador prepara una importación; el responsable la revisa y autoriza. Compras e Inventario de Odoo registran la mercancía físicamente. Una preventa confirmada puede convertirse en presupuesto cuando la importación está completamente recibida. Ventas e Inventario gestionan la venta y sus entregas; TradeOps aporta seguimiento, incidencias y conciliación comercial.

Cada operación pertenece a una compañía y utiliza su moneda. El almacén es una relación explícita de esa compañía. Los puertos son un catálogo global; los contactos y productos siguen las reglas estándar de Odoo. El código de puerto se normaliza y es único. `res.partner.trade_code` es una referencia opcional, no una clave única de clientes.

Se permiten cantidades positivas finitas y precios no negativos finitos. Los gastos no pueden ser negativos. Un precio cero es admisible, pero **gastos positivos con compra total cero se rechazan**. Los productos de una importación enviada a revisión deben ser almacenables y activos; proveedor y puertos deben ser válidos y activos.

## Estados, acciones y consecuencias

| Documento | Acción / rol | Regla y efecto |
| --- | --- | --- |
| Importación | Submit for Review / operador | Draft → Document Review; exige proveedor, almacén, productos y datos coherentes; congela edición ordinaria. |
| Importación | Return to Draft / responsable | Solo desde Document Review y sin compra asociada. |
| Importación | Validate / Create RFQ / responsable | Document Review → Validated; crea una solicitud de presupuesto de compra con correspondencia exacta de líneas. No recibe stock. |
| Importación | Confirm Purchase / In Transit / responsable | Confirma la compra estándar y pasa a In Transit. |
| Importación | Receive Goods / operador | Abre recepciones estándar; el primer acceso puede pasar a Receiving. |
| Importación | Recepción física / Inventario | Partially Received mientras falte mercancía; Completed solo cuando todas las líneas tienen recepción suficiente. Una reserva o recepción cancelada no cuenta. |
| Importación | Cancel / responsable | No permite cancelar después de movimientos físicos terminados. Antes, requiere cancelar las preventas y cancela la compra vinculada. |
| Preventa | Confirm Commitment / operador | Draft → Confirmed; exige líneas, importación validada y no cancelada y lista de precios en moneda de compañía. No reserva stock. |
| Preventa | Return to Draft / responsable | Confirmed → Draft, sin venta vinculada. |
| Preventa | Cancel / operador | Desde Draft o Confirmed; libera compromiso. Una convertida conserva su origen y se cancela desde Ventas. |
| Preventa | Create Quotation / operador | Importación Completed y preventa Confirmed; crea presupuesto una sola vez, conserva vínculos y pasa a Converted. |
| Distribución | Start Distribution / operador | Exige venta confirmada procedente de preventa; crea líneas de seguimiento y pasa a Active. |
| Distribución | Close Distribution / responsable | Exige todas las cantidades entregadas y ninguna incidencia abierta. |
| Distribución | Devolución o aumento de demanda | Reabre una distribución cerrada cuando vuelve a existir cantidad pendiente. |
| Incidencia | Report Incident / operador | Crea incidencia Open con descripción, fecha y responsable permitido en la compañía; no mueve stock. |
| Incidencia | Resolve Incident / responsable | Exige explicación; conserva fecha y autor de resolución; el registro pasa a ser inmutable. |
| Conciliación | Confirm Statement / responsable | Congela subtotales, cantidades, precios y referencias de líneas válidas del proveedor. |
| Conciliación | Record Adjustment / responsable | Registra un ajuste separado, no nulo, con motivo; no reescribe el subtotal confirmado. |

Las transiciones se validan también en el servidor. Escribir `state` directamente, modificar referencias generadas o alterar hijos de documentos congelados no sustituye a una acción de negocio.

## Cantidades, costos y compromisos

El valor de compra de una línea es cantidad × precio. Los gastos se reparten por valor de compra usando redondeo acumulado para asignar también los centavos residuales. El costo total operativo de línea es compra + gasto asignado; el costo unitario conserva seis decimales. Los totales monetarios respetan la precisión de la moneda.

El compromiso suma preventas confirmadas. Después de convertir, toma la cantidad de sus líneas de venta no canceladas, sin sumar de nuevo la preventa. El exceso sobre la cantidad prevista produce una advertencia, **no un bloqueo ni una garantía de disponibilidad**.

La distribución lee `sale.order.line.qty_delivered`. Las devoluciones deben usar el flujo estándar y la política de actualización de cantidades (`to_refund`) del caso demostrado. Los detalles mantienen sus unidades; la cabecera solo suma cuando todas coinciden. No se deben interpretar sumas de unidades incompatibles como una medida física.

## Conciliación y evidencia histórica

El importe conciliado es el subtotal de venta **sin impuestos**, atribuible al proveedor mediante la importación de origen. No es el costo de compra ni una deuda contable. Una línea de venta solo puede pertenecer a una conciliación, incluso mientras esta está en borrador. Para corregir un cierre se añade otro registro con motivo; para revertir un ajuste, se registra un ajuste opuesto deliberado.

Las referencias automáticas son únicas por compañía. Los documentos se crean en Draft, se editan y borran solo cuando el flujo lo permite. Copiar importaciones/preventas crea nuevas referencias sin enlaces finales; las distribuciones no se duplican. Las conciliaciones duplicadas no arrastran líneas conciliadas ni ajustes.

Archivar un puerto lo excluye de nuevas revisiones, pero conserva las relaciones de operaciones históricas. No se permite eliminar catálogos referenciados cuando una relación está definida con `ondelete='restrict'`.

## Matriz de roles

| Capacidad | Consulta | Operador | Responsable |
| --- | --- | --- | --- |
| Consultar documentos propios de compañías permitidas | Sí | Sí | Sí |
| Crear/editar borradores y sus líneas | No | Sí | Sí |
| Mantener puertos | No | No | Sí |
| Enviar importación a revisión | No | Sí | Sí |
| Validar importación, confirmar compra, cancelar importación | No | No | Sí |
| Confirmar/cancelar preventa y crear presupuesto elegible | No | Sí | Sí |
| Ejecutar operaciones estándar de stock/ventas/compras | No por este perfil | Grupos operativos estándar | Grupos de gestión estándar |
| Iniciar distribución y registrar incidencia | No | Sí | Sí |
| Resolver incidencia y cerrar/cancelar distribución | No | No | Sí |
| Confirmar conciliación y registrar ajuste | No | No | Sí |

Los permisos son aditivos: Consulta no revoca permisos de otros grupos asignados al mismo usuario. Ninguno de estos perfiles equivale a administrador contable. Las reglas globales por `company_ids` cubren cabeceras, hijos e incidencias; los asistentes también tienen reglas propias.

## Migración

La versión anterior podía afirmar estados sin documentos físicos. La migración conserva referencias y snapshots originales, marca operaciones para revisión y no fabrica recepciones, fechas ni autores históricos. Relaciones ambiguas, colisiones de códigos y monedas incompatibles detienen el upgrade. No se borra información para conseguir una validación verde.

La evidencia ejecutable está en los tests de cada addon y en `scripts/acceptance.py`, `scripts/concurrency.py` y `scripts/migration_fixture.py`. El detalle de responsabilidades está en [las fichas](modules/README.md).
