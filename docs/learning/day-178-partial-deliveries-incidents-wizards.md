# Día 178–179 — Entregas parciales, incidencias y wizard

TradeOps incorpora `trade.distribution` como enlace operativo entre una venta y
una transferencia de Inventory. La cantidad entregada se calcula desde
`stock.move.line.qty_done`; la pendiente es un valor derivado y nunca se guarda
como una segunda fuente de verdad.

Las excepciones empresariales viven en `trade.delivery.incident`. El botón
`Report Incident` abre un `TransientModel` y delega la creación al método de
dominio `report_incident`.

La verificación disponible es `python3 -m compileall -q custom_addons` y
`git diff --check`. La ejecución funcional requiere Odoo 17 con `sale` y
`stock` instalados.
