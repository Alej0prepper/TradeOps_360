# trade_core — Catálogos y garantías comunes

## 0. Identificación
Odoo 17 · addon `17.0.2.0.0` · fase 1. Estado: implementación y criterios documentados; la evidencia válida es la ejecución del mismo commit en CI.

## 1. Problema y actores
Preparar puertos y códigos comerciales y aplicar la misma política de permisos, numeración y propiedad a todos los documentos sin duplicar contactos ni productos. Los perfiles son Operador, Responsable y Consulta; véase la [matriz común](../functional-spec.md).

## 2. Alcance y exclusiones
No es un repositorio de reglas de todos los dominios ni un backend independiente. Los grupos estándar son aditivos; asignar Consulta no revoca permisos externos.

## 3. Odoo estándar y dependencias
`contacts`, `sale_stock`, `purchase_stock`, `mail`. `trade.port` (catálogo global), `trade.document.mixin`, `trade.child.mixin` y `trade.legacy.mixin` (abstractos). Extiende `res.partner` con `trade_code`.

## 4. Datos y propiedad
Puerto: nombre y código obligatorios, código normalizado a mayúsculas y único, `active` para archivar. Documento: referencia generada, compañía obligatoria y moneda relacionada. Hijo: compañía/moneda derivadas de su cabecera. `trade_code` es opcional y no único. Cabeceras e hijos operativos usan las compañías seleccionadas del usuario; los catálogos compartidos conservan las reglas estándar.

## 5. Reglas y workflow
Los catálogos no tienen un workflow transaccional. Solo el responsable mantiene puertos. Cada documento usa su propia secuencia y comienza en borrador; los mixins rechazan referencias, estados y vínculos generados suministrados por el cliente.

No borrar evidencia de documentos fuera de borrador. Proteger también escrituras directas sobre hijos y cambios de padre. Antes de bloquear filas, verificar ACL y reglas de registro. No usar una bandera en el contexto como bypass de seguridad.

## 6. Seguridad y transacciones
ACL, record rules y acciones de servidor actúan juntas; la vista no es una barrera de seguridad. Los hijos se validan también fuera de su formulario. Se respeta la transacción de Odoo; errores no deben dejar operaciones parciales. Ver [arquitectura](../architecture.md).

## 7. Experiencia de usuario
TradeOps → Configuration → Ports; el formulario estándar de contactos incorpora TradeOps Code mediante herencia XML/XPath.

## 8. Integración y archivos
Rutas relativas a `custom_addons/trade_core/`: `models/common.py`, `models/legacy.py`, `models/trade_port.py`, `models/res_partner.py`, `security/trade_groups.xml`, `data/trade_sequences.xml`.

## 9. Incremento explicado
Antes había un catálogo sin permisos suficientes y documentos `New`. Ahora hay grupos reutilizables, referencias automáticas y protecciones transversales; no se asigna a Core el workflow de importación.

## 10. Pruebas y aceptación
`tests/test_trade_core.py`: catálogo legible, mantenimiento restringido, códigos únicos/normalizados, rechazo de nombres vacíos y extensión de contactos. Las pruebas de cada módulo consumidor verifican los mixins en documentos concretos.

Caso de aceptación: Crear un puerto con el responsable, leerlo con Consulta e intentar modificarlo con Operador. Un código que solo cambia mayúsculas no debe crear otro puerto. Conservar también un rechazo por permisos y uno por regla de negocio, no solo el caso exitoso.

## 11. Ejecución reproducible
Desde la raíz del repositorio: `bash scripts/dev.sh test tradeops_phase1_test` instala los cinco addons y ejecuta sus pruebas. Los comandos de instalación, actualización y recuperación están en [operaciones](../operations.md). Los casos concurrentes y de migración se ejecutan además en CI.

## 12. Terminado y evidencia
El workflow debe estar verde para el commit elegido y su `final-result.json` debe indicar cero pruebas previstas ausentes. Consultar [objetivos](../phase-1-objectives.md) y [demostración](../demo-guide.md); no sustituir aceptación de usuario por un recuento de tests.

## 13. Aprendizaje y defensa
`models.AbstractModel`, `_inherit`, `@api.model_create_multi`, `fields.Command`, ACL frente a record rules y secuencias. Explicar por qué una protección solo en una vista no protege el servidor.
