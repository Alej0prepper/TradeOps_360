# trade_reconciliation — Cierre comercial y ajustes

## 0. Identificación
Odoo 17 · addon `17.0.2.0.0` · fase 1. Estado: implementación y criterios documentados; la evidencia válida es la ejecución del mismo commit en CI.

## 1. Problema y actores
Agrupar ventas atribuibles a un proveedor y congelar un resumen comercial verificable, conservando correcciones posteriores sin reescribir la historia. Los perfiles son Operador, Responsable y Consulta; véase la [matriz común](../functional-spec.md).

## 2. Alcance y exclusiones
No sustituye conciliación bancaria/contable, saldo de proveedor, factura ni pago. El subtotal conciliado es venta sin impuestos, no costo de adquisición.

## 3. Odoo estándar y dependencias
`trade_presale`, `sale`, `mail`. No depende del módulo de distribución. `trade.reconciliation`, `trade.reconciliation.line`, `trade.reconciliation.adjustment`, `trade.reconciliation.adjustment.wizard`.

## 4. Datos y propiedad
Proveedor, compañía/moneda, fecha, líneas de venta y estado. Al confirmar se guardan subtotal sin impuestos, cantidad, precio unitario, producto, unidad y referencia de venta. Ajustes separados con importe, motivo e identificador de solicitud. Cabeceras e hijos operativos usan las compañías seleccionadas del usuario; los catálogos compartidos conservan las reglas estándar.

## 5. Reglas y workflow
Draft → Confirmed por Responsable. Se validan y bloquean las fuentes antes de capturar snapshots. Tras confirmar solo se añaden ajustes explícitos mediante acción/asistente.

Venta confirmada y trazable al proveedor por línea de preventa/importación; no mezclar compañías, monedas ni proveedores. Una línea no se reutiliza en otra conciliación. Total neto = subtotal congelado + ajustes. Ajuste no nulo, finito, motivo obligatorio y replay protegido.

## 6. Seguridad y transacciones
ACL, record rules y acciones de servidor actúan juntas; la vista no es una barrera de seguridad. Los hijos se validan también fuera de su formulario. Se respeta la transacción de Odoo; errores no deben dejar operaciones parciales. Ver [arquitectura](../architecture.md).

## 7. Experiencia de usuario
TradeOps → Reconciliations; líneas con evidencia congelada, total original y total ajustado separados; asistente Record Adjustment.

## 8. Integración y archivos
Rutas relativas a `custom_addons/trade_reconciliation/`: `models/trade_reconciliation.py`, `wizard/trade_reconciliation_adjustment_wizard.py`, `views/trade_reconciliation_views.xml`, `migrations/17.0.2.0.0/post-migrate.py`.

## 9. Incremento explicado
Antes el total podía seguir cambiando con una venta. Ahora el cierre conserva valores propios y un cambio posterior se explica con un ajuste, no con una edición silenciosa.

## 10. Pruebas y aceptación
`tests/test_trade_reconciliation.py`: subtotal, procedencia, lotes inválidos atómicos, roles, unicidad ORM/SQL, snapshot y ajustes/replay. `tests/test_multicompany.py`: cabeceras, líneas y ajustes bajo compañía exclusiva y selección multicompañía.

Caso de aceptación: Conciliar subtotales por 2 000, confirmar, modificar una condición permitida de venta y mostrar que el cierre no cambia. Registrar ajuste de −50: total comercial ajustado 1 950. Conservar también un rechazo por permisos y uno por regla de negocio, no solo el caso exitoso.

## 11. Ejecución reproducible
Desde la raíz del repositorio: `bash scripts/dev.sh test tradeops_phase1_test` instala los cinco addons y ejecuta sus pruebas. Los comandos de instalación, actualización y recuperación están en [operaciones](../operations.md). Los casos concurrentes y de migración se ejecutan además en CI.

## 12. Terminado y evidencia
El workflow debe estar verde para el commit elegido y su `final-result.json` debe indicar cero pruebas previstas ausentes. Consultar [objetivos](../phase-1-objectives.md) y [demostración](../demo-guide.md); no sustituir aceptación de usuario por un recuento de tests.

## 13. Aprendizaje y defensa
Snapshot histórico frente a campo relacionado, unicidad final en PostgreSQL, comprobaciones de procedencia y atomicidad de lotes. El ajuste no es un asiento contable.
