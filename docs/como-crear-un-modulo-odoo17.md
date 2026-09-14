# Cómo crear un módulo en Odoo 17

Esta guía explica paso a paso cómo se construye un addon de Odoo 17 y relaciona los conceptos con la arquitectura utilizada en TradeOps 360.

## 1. Qué es un módulo

Un módulo o addon es una unidad funcional instalable que puede añadir modelos, extender modelos existentes, crear vistas, menús, permisos, datos, reportes, tests y lógica de negocio.

En TradeOps 360, por ejemplo:

```text
custom_addons/
├── trade_core/
├── trade_import/
├── trade_presale/
├── trade_distribution/
└── trade_reconciliation/
```

Cada carpeta representa un módulo independiente.

## 2. Estructura de un módulo

La estructura mínima es:

```text
mi_modulo/
├── __init__.py
└── __manifest__.py
```

Un módulo real puede tener:

```text
mi_modulo/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── mi_modelo.py
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
├── views/
│   ├── mi_modelo_views.xml
│   └── menus.xml
├── data/
│   └── sequence.xml
├── wizard/
│   ├── __init__.py
│   ├── mi_wizard.py
│   └── mi_wizard_views.xml
├── report/
│   └── mi_report.xml
├── tests/
│   ├── __init__.py
│   └── test_mi_modelo.py
└── static/
    └── description/
        └── icon.png
```

No todas las carpetas son obligatorias. La estructura debe responder a la responsabilidad real del addon.

## 3. `__manifest__.py`

Es la ficha del módulo y permite a Odoo descubrir sus características, dependencias y archivos de datos.

```python
{
    "name": "Trade Import",
    "version": "17.0.1.0.0",
    "category": "Operations",
    "summary": "Manage commercial import operations",
    "author": "Alejandro Alvarez",
    "depends": [
        "base",
        "mail",
        "purchase",
        "stock",
        "trade_core",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/trade_import_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
}
```

### `depends`

Declara qué módulos deben estar disponibles antes de cargar el addon. Odoo utiliza estas dependencias para construir el grafo de carga.

```text
trade_import
├── purchase
├── stock
└── trade_core
```

Las dependencias deben reflejar dependencias técnicas reales, no añadirse arbitrariamente.

### `data`

Indica los XML y CSV que Odoo debe cargar. Que un archivo exista en la carpeta no significa que Odoo vaya a procesarlo automáticamente.

## 4. `__init__.py`

Permite importar el código Python del módulo.

`mi_modulo/__init__.py`:

```python
from . import models
```

`models/__init__.py`:

```python
from . import trade_import
```

Flujo:

```text
Odoo carga el addon
      ↓
__init__.py
      ↓
models
      ↓
models/__init__.py
      ↓
trade_import.py
```

Crear un archivo Python sin importarlo es un error frecuente: el archivo existe, pero el código nunca se carga.

## 5. Crear un modelo

```python
from odoo import fields, models


class TradePort(models.Model):
    _name = "trade.port"
    _description = "Trade Port"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    active = fields.Boolean(default=True)
```

`_name` es el identificador técnico del modelo:

```python
env["trade.port"]
```

`_description` proporciona una descripción legible.

Odoo ORM gestiona la persistencia y campos técnicos como `id`, `create_uid`, `create_date`, `write_uid` y `write_date`.

## 6. Tipos de campos

Ejemplos comunes:

```python
name = fields.Char()
quantity = fields.Float()
date = fields.Date()
active = fields.Boolean()
state = fields.Selection(
    [
        ("draft", "Draft"),
        ("validated", "Validated"),
        ("completed", "Completed"),
    ],
    default="draft",
)
```

## 7. Relaciones entre modelos

### Many2one

```python
supplier_id = fields.Many2one(
    "res.partner",
    string="Supplier",
    required=True,
)
```

Muchas importaciones pueden apuntar al mismo proveedor.

Un principio importante es reutilizar modelos estándar: TradeOps utiliza `res.partner` en lugar de crear un sistema paralelo de proveedores.

### One2many

```python
line_ids = fields.One2many(
    "trade.import.line",
    "import_id",
    string="Products",
)
```

Y en la línea:

```python
import_id = fields.Many2one(
    "trade.import",
    required=True,
    ondelete="cascade",
)
```

Regla mental: el `Many2one` contiene la relación persistida; el `One2many` representa la relación inversa.

### Many2many

```python
tag_ids = fields.Many2many("trade.tag")
```

Se utiliza cuando múltiples registros de ambos modelos pueden relacionarse entre sí.

## 8. Extender modelos estándar

No se debe modificar el código fuente de Odoo para añadir un campo a un modelo estándar.

```python
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    trade_code = fields.Char(string="Trade Code")
```

`_inherit = "res.partner"` extiende el modelo existente. Este patrón permite que TradeOps añada información específica sin reconstruir Contacts.

## 9. Lógica de negocio y estados

Los modelos pueden exponer acciones de dominio:

```python
def action_submit_review(self):
    for record in self:
        if record.state != "draft":
            raise UserError("Only draft imports can be submitted.")
        record.state = "document_review"
```

Esto representa una transición controlada:

```text
Draft
  ↓ Submit for Review
Document Review
```

Los estados deben representar reglas reales del negocio y no simples etiquetas visuales.

## 10. Constraints e invariantes

```python
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TradeImportLine(models.Model):
    _name = "trade.import.line"

    quantity = fields.Float()

    @api.constrains("quantity")
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError("Quantity must be greater than zero.")
```

Las reglas importantes deben protegerse en backend.

Un `readonly` en XML mejora la interfaz, pero no constituye una barrera de seguridad ni una invariante de dominio.

## 11. Vistas

### Form view

```xml
<record id="view_trade_port_form" model="ir.ui.view">
    <field name="name">trade.port.form</field>
    <field name="model">trade.port</field>
    <field name="arch" type="xml">
        <form>
            <sheet>
                <group>
                    <field name="name"/>
                    <field name="code"/>
                    <field name="active"/>
                </group>
            </sheet>
        </form>
    </field>
</record>
```

### List view

```xml
<record id="view_trade_port_tree" model="ir.ui.view">
    <field name="name">trade.port.tree</field>
    <field name="model">trade.port</field>
    <field name="arch" type="xml">
        <tree>
            <field name="name"/>
            <field name="code"/>
            <field name="active"/>
        </tree>
    </field>
</record>
```

El modelo define datos y comportamiento; las vistas determinan cómo se presentan en el cliente Odoo.

## 12. Actions y menús

Una acción conecta la interfaz con un modelo:

```xml
<record id="action_trade_port" model="ir.actions.act_window">
    <field name="name">Ports</field>
    <field name="res_model">trade.port</field>
    <field name="view_mode">tree,form</field>
</record>
```

Luego puede exponerse mediante menús:

```xml
<menuitem id="menu_tradeops_root" name="TradeOps"/>

<menuitem
    id="menu_tradeops_configuration"
    name="Configuration"
    parent="menu_tradeops_root"
/>

<menuitem
    id="menu_trade_port"
    name="Ports"
    parent="menu_tradeops_configuration"
    action="action_trade_port"
/>
```

Flujo conceptual:

```text
TradeOps
  ↓
Configuration
  ↓
Ports
  ↓
action_trade_port
  ↓
trade.port
```

## 13. Seguridad y grupos

Un módulo profesional debe definir quién puede realizar cada operación.

TradeOps utiliza conceptualmente perfiles como:

```text
TradeOps
├── Consulta
├── Operador
└── Responsable
```

Un grupo puede declararse mediante `res.groups` en XML.

## 14. ACL

El archivo habitual es:

```text
security/ir.model.access.csv
```

Ejemplo:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_trade_port_user,trade.port.user,model_trade_port,group_trade_operator,1,1,1,0
```

Los permisos representan:

```text
read
write
create
unlink
```

En el ejemplo, el usuario puede leer, modificar y crear, pero no eliminar.

## 15. Record rules y multicompañía

Las ACL responden si un grupo puede acceder a un modelo. Las record rules restringen a qué registros concretos puede acceder.

Esto es esencial en entornos multicompañía:

```text
Usuario Company A → documentos permitidos de A
Usuario Company B → documentos permitidos de B
```

La presencia de `company_id` por sí sola no sustituye una política de seguridad correctamente definida.

## 16. Campos computed

```python
total = fields.Monetary(compute="_compute_total")

@api.depends("line_ids.subtotal")
def _compute_total(self):
    for record in self:
        record.total = sum(record.line_ids.mapped("subtotal"))
```

`@api.depends` declara las dependencias que permiten a Odoo determinar cuándo recalcular el valor.

## 17. Campos related

```python
currency_id = fields.Many2one(
    related="company_id.currency_id",
)
```

Permiten exponer información siguiendo relaciones existentes sin duplicar manualmente la lógica.

## 18. `onchange`

```python
@api.onchange("supplier_id")
def _onchange_supplier_id(self):
    ...
```

Un `onchange` se utiliza principalmente para UX y comportamiento interactivo del formulario.

Regla importante:

```text
onchange → ayuda de interfaz
constraint/lógica de modelo → integridad real
```

Una regla crítica no debe depender exclusivamente de `onchange`.

## 19. Secuencias

Para numeraciones como:

```text
IMP/2026/0001
IMP/2026/0002
IMP/2026/0003
```

Odoo proporciona `ir.sequence`.

Es preferible utilizar una secuencia a implementar manualmente `último número + 1`, especialmente por problemas de concurrencia.

## 20. Chatter y actividades

Un modelo puede integrar trazabilidad estándar:

```python
class TradeImport(models.Model):
    _name = "trade.import"
    _inherit = ["mail.thread", "mail.activity.mixin"]
```

Un campo puede registrar cambios:

```python
state = fields.Selection(..., tracking=True)
```

Esto permite chatter, mensajes, actividades y seguimiento de operaciones.

## 21. Wizards

Los wizards suelen utilizar `TransientModel` cuando una acción necesita solicitar información temporal:

```python
class TradeIncidentWizard(models.TransientModel):
    _name = "trade.incident.wizard"
```

Ejemplo conceptual:

```text
Report Incident
      ↓
Tipo + descripción + responsable
      ↓
Confirmar
      ↓
trade.delivery.incident
```

El wizard es una interacción temporal; la incidencia resultante sí representa un registro persistente del negocio.

## 22. Tests

Una estructura típica:

```text
tests/
├── __init__.py
└── test_trade_import.py
```

Ejemplo:

```python
from odoo.tests.common import TransactionCase


class TestTradeImport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({
            "name": "Test Supplier",
        })

    def test_create_import(self):
        trade_import = self.env["trade.import"].create({
            "supplier_id": self.partner.id,
        })
        self.assertEqual(trade_import.supplier_id, self.partner)
```

En un proyecto como TradeOps son más valiosas las pruebas de reglas de negocio, por ejemplo:

- ¿puede un Operador ejecutar una acción reservada al Responsable?
- ¿puede Consulta modificar documentos?
- ¿puede Company B leer documentos de Company A?
- ¿puede convertirse dos veces una misma preventa?
- ¿puede cerrarse una distribución con incidencias abiertas?
- ¿una recepción parcial calcula correctamente lo recibido?
- ¿una devolución modifica correctamente la cantidad entregada?

## 23. Instalación

La carpeta del addon debe estar en una ruta declarada en `addons_path`.

En el entorno local de TradeOps se utiliza:

```text
/home/alejo/Github/Odoo/TradeOps_360/custom_addons
```

Un módulo puede instalarse por CLI:

```bash
./odoo-bin \
    -c ../config/odoo.conf \
    -d tradeops_dev \
    -i trade_import
```

`-i` instala el módulo.

## 24. Actualización de un módulo instalado

Después de modificar un addon ya instalado se utiliza normalmente `-u`:

```bash
./odoo-bin \
    -c ../config/odoo.conf \
    -d tradeops_dev \
    -u trade_import
```

Una distinción fundamental es:

```text
Código fuente ≠ estado de la base de datos
```

Cambiar un XML o un modelo en el repositorio no implica automáticamente que la base instalada haya aplicado la modificación.

## 25. Ciclo completo de construcción

```text
1. Definir responsabilidad del módulo
             ↓
2. Crear carpeta
             ↓
3. __manifest__.py
             ↓
4. __init__.py
             ↓
5. Crear modelos
             ↓
6. Relaciones
             ↓
7. Constraints e invariantes
             ↓
8. Lógica y acciones
             ↓
9. Grupos
             ↓
10. ACL
             ↓
11. Record rules
             ↓
12. Vistas
             ↓
13. Actions
             ↓
14. Menús
             ↓
15. Datos y secuencias
             ↓
16. Wizards/reportes si hacen falta
             ↓
17. Tests
             ↓
18. Instalar
             ↓
19. Probar desde frontend
             ↓
20. Upgrade
             ↓
21. Regresión
```

## 26. Diseñar antes de programar

Antes de implementar un addon conviene responder explícitamente:

### ¿Qué responsabilidad tiene?

Ejemplo para `trade_import`: gestionar una operación de importación.

### ¿Qué entidades propias necesita?

```text
trade.import
trade.import.line
trade.import.expense
```

### ¿Qué entidades ya proporciona Odoo?

```text
res.partner
product.product
res.company
stock.warehouse
purchase.order
stock.picking
```

### ¿Qué estados necesita el proceso?

```text
Draft
Document Review
Validated
In Transit
Partially Received
Completed
Cancelled
```

### ¿Quién puede hacer qué?

```text
Consulta
Operador
Responsable
```

### ¿Cuáles son las invariantes?

Por ejemplo:

```text
cantidad > 0
precio >= 0
no completar sin recibir todo
no convertir preventa prematuramente
Company A no accede a documentos Company B
```

### ¿Qué debe delegarse a Odoo?

```text
Compra    → Purchase
Recepción → Inventory
Venta     → Sales
Entrega   → Inventory
Contacto  → Contacts
```

Estas decisiones deben tomarse antes de empezar a crear modelos indiscriminadamente.

## 27. Principio arquitectónico central

Un error frecuente al comenzar con Odoo es pensar: "Necesito una compra, por tanto crearé `trade.purchase`".

Primero debe preguntarse si Odoo ya dispone de un modelo que represente esa responsabilidad y si el addon únicamente necesita extenderlo, relacionarlo u orquestarlo.

TradeOps sigue este enfoque:

```text
                ODOO STANDARD
                     │
      ┌──────────────┼───────────────┐
      ▼              ▼               ▼
purchase.order   stock.picking   sale.order
      ▲              ▲               ▲
      │              │               │
      └──────────────┼───────────────┘
                     │
                TRADEOPS 360
                     │
      ┌──────────────┼───────────────┐
      ▼              ▼               ▼
trade.import    trade.presale   trade.distribution
```

**Odoo proporciona las capacidades ERP genéricas. TradeOps implementa las reglas específicas del negocio.**

Entender esta separación es una de las bases para diseñar addons mantenibles y correctamente integrados con Odoo.