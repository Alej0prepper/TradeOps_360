# trade_import — Importaciones, gastos y recepciones

## 0. Identificación
Odoo 17 · addon `17.0.2.0.0` · fase 1. Estado: implementación y criterios documentados; la evidencia válida es la ejecución del mismo commit en CI.

## 1. Problema y actores
Relacionar una operación de importación con su compra y sus recepciones físicas, conservar trazabilidad y explicar los costos operativos por producto. Los perfiles son Operador, Responsable y Consulta; véase la [matriz común](../functional-spec.md).

## 2. Alcance y exclusiones
Un proveedor, almacén y moneda de compañía por importación. Los gastos son costos operativos; no generan landed costs contables ni facturas de proveedor personalizadas.

## 3. Odoo estándar y dependencias
`trade_core`, `purchase_stock`, `mail`. `trade.import`, `trade.import.line`, `trade.import.expense`. Extiende `purchase.order`, `purchase.order.line` y `stock.picking` para conservar origen y sincronizar la recepción.

## 4. Datos y propiedad
Cabecera: cliente, proveedor, financista opcional, compañía, almacén, puertos y fechas. Línea: producto almacenable, cantidad positiva, precio de compra no negativo, unidad estándar, compra relacionada, cantidad recibida y costos calculados. Gastos: tipo e importe no negativo. Cabeceras e hijos operativos usan las compañías seleccionadas del usuario; los catálogos compartidos conservan las reglas estándar.

## 5. Reglas y workflow
Draft → Document Review → Validated → In Transit → Receiving/Partially Received → Completed. Operador envía a revisión; Responsable valida y confirma compra. Inventario determina recepción parcial y cierre; cancelar queda bloqueado tras movimientos terminados.

Proveedor, almacén, compañía y moneda deben ser coherentes. Puertos distintos y activos al revisar. Prorrateo proporcional al valor de compra, con redondeo residual conservado; rechazar gastos positivos sin base de reparto. Congelar fuentes fuera de borrador y evitar compras duplicadas.

## 6. Seguridad y transacciones
ACL, record rules y acciones de servidor actúan juntas; la vista no es una barrera de seguridad. Los hijos se validan también fuera de su formulario. Se respeta la transacción de Odoo; errores no deben dejar operaciones parciales. Ver [arquitectura](../architecture.md).

## 7. Experiencia de usuario
Lista, formulario, filtros, botones de compra/recepciones y resumen QWeb de importación. Las etiquetas dicen Operational Cost, no valoración contable.

## 8. Integración y archivos
Rutas relativas a `custom_addons/trade_import/`: `models/trade_import.py`, `models/trade_import_line.py`, `models/trade_import_expense.py`, `models/purchase_order.py`, `models/stock_picking.py`, `report/trade_import_report.xml`.

## 9. Incremento explicado
Antes se podían cambiar estados sin recepción. Ahora una compra genera operaciones estándar y el cierre se deriva de mercancía recibida; no existe inventario propio.

## 10. Pruebas y aceptación
`tests/test_trade_import.py`: costos, redondeo, cantidades/precios, rutas, estados, permisos/hijos, compañías, compra única, recepción 6+4, lotes y resumen HTML. `scripts/acceptance.py` aporta un caso de varios productos y documento PDF en el smoke de navegador.

Caso de aceptación: Importar diez unidades, recibir seis y después cuatro desde Inventario. Ver las dos recepciones y comprobar que reservar o cancelar un picking no equivale a recibir. Conservar también un rechazo por permisos y uno por regla de negocio, no solo el caso exitoso.

## 11. Ejecución reproducible
Desde la raíz del repositorio: `bash scripts/dev.sh test tradeops_phase1_test` instala los cinco addons y ejecuta sus pruebas. Los comandos de instalación, actualización y recuperación están en [operaciones](../operations.md). Los casos concurrentes y de migración se ejecutan además en CI.

## 12. Terminado y evidencia
El workflow debe estar verde para el commit elegido y su `final-result.json` debe indicar cero pruebas previstas ausentes. Consultar [objetivos](../phase-1-objectives.md) y [demostración](../demo-guide.md); no sustituir aceptación de usuario por un recuento de tests.

## 13. Aprendizaje y defensa
Campos calculados almacenados, dependencias, precisión monetaria, restricciones, relaciones a modelos estándar y extensión mediante `super()`. Diferenciar una decisión comercial de un hecho físico.
