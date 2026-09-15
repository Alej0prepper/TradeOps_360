# TradeOps 360 — primera fase funcional

Extensión educativa de **Odoo 17** para recorrer un proceso real: importación → recepción → preventa → presupuesto/venta → entrega e incidencias → conciliación comercial. Se reutilizan Compras, Ventas, Inventario, contactos y productos; no hay un backend ni un inventario paralelo.

## Estado y límites

Los cinco addons tienen modelos, vistas, permisos y pruebas. La versión de los manifests es `17.0.2.0.0`. **Implementación no equivale a aceptación**: consulta [los 22 objetivos y su evidencia](docs/phase-1-objectives.md) y el `final-result.json` del workflow correspondiente al commit que vayas a utilizar. La defensa personal del desarrollo sigue siendo una actividad de aprendizaje, no algo que certifique CI.

Una importación tiene una compañía, un proveedor principal, un almacén y la moneda de esa compañía. El prorrateo calcula **costos operativos**, no valoración contable; las preventas son compromisos, no reservas garantizadas; la conciliación agrupa subtotales comerciales, no acredita pagos. No se incluyen API externa, pagos propios, multidivisa, flota avanzada ni localizaciones fiscales.

## Inicio con Docker Compose

Requisitos: Git, Python 3, Docker Engine y Docker Compose v2. Las imágenes de Odoo y PostgreSQL están fijadas por digest en `compose.yaml`. Este entorno usa volúmenes propios, no expone PostgreSQL al host y publica Odoo únicamente en `127.0.0.1:8070`; no reemplaza tu instalación desde fuente.

```bash
git clone --branch sprint/phase-1-functional https://github.com/Alej0prepper/TradeOps_360.git
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

## Guías de trabajo

- [Reglas funcionales y seguridad](docs/functional-spec.md).
- [Objetivos y trazabilidad](docs/phase-1-objectives.md).
- [Arquitectura](docs/architecture.md) y [fichas de los cinco módulos](docs/modules/README.md).
- [Plantilla para desarrollar un módulo](docs/templates/module-spec.md).
- [Operación, actualización y recuperación](docs/operations.md).
- [Despliegue controlado en servidor compartido](docs/shared-server-deployment.md).
- [Demostración y defensa técnica](docs/demo-guide.md).
- [Decisiones](docs/decisions/README.md), [aprendizaje](docs/learning/README.md) y [changelog](CHANGELOG.md).

El [roadmap del curso](docs/roadmap.md) conserva la progresión pedagógica. El [sprint autorizado](docs/sprint-functional.md) permite completar esta primera fase en una rama separada, sin declarar impartidas las clases futuras.
