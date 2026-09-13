# trade_distribution — Seguimiento físico e incidencias

## 0. Identificación
Odoo 17 · addon `17.0.2.0.0` · fase 1. Estado: implementación y criterios documentados; la evidencia válida es la ejecución del mismo commit en CI.

## 1. Problema y actores
Distinguir preparación/reserva de entrega real, seguir pendientes y registrar excepciones sin adulterar cantidades de Inventario. Los perfiles son Operador, Responsable y Consulta; véase la [matriz común](../functional-spec.md).

## 2. Alcance y exclusiones
Sin planificación de flota, conductores o rutas. Una devolución sin actualizar cantidades sigue la semántica estándar de Odoo; la demostración activa explícitamente esa política.

## 3. Odoo estándar y dependencias
`trade_presale`, `sale_stock`, `mail`. `trade.distribution`, `trade.distribution.line`, `trade.delivery.incident` y `trade.report.delivery.incident.wizard`; extiende operaciones estándar para recomputación/reapertura.

## 4. Datos y propiedad
Una distribución por venta; líneas vinculadas a líneas de venta, unidades, cantidad entregada y pendiente. Incidencia: tipo, descripción, fecha, responsable, estado, resolución, autor y fecha de resolución. Cabeceras e hijos operativos usan las compañías seleccionadas del usuario; los catálogos compartidos conservan las reglas estándar.

## 5. Reglas y workflow
Draft → Active por Operador; Closed por Responsable solo sin pendientes ni incidencias abiertas. Una devolución que actualiza cantidades puede reabrirla. Incidencia Open → Resolved por Responsable con explicación obligatoria.

Venta confirmada, procedente de TradeOps y compañía compatible. Cantidad entregada desde `sale.order.line.qty_delivered`; nunca contar reservas. No sumar unidades incompatibles. No duplicar distribuciones ni borrar incidencias. Resoluciones terminadas son inmutables.

## 6. Seguridad y transacciones
ACL, record rules y acciones de servidor actúan juntas; la vista no es una barrera de seguridad. Los hijos se validan también fuera de su formulario. Se respeta la transacción de Odoo; errores no deben dejar operaciones parciales. Ver [arquitectura](../architecture.md).

## 7. Experiencia de usuario
Formulario con venta, líneas y pickings; asistente Report Incident, lista de incidencias y acción Resolve Incident. Se conserva un mensaje en Chatter de la distribución.

## 8. Integración y archivos
Rutas relativas a `custom_addons/trade_distribution/`: `models/trade_distribution.py`, `models/trade_delivery_incident.py`, `wizard/trade_delivery_incident_wizard.py`, `views/trade_distribution_views.xml`.

## 9. Incremento explicado
Antes una cantidad preparada podía confundirse con entrega. Ahora el seguimiento deriva del estándar, se recalcula y refleja devoluciones; una explicación no cambia el stock.

## 10. Pruebas y aceptación
`tests/test_trade_distribution.py`: reserva, entregas parciales, devoluciones, unidades mixtas, incidencias, roles e inmutabilidad. `tests/test_multicompany.py`: cabecera, líneas, incidencia, acceso directo y responsable ajeno.

Caso de aceptación: Entregar seis de diez: quedan cuatro. Registrar una incidencia, completar entrega, resolver y cerrar. Devolver dos con actualización de cantidades y comprobar reapertura. Conservar también un rechazo por permisos y uno por regla de negocio, no solo el caso exitoso.

## 11. Ejecución reproducible
Desde la raíz del repositorio: `bash scripts/dev.sh test tradeops_phase1_test` instala los cinco addons y ejecuta sus pruebas. Los comandos de instalación, actualización y recuperación están en [operaciones](../operations.md). Los casos concurrentes y de migración se ejecutan además en CI.

## 12. Terminado y evidencia
El workflow debe estar verde para el commit elegido y su `final-result.json` debe indicar cero pruebas previstas ausentes. Consultar [objetivos](../phase-1-objectives.md) y [demostración](../demo-guide.md); no sustituir aceptación de usuario por un recuento de tests.

## 13. Aprendizaje y defensa
`TransientModel` frente a registro persistente, campos relacionados, invalidación de cálculos y auditoría. Diferenciar estado del transporte, picking y cantidad neta entregada.
