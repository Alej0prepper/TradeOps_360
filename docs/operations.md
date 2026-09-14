# Operación, pruebas y recuperación

## Entorno reproducible

Sigue el [README](../README.md). `compose.yaml` fija Odoo 17 y PostgreSQL 16 por digest; `config/odoo.conf.example` es una plantilla sin credenciales. `scripts/odoo-entrypoint.py` genera un archivo privado y pasa su ruta mediante `ODOO_RC`, manteniendo intactos subcomandos como `shell`.

No necesitas modificar el PostgreSQL de tu instalación desde fuente. Docker usa sus propios volúmenes y el puerto web 8070. No compartas `.env`, contraseñas, copias de datos reales ni filestore en GitHub. Las pruebas y la demostración trabajan con datos ficticios.

## Comandos habituales

Desde la raíz del repositorio:

```bash
python3 scripts/static_check.py
python3 -m unittest discover -s scripts/tests -v
bash scripts/dev.sh test tradeops_phase1_test
bash scripts/dev.sh logs
bash scripts/dev.sh stop
```

`test` debe apuntar a una base de pruebas dedicada, nunca a una base productiva. `demo` solo acepta bases cuyo nombre termina en `_demo` y necesita `TRADEOPS_DEMO_PASSWORD`. `init` también restablece el administrador y no debe confundirse con `upgrade`.

Para usar los addons con una instalación desde fuente, conserva tu `odoo.conf` privado y añade la ruta absoluta `TradeOps_360/custom_addons` a `addons_path`. Instala o actualiza los cinco addons de acuerdo con el estado de tu base. El ensayo reproducible automatizado de esta rama usa Docker; no supone que se haya modificado o validado remotamente tu computadora.

## Antes de actualizar

Detén escrituras y procesos externos que puedan cambiar la base o adjuntos. Registra el commit actualmente instalado. No ejecutes dos procesos de instalación/actualización contra la misma base.

```bash
BACKUP="backups/$(date -u +%Y%m%dT%H%M%SZ)-tradeops_phase1_demo"
bash scripts/dev.sh backup tradeops_phase1_demo "$BACKUP"
bash scripts/dev.sh upgrade tradeops_phase1_demo
```

El backup detiene el servicio Odoo del Compose, conserva `database.dump`, `filestore.tar.gz`, nombre de base, revisión de código, Compose y sumas SHA-256. El servicio queda detenido. Para esta demostración es un punto consistente porque no hay otros escritores; en un despliegue real deben detenerse también los externos.

Comprueba el log, documentos, enlaces, costos, estados y acceso por roles antes de volver a iniciar. Los registros heredados marcados para revisión no equivalen a mercancía recibida; conserva su evidencia y sigue la revisión funcional. Consulta la [ADR 014](decisions/014-upgrade-and-legacy-evidence.md).

## Restaurar sin sobrescribir el origen

```bash
bash scripts/dev.sh restore tradeops_phase1_restore "$BACKUP"
ODOO_DB=tradeops_phase1_restore bash scripts/dev.sh up
```

El destino debe ser una base NUEVA y diferente del origen. Se verifican checksums y rutas del archivo de filestore; la restauración no elimina ni sobrescribe otra base. Usa la revisión indicada en `code-revision.txt` antes de abrirla. Revertir únicamente Git no revierte el esquema.

En datos procedentes de producción, un ensayo exige además neutralizar correo, cron e integraciones antes de habilitar la copia; esta guía y CI no autorizan usar datos productivos sin ese tratamiento.

## Qué ejecuta CI

| Etapa | Evidencia |
| --- | --- |
| Pruebas rápidas del wrapper y validador | `tooling-tests.log` |
| Estructura Python/XML/manifests/ACL | `static.log` |
| Instalación y pruebas Odoo | `install.log` |
| Escenario integral con usuarios normales | `acceptance.log`, `acceptance-manifest.json` |
| Conversión concurrente en dos transacciones | `concurrency.log`, `concurrency.json` |
| Upgrade sobre datos actuales y desde baseline anterior | `after-upgrade.log`, `legacy-verify.log`, `legacy-upgrade.json` |
| Restauración con verificación de adjunto | `restore.log`, `verified-tradeops_ci_restore.json` |
| Navegador y PDF | `ui-smoke.json`, capturas `ui-*.png`, `import-summary.pdf` |
| Inicio y recuperación usando los comandos documentados | `compose-*.log`, `compose-restore.json` |
| Cierre automatizado de la misma revisión | `final-result.json`, `runtime.txt`, `source.tar.gz` |

El artefacto `phase-1-evidence` se conserva 14 días en Actions. Descárgalo y archiva la evidencia necesaria antes de que expire; no confundas un enlace vencido con una nueva ejecución.

`scripts/validate_evidence.py .ci --full` rechaza fallos, ausencia de evidencia, tests definidos pero no ejecutados y una revisión diferente de `GITHUB_SHA`. Un JSON de pruebas unitarias del validador no es evidencia de Odoo: esos fixtures solo comprueban que el validador detecta errores.

## Diagnóstico del fallo corregido

`odoo server: error: unrecognized parameters: 'shell'` ocurría porque el wrapper generaba `odoo -c ... shell`. No se solucionó quitando la recuperación del workflow: se corrigió el despacho y se añadieron pruebas. Ver [el registro de aprendizaje](learning/phase-1-cli-recovery.md).

Si falla una fase, conserva logs y no declares completadas las siguientes por haber pasado en otro commit. No uses `docker compose down -v`, borrados de bases ni reseteos del repositorio para ocultar el problema.
