# TradeOps 360 — primera fase funcional

Extensión educativa de **Odoo 17** para recorrer un proceso real: importación → recepción → preventa → presupuesto/venta → entrega e incidencias → conciliación comercial. Se reutilizan Compras, Ventas, Inventario, contactos y productos; no hay un backend ni un inventario paralelo.

## Estado y límites

Los cinco addons tienen modelos, vistas, permisos y pruebas. La versión de los manifests es `17.0.2.0.0`. **Implementación no equivale a aceptación**: consulta [los 22 objetivos y su evidencia](docs/phase-1-objectives.md) y el `final-result.json` del workflow correspondiente al commit que vayas a utilizar. La defensa personal del desarrollo sigue siendo una actividad de aprendizaje, no algo que certifique CI.

Una importación tiene una compañía, un proveedor principal, un almacén y la moneda de esa compañía. El prorrateo calcula **costos operativos**, no valoración contable; las preventas son compromisos, no reservas garantizadas; la conciliación agrupa subtotales comerciales, no acredita pagos. No se incluyen API externa, pagos propios, multidivisa, flota avanzada ni localizaciones fiscales.

## Inicio con Docker Compose

Requisitos: Git, Python 3, Docker Engine y Docker Compose v2. Las imágenes de Odoo y PostgreSQL están fijadas por digest en `compose.yaml`. Este entorno usa volúmenes propios, no expone PostgreSQL al host y publica Odoo únicamente en `127.0.0.1:8070`; no reemplaza tu instalación desde fuente.

```bash
git clone https://github.com/Alej0prepper/TradeOps_360.git
cd TradeOps_360
test -e .env || cp .env.example .env
```

Edita `.env`: establece tres contraseñas distintas para `POSTGRES_PASSWORD`, `ODOO_MASTER_PASSWORD` y `TRADEOPS_ADMIN_PASSWORD` (esta última, mínimo 12 caracteres). Para seguir la demostración usa `ODOO_DB=tradeops_phase1_demo`. No publiques `.env`.

```bash
bash scripts/dev.sh init tradeops_phase1_demo
bash scripts/dev.sh up
```

Abre `http://localhost:8070` e inicia sesión como `admin` con `TRADEOPS_ADMIN_PASSWORD`. `init` configura o restablece expresamente ese administrador: no es un comando de actualización habitual.

Para cargar **solo datos ficticios en esa base de demostración**:

```bash
read -rsp 'Contraseña temporal para los usuarios demo: ' TRADEOPS_DEMO_PASSWORD
echo
export TRADEOPS_DEMO_PASSWORD
bash scripts/dev.sh demo tradeops_phase1_demo
unset TRADEOPS_DEMO_PASSWORD
```

Usuarios: `phase1_operator`, `phase1_responsible` y `phase1_viewer`. Los tres usan la contraseña temporal que acabas de introducir. La carga se rechaza cuando ya existen las fixtures; no borres datos para repetirla, utiliza otra base de demostración.

## Verificación

```bash
python3 scripts/static_check.py
python3 -m unittest discover -s scripts/tests -v
bash scripts/dev.sh test tradeops_phase1_test
```

Las pruebas rápidas no necesitan Odoo. Las pruebas de modelos sí se ejecutan dentro de Odoo. GitHub Actions añade la conversión concurrente, actualización desde el baseline real, restauración de base/filestore, navegador, PDF y ensayo de los comandos Docker. No se acepta un total verde si falta algún test previsto.

## Documentación del proyecto

La documentación está organizada por propósito. Para entender el sistema desde cero, empieza por la visión y el contrato funcional; para estudiar la implementación, continúa con arquitectura y fichas de módulos; para reproducir o aceptar la fase, utiliza las guías operativas y de demostración.

### Visión, alcance y reglas

- [Visión de TradeOps 360](docs/vision.md) — objetivo del proyecto, flujo de negocio, preocupaciones transversales y principio de extender Odoo en lugar de reconstruirlo.
- [Contrato funcional y de seguridad](docs/functional-spec.md) — reglas vigentes del dominio, workflows, roles, compañías, costos, stock, preventas, distribución y conciliación.
- [Objetivos y trazabilidad de la fase 1](docs/phase-1-objectives.md) — los 22 objetivos, criterios de aceptación y distinción entre diseñado, implementado, verificado y demostrado.
- [Alcance del sprint funcional](docs/sprint-functional.md) — autorización y límites específicos utilizados para completar la primera fase.
- [Roadmap del curso](docs/roadmap.md) — progresión pedagógica prevista por clases; no debe confundirse con evidencia de que una clase ya fue impartida.

### Arquitectura y módulos

- [Arquitectura de la fase 1](docs/architecture.md) — ejecución dentro de Odoo, dependencias entre addons, propiedad de responsabilidades e integración con Compras, Ventas e Inventario estándar.
- [Índice de fichas funcionales y técnicas](docs/modules/README.md) — punto de entrada a las especificaciones de los cinco addons:
  - [`trade_core`](docs/modules/trade_core.md) — catálogos, perfiles, referencias y garantías comunes.
  - [`trade_import`](docs/modules/trade_import.md) — importación, gastos, compra y recepción estándar.
  - [`trade_presale`](docs/modules/trade_presale.md) — compromisos comerciales, advertencia de sobrecompromiso y conversión única.
  - [`trade_distribution`](docs/modules/trade_distribution.md) — entregas físicas, pendientes e incidencias.
  - [`trade_reconciliation`](docs/modules/trade_reconciliation.md) — cierre comercial congelado y ajustes.
- [Cómo crear un módulo en Odoo 17](docs/como-crear-un-modulo-odoo17.md) — guía paso a paso sobre estructura de addons, manifest, ORM, modelos, relaciones, herencia, vistas, seguridad, tests, instalación y actualización.
- [Plantilla reutilizable de especificación de módulo](docs/templates/module-spec.md) — estructura para definir problema, alcance, estándar reutilizado, datos, workflow, seguridad, interfaz, integración, pruebas, operación y aprendizaje antes de implementar un nuevo addon.

### Validación, operación y entrega

- [Resumen funcional y guía de prueba frontend](docs/resumen-funcional.md) — recorrido manual completo de la fase 1 desde la perspectiva de un usuario normal de Odoo, con datos y resultados esperados.
- [Demostración de aceptación y defensa técnica](docs/demo-guide.md) — caso de demostración, diferencia entre evidencia automatizada y ejecución personal, y recorrido para explicar el sistema.
- [Operación, pruebas y recuperación](docs/operations.md) — entorno reproducible, comandos habituales, actualización, backup/restore y precauciones operativas.
- [Checklist de release readiness](docs/release-readiness.md) — comprobaciones técnicas y funcionales requeridas antes de considerar una revisión lista para entrega.
- [CHANGELOG](CHANGELOG.md) — evolución funcional y técnica registrada por versión/cambio.

### Decisiones de arquitectura

El [índice de decisiones](docs/decisions/README.md) conserva los ADR históricos. Los documentos 001–014 explican por qué se eligieron los límites entre addons, el modelo de importación, el catálogo de puertos, el prorrateo de gastos, la extensión de contactos, las preventas vinculadas a importaciones, la conversión a ventas estándar, las entregas e incidencias, la integridad de conciliación, Chatter para auditoría, la estrategia de pruebas, las invariantes del sprint, los límites entre costos/stock/historial comercial y la estrategia de upgrade y evidencia histórica.

### Registro de aprendizaje

El [índice de aprendizaje](docs/learning/README.md) conserva los incrementos didácticos sin reescribir las clases históricas como si hubieran descrito el estado final. Incluye:

- [Día 159 — primeros addons](docs/learning/day-159-first-addons.md).
- [Día 160 — primer modelo de importación](docs/learning/day-160-first-import-model.md).
- [Día 161 — relaciones de importación](docs/learning/day-161-import-relationships.md).
- [Día 162 — campos calculados y constraints](docs/learning/day-162-computed-fields-constraints.md).
- [Día 164 — gastos y distribución de costo](docs/learning/day-164-landed-cost-allocation.md).
- [Día 166 — extensión de Odoo y vistas](docs/learning/day-166-odoo-extension-and-views.md).
- [Día 172 — preventas vinculadas a importaciones](docs/learning/day-172-import-linked-presales.md).
- [Día 175 — preventa a `sale.order`](docs/learning/day-175-presale-sale-order-conversion.md).
- [Días 178–179 — entregas parciales, incidencias y wizard](docs/learning/day-178-partial-deliveries-incidents-wizards.md).
- [Sprint funcional de fase 1](docs/learning/phase-1-functional-sprint.md) — transformación del baseline educativo en un proceso verificable.
- [Recuperación de un error real de CLI](docs/learning/phase-1-cli-recovery.md) — fallo, corrección y regresión.
- [Evidencia de interfaz](docs/learning/phase-1-ui-evidence.md) — identidad de documentos y criterios para capturas fiables.

Los registros históricos sirven para estudiar cómo evolucionó el proyecto. Cuando exista una diferencia entre una nota histórica y el estado vigente, toma como referencia el [contrato funcional](docs/functional-spec.md), la [arquitectura](docs/architecture.md) y las [fichas actuales de módulos](docs/modules/README.md).