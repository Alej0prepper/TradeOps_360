# TradeOps 360 — arquitectura de la primera fase

## Ejecución

```text
Usuario → cliente web Odoo → acciones/modelos → ORM → PostgreSQL
                                 ↓
                     Compras / Ventas / Inventario
```

TradeOps se ejecuta dentro de Odoo 17. No existe un servicio backend independiente ni tablas alternativas de clientes, productos, ventas o existencias.

## Dependencias y propiedad

`trade_core` depende de `contacts`, `sale_stock`, `purchase_stock` y `mail`. Centraliza puertos, códigos de contacto, roles, secuencias y dos mixins de invariantes. Esta dependencia amplia coordina permisos operativos de las aplicaciones estándar; no pretende ser una biblioteca mínima instalable sin ellas.

`trade_import` depende de Core y Compras/Inventario; posee importación, líneas y gastos. Extiende compras y recepciones para conservar procedencia y actualizar el estado desde hechos físicos.

`trade_presale` depende de Importaciones y Ventas/Inventario; posee compromisos comerciales. Extiende ventas y líneas estándar con enlaces protegidos, y calcula compromiso sin duplicar demanda.

`trade_distribution` depende de Preventas y Ventas/Inventario; posee seguimiento e incidencias. No decide existencias. Su cierre depende de entregas netas y resolución de incidencias.

`trade_reconciliation` depende de Preventas y Ventas; posee declaraciones comerciales, snapshots y ajustes. No crea ni reemplaza asientos o pagos.

Las dependencias exactas y archivos cargados están en cada `__manifest__.py`; las [fichas](modules/README.md) detallan contratos y pruebas.

## Invariantes, seguridad y transacciones

`trade.document.mixin` protege creación, compañía, referencia, estado, enlaces, edición y borrado. `trade.child.mixin` protege los padres de líneas y gastos incluso al modificar hijos directamente. No son un motor genérico de workflow: cada addon conserva sus acciones de negocio.

Los roles se combinan con ACL y reglas globales por compañías permitidas. `check_company=True` y validaciones específicas evitan vínculos incompatibles. Las ayudas XML no sustituyen la validación del servidor.

Las mutaciones ordinarias usan ORM. El SQL de bloqueo toma filas existentes después de comprobar permisos; los cambios continúan por ORM. Las restricciones únicas protegen vínculos uno-a-uno, y la prueba concurrente usa conexiones/transacciones separadas con reintento tras conflicto de serialización. No se hace `commit()` en las acciones de negocio; los commits explícitos de scripts preparan únicamente fixtures desechables.

Los hooks de Inventario usan `sudo()` de forma acotada para sincronizar operaciones ya enlazadas al movimiento validado. No se usa un flag de contexto del cliente para saltar permisos.

## Trazabilidad y límites

Chatter registra transiciones y eventos. Las conciliaciones guardan snapshots al confirmar; sus ajustes son registros nuevos e inmutables. No se afirma que todo cambio de una tabla estándar constituya una auditoría contable completa.

Los nombres técnicos heredados como `landed_total` conservan compatibilidad, pero las etiquetas y documentación dicen **costo operativo**. Compromiso no es reserva, entrega no es cantidad reservada y conciliación comercial no es pago.

## Verificación y entrega

Las pruebas de modelos están en `custom_addons/*/tests`. Las pruebas rápidas de infraestructura están en `scripts/tests`. CI instala en limpio, compara el inventario de tests con lo ejecutado, ensaya concurrencia, actualización actual y desde el baseline `b72cf69`, recuperación de base/filestore y navegación/PDF.

Un único `final-result.json` identifica el commit y los resultados completos del run. No basta con combinar éxitos de ejecuciones distintas. El contenedor local usa volúmenes propios y acceso web local; no representa una configuración de producción.

El [roadmap](roadmap.md) conserva la progresión del curso y el [sprint](sprint-functional.md) registra la excepción de alcance autorizada. Las decisiones anteriores son historia; las ADR 012–014 y el contrato funcional describen la fase actual.
