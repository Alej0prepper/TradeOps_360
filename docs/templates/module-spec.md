# Ficha funcional y técnica de un módulo Odoo 17

Copia esta ficha en `docs/modules/<addon-o-incremento>.md`. Primero define reglas; después implementa incrementos pequeños. Distingue diseñado, implementado, verificado y demostrado. “No aplica” requiere una justificación.

## 0. Identidad y estado

Nombre funcional; addon; capacidad; responsable/revisor; Odoo/edición/revisión; PostgreSQL; dependencias; commit base; estado y fecha de verificación.

## 1. Problema y resultado

Como [rol], necesito [acción] sobre [objeto] para [resultado]. Describe situación actual, resultado observable y quién acepta la regla. Incluye un caso correcto y otro que deba rechazarse sin efectos parciales.

## 2. Alcance y exclusiones

Enumera operaciones incluidas y excluidas. Decide compañía, almacén, moneda, unidades, estados y volúmenes. No escondas decisiones críticas detrás de “después”.

## 3. Evaluación de Odoo estándar

| Necesidad | Modelo/app estándar | Brecha | Configurar, extender o crear |
| --- | --- | --- | --- |
| Completar | Completar | Completar | Justificar |

Explica cada modelo nuevo y cada dependencia del manifest. Registra una alternativa descartada.

## 4. Modelo de datos y propiedad

| Campo/relación | Tipo | Obligatorio/default | Fuente de verdad | Regla de borrado |
| --- | --- | --- | --- | --- |
| Completar | Completar | Completar | Completar | Completar |

Incluye cabecera/hijos, compañía, almacén, catálogos compartidos, moneda/unidades, fórmula y redondeo, dependencias `@api.depends`, justificación de `store=True`, datos vivos y snapshots.

## 5. Flujo e invariantes

| Acción | Origen → destino | Rol | Precondición | Efecto | Error sin efecto parcial |
| --- | --- | --- | --- | --- | --- |
| Completar | Completar | Completar | Completar | Completar | Completar |

Decide creación, edición, borrado, copia, archivo, cancelación, cambios directos de hijos y modificaciones del origen. Especifica repetición, concurrencia, atomicidad y propiedad de la transacción.

## 6. Seguridad

Define lectura, creación, edición, borrado y acciones críticas para sin rol, consulta, operador y responsable. Repite para hijos/asistentes. Identifica grupos, ACL, reglas, `check_company`, permisos estándar, datos sensibles y cualquier `sudo()` acotado. Prueba acceso por ID y búsqueda, no solo menús.

## 7. Interfaz

Menú, acción, lista, formulario, filtros, botones y navegación. Para cada dominio/onchange identifica la regla del servidor equivalente. Justifica wizard y reporte. Usa terminología que no confunda compromiso, stock, costos y contabilidad.

## 8. Integración y efectos

Entrada, dueño estándar, operación, documento resultante y fallo esperado. Describe Chatter/actividades y qué NO reemplaza el addon. Para API externa, solo cuando esté aprobada, define autenticación, autorización e idempotencia.

## 9. Incrementos y archivos

Planifica comportamiento → archivos → test → resultado. Revisa `__init__.py`, manifest, orden XML/CSV, IDs externos, migraciones y compatibilidad. No implementes funciones de otra fase sin autorización.

## 10. Pruebas

| Caso | Dado/cuando/entonces | Nivel | Archivo/método | Evidencia del commit |
| --- | --- | --- | --- | --- |
| Instalación limpia | Completar | Odoo | Completar | No ejecutado |
| Flujo y caso inválido | Completar | Modelo/UI | Completar | No ejecutado |
| Rol y compañías | Completar | Seguridad | Completar | No ejecutado |
| Hijos y cambios de origen | Completar | ORM | Completar | No ejecutado |
| Repetición/concurrencia | Completar | Transacciones separadas | Completar | No ejecutado |
| Upgrade/recuperación | Completar | Integración | Completar | No ejecutado |

Añade límites de moneda, unidades, cantidades, devoluciones y fallos intermedios. Dos llamadas secuenciales no prueban concurrencia.

## 11. Ejecución

Comandos exactos para instalar, probar y actualizar; configuración sin secretos; datos ficticios; usuario y pasos manuales; backup/restauración; logs y límites conocidos. Registra lo ejecutado, no solo lo previsto.

## 12. Definición de terminado

Alcance aceptado, seguridad completa, tests ejecutados, instalación/upgrade comprobados, flujo con usuario normal, recuperación al nivel requerido, documentación y aceptación vinculadas a la misma revisión. Un checkbox no sustituye evidencia.

## 13. Aprendizaje

Qué aprendí; por qué elegí la solución; qué fallo reproduje/corregí; qué prueba lo protege; cómo entregaría otro cambio. Incluye un mini reto y una explicación que puedas defender sin leer todo el chat.
