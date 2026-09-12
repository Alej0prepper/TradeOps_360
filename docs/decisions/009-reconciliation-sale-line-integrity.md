# Decision 009: reconciliar líneas de venta con una restricción única

Una conciliación de proveedor agrupa líneas de `sale.order.line` ya
confirmadas. TradeOps conserva el proveedor como dato propio de la operación,
porque el flujo actual no tiene una relación de proveedor en la venta estándar.

`trade.reconciliation.line` es la tabla de relación y define
`UNIQUE(sale_line_id)`. La validación ORM devuelve un mensaje comprensible en
el caso habitual; la restricción PostgreSQL mantiene la invariante cuando dos
transacciones intentan usar la misma línea simultáneamente. La acción no hace
commits manuales: Odoo conserva la creación, validación y confirmación dentro
de la transacción de la solicitud.

Las líneas se eliminan en cascada al borrar una conciliación, de modo que una
venta no queda marcada sin su registro de conciliación. Una futura política de
cancelación y auditoría podrá sustituir el borrado sin cambiar esa integridad.
