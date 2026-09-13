# Fichas funcionales y técnicas

Las fichas siguen la estructura de la [plantilla reutilizable](../templates/module-spec.md): problema, alcance, estándar reutilizado, datos, workflow, seguridad, interfaz, integración, pruebas, operación y aprendizaje.

| Módulo | Responsabilidad |
| --- | --- |
| [trade_core](trade_core.md) | Catálogos, perfiles, referencias y garantías comunes. |
| [trade_import](trade_import.md) | Importación, gastos, compra y recepción estándar. |
| [trade_presale](trade_presale.md) | Compromiso, advertencia y conversión única. |
| [trade_distribution](trade_distribution.md) | Entregas físicas, pendientes e incidencias. |
| [trade_reconciliation](trade_reconciliation.md) | Cierre comercial congelado y ajustes. |

Lee primero el [contrato funcional](../functional-spec.md). Para implementar otro módulo, copia la plantilla, define sus criterios antes del código y conserva el vínculo entre cada regla, archivo, test y resultado.
