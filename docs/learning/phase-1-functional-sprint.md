# Sprint funcional: del ejemplo de clase a un proceso verificable

## Problema
El baseline tenía modelos y pantallas, pero algunas afirmaciones de negocio no se apoyaban en hechos físicos y parte de la seguridad/documentación estaba incompleta.

## Decisiones y archivos
Los [ADR 012](../decisions/012-functional-sprint-invariants.md), [013](../decisions/013-costs-stock-and-commercial-boundaries.md) y [014](../decisions/014-upgrade-and-legacy-evidence.md) fijan las garantías: permisos en servidor, reutilización de documentos estándar, costos operativos y migraciones sin historia inventada. Las [fichas](../modules/README.md) localizan el código por responsabilidad.

## Transformaciones comprobables
| Antes | Ahora | Evidencia |
| --- | --- | --- |
| Estado de importación declarativo | Compra y recepción estándar determinan el cierre | Tests de importación y aceptación 6+4. |
| Un botón parecía proteger una acción | ACL, reglas de compañía y validaciones de servidor | Tests con usuarios normales y escritura directa de hijos. |
| Repetir conversión podía duplicar | Bloqueo y unicidad conservan un presupuesto | Dos transacciones reales en `scripts/concurrency.py`. |
| Reserva podía confundirse con entrega | Seguimiento de cantidad física neta y devoluciones | Tests de distribución y unidades mixtas. |
| Total comercial dependiente de cambios posteriores | Snapshot confirmado y ajustes separados | Tests de reconciliación. |
| Checklist de recuperación sin ensayo suficiente | Instalación, upgrade y restauración ejecutables | CI con verificación de registros y hash de filestore. |

## Ampliación de regresión
La recuperación de este sprint añade pruebas de aislamiento para incidencias y ajustes, incluyendo selección de compañía entre varias autorizadas. El verificador compara los métodos previstos en el source con las líneas de ejecución de Odoo y registra el commit de la evidencia. Sus tests sintéticos demuestran que el control rechaza evidencia incompleta; no se cuentan como tests de la aplicación.

## Ejercicio de defensa
Explica por qué `onchange` no sustituye a una restricción y por qué una restricción única no demuestra por sí sola concurrencia. Después localiza la regla en el código y ejecuta su prueba. Sigue la [demostración](../demo-guide.md) para registrar el resultado personal.
