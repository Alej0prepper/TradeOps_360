# Decision 013 - Costos operativos, documentos estandar e historial comercial

## Contexto

Los campos calculados de importacion no eran una recepcion fisica. El contador de distribucion sumaba cantidades sin exigir movimientos terminados. Una conciliacion confirmada seguia leyendo precios modificables de la venta.

## Decision

Cada importacion tiene una compania, proveedor principal y almacen de destino. La revision valida datos y congela las lineas; la validacion genera un presupuesto de compra estandar y la salida a transito confirma esa compra. Las recepciones, lotes y pendientes se procesan en Inventario. El estado completado depende de cantidades realmente recibidas; las devoluciones pueden reabrirlo.

El prorrateo es por valor de compra y usa redondeo acumulado para asignar todos los centavos. Los totales monetarios se redondean por moneda; el cociente unitario conserva seis decimales. Un gasto sin base positiva se rechaza. El costo es operativo: no se publica automaticamente como `stock.landed.cost` ni asiento contable.

La preventa registra compromiso, no stock reservado. El sobrecompromiso avisa y no bloquea. Tras la conversion se usa la cantidad de la linea de venta no cancelada para no contar dos veces la demanda y reflejar negociaciones posteriores.

La distribucion lee `sale.order.line.qty_delivered`, que pertenece a la integracion estandar de Ventas e Inventario. Las devoluciones que actualizan cantidades pedidas reducen la entrega neta. Se conserva una linea por producto/linea comercial; solo se muestra un agregado cuando todas las unidades coinciden.

La conciliacion comercial congela el subtotal sin impuestos de ventas confirmadas atribuibles al proveedor mediante la importacion. No representa cuentas por pagar, pagos ni conciliacion bancaria. Los ajustes son registros nuevos e inmutables con motivo y autor; un replay del mismo wizard no repite el ajuste.

## Consecuencias

Una operacion validada no se reescribe silenciosamente. Los documentos estandar conservan su flujo normal y su procedencia no se puede cambiar. El stock fisico no se duplica en tablas TradeOps. Los reportes identifican explicitamente los limites contables del calculo.
