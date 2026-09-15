# Despliegue controlado en servidor compartido

Esta guía despliega la versión actual de TradeOps 360 en un servidor Linux compartido con Docker Compose, proxy inverso y configuración externa al repositorio. Es un patrón de operación inicial; no convierte por sí solo el entorno educativo en una producción aprobada. Antes de empezar deben estar aprobados el dominio, recursos, responsable operativo, ventana de mantenimiento y política de backups.

## Qué se despliega

El repositorio contiene Odoo 17 y PostgreSQL 16 con imágenes fijadas por digest y cinco addons: `trade_core`, `trade_import`, `trade_presale`, `trade_distribution` y `trade_reconciliation`. No define API propia, servicios externos ni correo saliente.

El `compose.yaml` actual es reproducible para desarrollo: Odoo se publica sólo en `127.0.0.1`, PostgreSQL no se publica, `list_db = False`, `proxy_mode = False` y `workers = 0`. Para el servidor compartido mantenemos la base y los volúmenes privados, activamos el modo proxy mediante una configuración externa y no exponemos Odoo directamente a la red.

```text
Usuarios ─HTTPS─> proxy inverso ─loopback─> Odoo
                                              │
                                              ├─ custom_addons (sólo lectura)
                                              ├─ volumen odoo-data (filestore)
                                              └─ red privada Compose ─> PostgreSQL
                                                                          └─ volumen postgres-data
```

## Aprobaciones y preflight

Registra en el ticket de despliegue:

- Responsable funcional, técnico y administrador del host.
- Dominio, certificado TLS, canal de soporte, recursos reservados y ventana.
- SHA o etiqueta inmutable aprobada; no una rama móvil.
- Ubicación externa, cifrada y retenida para backups, además de una fecha para ensayar su restauración.
- Proyecto Docker, base, puerto y dominio exclusivos para este entorno.

El SHA que se publique debe tener la evidencia completa del workflow del mismo commit, incluido `final-result.json`, instalación, migración, restauración y smoke de navegador/PDF. Como mínimo, desde el repositorio validado se ejecuta:

```bash
python3 scripts/static_check.py
python3 -m unittest discover -s scripts/tests -v
bash scripts/dev.sh test tradeops_phase1_test
```

Los tests y CI no sustituyen la aceptación funcional por usuarios ni la aprobación de producción.

## Preparar el host

Estos nombres son un ejemplo; anótalos en el inventario del servidor y usa un usuario Unix dedicado, aquí `tradeops`.

```text
/srv/tradeops-360             clon de código
/etc/tradeops                 configuración del host y secretos
/srv/tradeops-backups         copias temporales antes de enviarlas fuera del host
```

El administrador instala Docker Engine y Docker Compose v2 según la política corporativa. Pertenecer al grupo `docker` ofrece privilegios equivalentes a administración del host; concédelo sólo al usuario de servicio si está autorizado.

```bash
sudo install -d -o tradeops -g tradeops -m 0750 /srv/tradeops-360
sudo install -d -o root -g tradeops -m 0750 /etc/tradeops
sudo install -d -o tradeops -g tradeops -m 0700 /srv/tradeops-backups

git clone https://github.com/Alej0prepper/TradeOps_360.git /srv/tradeops-360
cd /srv/tradeops-360
git fetch --tags origin
git checkout --detach <SHA_APROBADO>
git rev-parse HEAD
```

El último comando debe devolver exactamente el SHA aprobado. No copies el entorno virtual local `odoo17/`: este despliegue usa las imágenes Docker del repositorio.

## Secretos y aislamiento de Compose

Crea `/srv/tradeops-360/.env` con un gestor de secretos o una consola privada. No pongas valores reales en el historial, tickets, logs ni Git.

```dotenv
POSTGRES_PASSWORD=<secreto-aleatorio-y-unico>
ODOO_MASTER_PASSWORD=<secreto-aleatorio-y-unico>
TRADEOPS_ADMIN_PASSWORD=<secreto-aleatorio-de-al-menos-12-caracteres>
TRADEOPS_ADMIN_EMAIL=admin@empresa.example
ODOO_DB=tradeops_prod
ODOO_HTTP_PORT=18070
```

```bash
chmod 600 .env
stat -c '%a %U:%G %n' .env
```

Las tres contraseñas son diferentes. `ODOO_MASTER_PASSWORD` protege operaciones administrativas de Odoo, mientras que `TRADEOPS_ADMIN_PASSWORD` sirve para crear o restablecer el administrador durante `init`. Entrégala por canal seguro y cámbiala tras el primer acceso.

El nombre superior de Compose del repositorio es `tradeops-phase1`. En el servidor compartido se debe reemplazar para que sus contenedores, red y volúmenes no colisionen con otros proyectos. Crea fuera de Git la siguiente sobrescritura.

`/etc/tradeops/odoo-prod.conf`:

```ini
[options]
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
data_dir = /var/lib/odoo
http_interface = 0.0.0.0
http_port = 8069
list_db = False
proxy_mode = True
workers = 0
max_cron_threads = 1
log_level = info
```

`/etc/tradeops/compose.shared-server.yaml`:

```yaml
services:
  db:
    restart: unless-stopped
  odoo:
    restart: unless-stopped
    volumes:
      - /etc/tradeops/odoo-prod.conf:/etc/tradeops/odoo.conf.example:ro
```

`workers = 0` conserva el perfil validado para el primer arranque. No subas workers por una fórmula genérica en un host compartido: antes se deben reservar CPU/RAM, probar carga y revisar límites de Odoo, cron y bus/long-polling del proxy. La política `restart` cubre reinicios y caídas del contenedor, pero no sustituye alertas.

En toda sesión administrativa, y en automatizaciones que llamen a `scripts/dev.sh`, usa estas variables. El script ejecuta `docker compose` internamente y las respeta.

```bash
cd /srv/tradeops-360
export COMPOSE_PROJECT_NAME=tradeops-prod
export COMPOSE_FILE=compose.yaml:/etc/tradeops/compose.shared-server.yaml
docker compose config
```

Revisa el resultado: debe haber un único montaje en `/etc/tradeops/odoo.conf.example`, una base `tradeops_prod`, el puerto `127.0.0.1:18070` y ningún `ports` para PostgreSQL.

## Proxy inverso y TLS

El proxy corporativo es el único componente expuesto. Abre sólo 80/443 según la política; `18070` permanece en loopback. Usa el certificado gestionado por la organización. Este virtual host Nginx es una referencia, con el dominio y rutas de certificados que correspondan:

```nginx
server {
    listen 80;
    server_name tradeops.interno.example;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tradeops.interno.example;

    ssl_certificate     /ruta/gestionada/certificado.pem;
    ssl_certificate_key /ruta/gestionada/clave-privada.pem;
    client_max_body_size 50m;

    location / {
        proxy_pass http://127.0.0.1:18070;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 720s;
        proxy_send_timeout 720s;
        proxy_redirect off;
    }
}
```

Valida y recarga Nginx con el procedimiento de la distribución. No habilites el sitio hasta que Odoo responda localmente. `proxy_mode = True` permite a Odoo usar los encabezados del proxy; no confíes esos encabezados desde Internet sin este proxy delante.

## Primer arranque y aceptación

Con las variables `COMPOSE_*` de la sección anterior exportadas:

```bash
docker compose config --quiet
docker compose pull
bash scripts/dev.sh init tradeops_prod
bash scripts/dev.sh up
docker compose ps
docker compose logs --tail=200 odoo
curl --fail --silent --show-error http://127.0.0.1:18070/web/login -o /dev/null
```

`init` instala los cinco addons y crea o **restablece** el administrador. Sólo se usa sobre una base nueva y vacía; nunca para actualizar una instalación existente. Cambia la contraseña inicial al iniciar sesión y configura en Odoo la URL base HTTPS del dominio publicado.

Antes de abrir DNS o el proxy al resto de usuarios, acepta por HTTPS los flujos con cuentas no administrativas: roles y compañías, importación, compra/recepción, preventa a presupuesto, entrega/incidencia y conciliación. Confirma además que la lista de bases no se muestra, que PostgreSQL no es alcanzable desde el host/red y que los logs no incluyen secretos.

## Operación y backups

Ejecuta siempre desde el directorio y proyecto correctos:

```bash
cd /srv/tradeops-360
export COMPOSE_PROJECT_NAME=tradeops-prod
export COMPOSE_FILE=compose.yaml:/etc/tradeops/compose.shared-server.yaml
docker compose ps
docker compose logs --tail=200 odoo
docker compose logs --tail=200 db
```

Monitoriza disponibilidad HTTPS, espacio libre de host y volúmenes, antigüedad del último backup verificado, reinicios y errores de Odoo/PostgreSQL. Limita el acceso a logs, pues pueden contener datos funcionales.

El backup integrado detiene Odoo y lo deja detenido para obtener una copia consistente. Define una ventana, detén también escritores externos autorizados y almacena la copia fuera de los volúmenes Docker:

```bash
BACKUP=/srv/tradeops-backups/$(date -u +%Y%m%dT%H%M%SZ)-tradeops_prod
bash scripts/dev.sh backup tradeops_prod "$BACKUP"
bash scripts/dev.sh up
```

La carpeta incluye dump de PostgreSQL, filestore, SHA-256, nombre de base, `compose.yaml` y `code-revision.txt`. Envíala cifrada al destino externo pactado y verifica llegada y retención. Ensaya la restauración regularmente en una base aislada; en una copia de datos reales neutraliza correo, cron e integraciones antes de abrirla.

## Actualización y reversión

No actualices desde una rama ni ejecutes actualizaciones paralelas. Prueba primero el SHA nuevo en staging con una copia tratada. En la ventana productiva:

```bash
cd /srv/tradeops-360
export COMPOSE_PROJECT_NAME=tradeops-prod
export COMPOSE_FILE=compose.yaml:/etc/tradeops/compose.shared-server.yaml
BACKUP=/srv/tradeops-backups/$(date -u +%Y%m%dT%H%M%SZ)-tradeops_prod
bash scripts/dev.sh backup tradeops_prod "$BACKUP"
git fetch --tags origin
git checkout --detach <SHA_NUEVO_APROBADO>
bash scripts/dev.sh upgrade tradeops_prod
# Revisar log, documentos, permisos y flujos críticos.
bash scripts/dev.sh up
```

`upgrade` actualiza los cinco módulos y queda detenido para la revisión. Volver sólo al commit anterior no revierte el esquema. Si falla, conserva logs y la base fallida, vuelve al SHA de `code-revision.txt`, restaura el backup en una **base nueva** y cambia `ODOO_DB` a ella antes de arrancar:

```bash
git checkout --detach "$(cat "$BACKUP/code-revision.txt")"
bash scripts/dev.sh restore tradeops_prod_restore_20260915 "$BACKUP"
# Editar .env: ODOO_DB=tradeops_prod_restore_20260915
bash scripts/dev.sh up
```

No borres ni sobrescribas la base afectada para acelerar la recuperación. La copia restaurada no se publica hasta verificar código, adjuntos, documentos, permisos y ausencia de efectos externos.

## Checklist de salida

- SHA y evidencia CI del mismo commit registrados.
- Secretos, configuración externa y backups fuera de Git con permisos correctos.
- Proyecto Compose, dominio, puerto, base y volúmenes exclusivos.
- Odoo en loopback, PostgreSQL sin publicar y proxy HTTPS funcional.
- `proxy_mode = True`, `list_db = False` y filtro de base activos.
- Backup enviado fuera del host y restauración aislada ensayada.
- Aceptación funcional por roles/compañías realizada y URL base HTTPS configurada.
- Dueño operativo, alertas, mantenimiento y rollback conocidos.

Consulta también [Operación, pruebas y recuperación](operations.md) y la [revisión de entrega](release-readiness.md).
