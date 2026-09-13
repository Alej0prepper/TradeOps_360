# trade_presale — Compromiso comercial y conversión

## 0. Identificación
Odoo 17 · addon `17.0.2.0.0` · fase 1. Estado: implementación y criterios documentados; la evidencia válida es la ejecución del mismo commit en CI.

## 1. Problema y actores
Registrar demanda antes de terminar una importación, visualizar sobrecompromiso y producir un presupuesto estándar sin duplicarlo ante reintentos o concurrencia. Los perfiles son Operador, Responsable y Consulta; véase la [matriz común](../functional-spec.md).

## 2. Alcance y exclusiones
No cobra anticipos ni garantiza reservas; la advertencia no bloquea sobreventa. Ventas decide la confirmación, negociación posterior permitida, entrega y facturación estándar.

## 3. Odoo estándar y dependencias
`trade_import`, `sale_stock`, `mail`. `trade.presale`, `trade.presale.line`; extiende importaciones/líneas para compromisos y `sale.order`/`sale.order.line` para procedencia.

## 4. Datos y propiedad
Cabecera: importación, cliente, compañía/moneda, lista de precios y presupuesto generado. Línea: línea de importación, producto/unidad derivados, cantidad positiva y precio no negativo. La cantidad convertida se consulta en la venta no cancelada. Cabeceras e hijos operativos usan las compañías seleccionadas del usuario; los catálogos compartidos conservan las reglas estándar.

## 5. Reglas y workflow
Draft → Confirmed → Converted, o Cancelled antes de convertir. Confirmar requiere importación validada y líneas válidas. Solo una importación Completed admite conversión. Una repetición abre el mismo presupuesto.

Revalidar líneas al cambiar la importación de la cabecera. Lista de precios en moneda de compañía. No contar dos veces demanda convertida. Bloquear edición de compromisos confirmados; volver a borrador requiere Responsable. El bloqueo transaccional y la restricción SQL se complementan.

## 6. Seguridad y transacciones
ACL, record rules y acciones de servidor actúan juntas; la vista no es una barrera de seguridad. Los hijos se validan también fuera de su formulario. Se respeta la transacción de Odoo; errores no deben dejar operaciones parciales. Ver [arquitectura](../architecture.md).

## 7. Experiencia de usuario
TradeOps → Presales; formulario, advertencia de sobrecompromiso, botón Create Quotation y apertura del documento estándar. La importación expone esperado, comprometido y no comprometido por producto.

## 8. Integración y archivos
Rutas relativas a `custom_addons/trade_presale/`: `models/trade_presale.py`, `models/trade_presale_line.py`, `models/trade_import.py`, `models/sale_order.py`, `views/trade_presale_views.xml`.

## 9. Incremento explicado
Antes bastaba un enlace para representar una conversión. Ahora se protege el origen, el estado y la transacción; la cantidad comercial sigue los cambios válidos de la venta.

## 10. Pruebas y aceptación
`tests/test_trade_presale.py` y `tests/test_forms.py`: estados, fuente de productos, cambios de cabecera, precios, moneda, protección y compromiso. `scripts/concurrency.py`: dos transacciones independientes convierten la misma preventa y comprueban un solo presupuesto.

Caso de aceptación: Confirmar preventa con la importación parcialmente recibida: aún no puede convertir. Tras recepción final, convertir dos veces: se conserva el mismo presupuesto. Mostrar la advertencia con demanda superior a lo previsto. Conservar también un rechazo por permisos y uno por regla de negocio, no solo el caso exitoso.

## 11. Ejecución reproducible
Desde la raíz del repositorio: `bash scripts/dev.sh test tradeops_phase1_test` instala los cinco addons y ejecuta sus pruebas. Los comandos de instalación, actualización y recuperación están en [operaciones](../operations.md). Los casos concurrentes y de migración se ejecutan además en CI.

## 12. Terminado y evidencia
El workflow debe estar verde para el commit elegido y su `final-result.json` debe indicar cero pruebas previstas ausentes. Consultar [objetivos](../phase-1-objectives.md) y [demostración](../demo-guide.md); no sustituir aceptación de usuario por un recuento de tests.

## 13. Aprendizaje y defensa
Recordsets, transacciones, restricciones únicas e idempotencia. Explicar por qué dos llamadas sucesivas no son una prueba de concurrencia y por qué no se hace `commit()` en la acción de negocio.
