# Decision 008: separar cantidades físicas e incidencias

Las cantidades de una distribución se leen de la transferencia estándar de
Odoo (`stock.picking` y `stock.move.line`). TradeOps solo deriva la cantidad
pendiente y registra la explicación empresarial en `trade.delivery.incident`.
El incident wizard es transitorio y delega persistencia al modelo de dominio.
