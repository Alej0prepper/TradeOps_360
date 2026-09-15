# Resumen funcional de TradeOps 360

## Objetivo

Este documento describe, desde la perspectiva de un usuario normal de Odoo, cómo comprobar manualmente desde frontend el flujo funcional principal de la fase 1 de TradeOps 360.

El objetivo no es revisar código ni ejecutar comandos internos de Odoo, sino validar que una persona pueda recorrer el proceso completo desde la interfaz: configurar datos maestros, registrar una importación, calcular costos operativos, gestionar preventas, recibir mercancía, convertir una preventa en venta, distribuir productos, registrar incidencias, cerrar una conciliación comercial y comprobar permisos y aislamiento multicompañía.

El flujo validado es:

```text
Datos maestros
   ↓
Importación
   ↓
Costos operativos
   ↓
Revisión
   ↓
Compra
   ↓
Preventa
   ↓
Recepción parcial
   ↓
Recepción completa
   ↓
Presupuesto
   ↓
Venta
   ↓
Distribución
   ↓
Entrega parcial
   ↓
Incidencia
   ↓
Entrega completa
   ↓
Resolución
   ↓
Conciliación comercial
   ↓
Ajuste comercial
   ↓
Permisos
   ↓
Multicompañía
   ↓
Reporte y trazabilidad
```

---

# 1. Requisitos previos

Antes de empezar, la base debe tener instalados y actualizados los módulos de TradeOps 360 y debe existir al menos una compañía, un almacén y usuarios con los perfiles necesarios.

Los perfiles que se utilizan durante la prueba son:

| Perfil | Uso principal |
| --- | --- |
| Operador | Crear y ejecutar operaciones normales de TradeOps |
| Responsable | Validar operaciones, resolver incidencias y cerrar documentos |
| Consulta | Ver documentos sin modificarlos |
| Usuario de otra compañía | Probar aislamiento multicompañía |

El servidor debe estar arrancado y debe ser posible entrar a Odoo con un usuario normal.

---

# 2. Comprobar que TradeOps está disponible

Entrar en Odoo y abrir la aplicación **TradeOps**.

Comprobar que aparecen los menús funcionales principales, entre ellos:

- Imports
- Presales
- Configuration
- Distributions
- Incidents
- Commercial Reconciliations

Resultado esperado: el usuario autorizado puede entrar en TradeOps y navegar por sus menús.

---

# 3. Crear los puertos

Con un usuario Responsable ir a:

**TradeOps → Configuration → Ports**

Crear:

### Puerto de origen

- Name: `Puerto Origen Prueba`
- Code: `ORI01`

### Puerto de destino

- Name: `Puerto Destino Prueba`
- Code: `DES01`

Guardar ambos.

Resultado esperado: los puertos quedan disponibles para utilizarlos en nuevas importaciones.

---

# 4. Crear proveedor y cliente

Crear el proveedor desde Compras para asegurarse de que Odoo lo reconozca correctamente como proveedor:

**Purchase → Vendors → New**

- Name: `Proveedor Prueba TradeOps`

Crear también un cliente:

- Name: `Cliente Prueba TradeOps`

Guardar ambos.

Resultado esperado: ambos contactos pueden seleccionarse posteriormente desde TradeOps.

---

# 5. Crear los productos

Crear dos productos almacenables.

## Producto A

- Name: `Producto A TradeOps`
- Product Type: Storable Product
- Unit of Measure: Units
- Sales Price: 125
- Tracking: No Tracking

## Producto B

- Name: `Producto B TradeOps`
- Product Type: Storable Product
- Unit of Measure: Units
- Sales Price: 375
- Tracking: By Lots

Si no aparece el campo Tracking, activar primero:

**Inventory → Configuration → Settings → Lots & Serial Numbers**

Resultado esperado: ambos productos son almacenables y el Producto B exige lote durante las operaciones de inventario.

---

# 6. Crear la importación

Ir a:

**TradeOps → Imports → New**

Completar:

| Campo | Valor |
| --- | --- |
| Supplier | Proveedor Prueba TradeOps |
| Customer | Cliente Prueba TradeOps |
| Warehouse | Almacén principal |
| Origin Port | Puerto Origen Prueba |
| Destination Port | Puerto Destino Prueba |
| Reference | PRUEBA-FUNCIONAL-01 |

Si aparece Financier, puede dejarse vacío para esta prueba.

---

# 7. Añadir productos a la importación

En la pestaña **Products** añadir:

| Producto | Quantity | Unit Purchase Price |
| --- | ---: | ---: |
| Producto A TradeOps | 10 | 100 |
| Producto B TradeOps | 2 | 300 |

Resultado esperado:

- Producto A: subtotal de compra = 1000
- Producto B: subtotal de compra = 600
- Purchase Total = 1600

---

# 8. Añadir gastos operativos

Abrir **Operational Expenses** y añadir:

- Expense Type: Freight
- Amount: 160

Guardar.

Resultado esperado:

| Concepto | Valor esperado |
| --- | ---: |
| Purchase Total | 1600 |
| Expense Total | 160 |
| Operational / Landed Total | 1760 |
| Producto A - gasto asignado | 100 |
| Producto A - costo unitario real | 110 |
| Producto B - gasto asignado | 60 |
| Producto B - costo unitario real | 330 |

Esta comprobación valida el reparto proporcional de gastos del caso principal.

---

# 9. Enviar la importación a revisión

Con usuario Operador pulsar:

**Submit for Review**

Resultado esperado:

- Draft → Document Review
- las líneas y gastos dejan de poder editarse normalmente
- el Operador no puede ejecutar la validación reservada al Responsable

---

# 10. Validar la importación y crear la compra

Cambiar a usuario Responsable.

Abrir la importación y pulsar:

**Validate / Create RFQ**

Resultado esperado:

- Document Review → Validated
- se crea una solicitud de compra estándar de Odoo
- aparece el acceso a Purchase

Abrir la compra y comprobar:

- proveedor correcto
- Producto A = 10 × 100
- Producto B = 2 × 300

Volver a la importación y pulsar:

**Confirm Purchase / In Transit**

Resultado esperado:

- Validated → In Transit
- la compra queda confirmada
- todavía no se considera mercancía recibida

---

# 11. Crear una preventa antes de recibir mercancía

Ir a:

**TradeOps → Presales → New**

Seleccionar:

- Import: la importación creada
- Customer: Cliente Prueba TradeOps
- Pricelist: lista de precios de la compañía

Añadir líneas seleccionando primero la línea de importación correspondiente:

| Producto | Quantity | Unit Price |
| --- | ---: | ---: |
| Producto A TradeOps | 10 | 125 |
| Producto B TradeOps | 2 | 375 |

Guardar y pulsar:

**Confirm Commitment**

Resultado esperado:

- Draft → Confirmed

---

# 12. Intentar convertir la preventa antes de recibir

Sin recibir todavía la mercancía, pulsar:

**Create Quotation**

Resultado esperado:

- la operación se rechaza
- la preventa permanece en Confirmed
- no se crea ningún presupuesto

La regla validada es que una preventa no puede convertirse mientras la importación no esté completamente recibida.

---

# 13. Registrar una recepción parcial

Volver a la importación y pulsar:

**Receive Goods**

En la recepción estándar de Inventario procesar únicamente:

| Producto | Cantidad recibida |
| --- | ---: |
| Producto A | 6 |
| Producto B | 1 |

Para Producto B asignar un lote, por ejemplo:

`LOTE-B-001`

Validar la recepción y cuando Odoo pregunte qué hacer con lo pendiente, elegir:

**Create Backorder**

Resultado esperado:

- importación en Partially Received
- Producto A recibido = 6
- Producto B recibido = 1
- quedan pendientes A = 4 y B = 1

---

# 14. Completar la recepción

Abrir el backorder de la recepción anterior.

Recibir:

- Producto A = 4
- Producto B = 1

Para Producto B utilizar otro lote:

`LOTE-B-002`

Validar.

Resultado esperado:

- estado de la importación = Completed
- Producto A recibido = 10
- Producto B recibido = 2
- las dos recepciones quedan conservadas y vinculadas

---

# 15. Convertir la preventa en presupuesto

Volver a:

**TradeOps → Presales**

Abrir la preventa confirmada y pulsar:

**Create Quotation**

Resultado esperado:

- Confirmed → Converted
- aparece el acceso Quotation
- se crea un único presupuesto

Comprobar:

| Producto | Cantidad | Precio | Subtotal |
| --- | ---: | ---: | ---: |
| Producto A | 10 | 125 | 1250 |
| Producto B | 2 | 375 | 750 |

Total sin impuestos esperado: **2000**.

Confirmar el presupuesto mediante la acción estándar de Ventas.

Resultado esperado: queda una venta confirmada vinculada a la preventa.

---

# 16. Crear la distribución

Ir a:

**TradeOps → Distributions → New**

Seleccionar la venta confirmada.

Guardar y pulsar:

**Start Distribution**

Resultado esperado:

| Producto | Expected | Delivered | Pending |
| --- | ---: | ---: | ---: |
| Producto A | 10 | 0 | 10 |
| Producto B | 2 | 0 | 2 |

La distribución queda en **Active**.

La reserva estándar de inventario no debe contarse como entrega.

---

# 17. Hacer una entrega parcial

Desde la distribución pulsar:

**Deliveries / Returns**

Procesar:

- Producto A = 6
- Producto B = 1

Para Producto B seleccionar uno de los lotes recibidos, por ejemplo `LOTE-B-001`.

Validar y crear backorder.

Resultado esperado:

| Producto | Delivered | Pending |
| --- | ---: | ---: |
| Producto A | 6 | 4 |
| Producto B | 1 | 1 |

La distribución permanece en Active.

---

# 18. Registrar una incidencia

Desde la distribución activa pulsar:

**Report Incident**

Completar:

- Type: Documentation Problem
- Description: `Documento de entrega pendiente de corrección.`
- Responsible: usuario responsable de la compañía

Guardar.

Resultado esperado:

- incidencia en Open
- la distribución sigue Active
- las cantidades entregadas no cambian

---

# 19. Completar la entrega

Abrir el backorder pendiente y entregar:

- Producto A = 4
- Producto B = 1

Para Producto B utilizar `LOTE-B-002`.

Validar.

Resultado esperado:

| Producto | Delivered | Pending |
| --- | ---: | ---: |
| Producto A | 10 | 0 |
| Producto B | 2 | 0 |

La distribución sigue Active porque todavía existe una incidencia abierta.

---

# 20. Comprobar que no puede cerrarse con una incidencia abierta

Con usuario Responsable pulsar:

**Close Distribution**

Resultado esperado:

- la operación se rechaza
- la distribución sigue Active

La regla validada es que una distribución no puede cerrarse mientras tenga incidencias abiertas, aunque todas las cantidades hayan sido entregadas.

---

# 21. Resolver la incidencia

Ir a:

**TradeOps → Incidents**

Abrir la incidencia e introducir una resolución, por ejemplo:

`Documento corregido y validado con el cliente.`

Pulsar:

**Resolve Incident**

Resultado esperado:

- estado = Resolved
- queda registrada la resolución
- queda registrada la fecha y el usuario que resolvió

---

# 22. Cerrar la distribución

Volver a la distribución y pulsar:

**Close Distribution**

Resultado esperado:

- estado = Closed
- Producto A pending = 0
- Producto B pending = 0

---

# 23. Crear y confirmar la conciliación comercial

Ir a:

**TradeOps → Commercial Reconciliations → New**

Seleccionar:

- Supplier: Proveedor Prueba TradeOps
- Reconciliation Date: fecha actual
- Company: compañía de la operación

En **Sales and Closing Snapshots** añadir las líneas de venta correspondientes:

| Línea | Importe esperado |
| --- | ---: |
| Producto A | 1250 |
| Producto B | 750 |

Guardar.

Resultado esperado:

- estado = Draft
- Total Amount = 2000

Con usuario Responsable pulsar:

**Confirm Statement**

Resultado esperado:

- estado = Confirmed
- se conservan los datos históricos del cierre
- quedan registrados Confirmed At y Confirmed By

La conciliación es comercial, no una conciliación contable ni una prueba de pago.

---

# 24. Registrar un ajuste comercial

En la conciliación confirmada pulsar:

**Record Adjustment**

Introducir:

- Amount: `-50`
- Reason: `Ajuste comercial acordado con proveedor.`

Guardar.

Resultado esperado:

| Concepto | Valor |
| --- | ---: |
| Total original | 2000 |
| Adjustment Total | -50 |
| Net Total | 1950 |

En **Immutable Corrections** debe mantenerse una entrada separada con el importe, motivo, fecha y usuario.

El cierre original de 2000 no debe ser reescrito.

---

# 25. Probar sobrecompromiso de preventa

Crear una segunda preventa sobre la misma importación.

Añadir solo:

- Producto A = 1
- Unit Price = 125

Confirmar.

Como ya existen 10 unidades comprometidas sobre una importación de 10, el total comprometido pasa a 11.

Resultado esperado:

- la preventa se confirma
- aparece una advertencia de overcommit
- la operación no se bloquea
- no se interpreta como una reserva física de stock

Cancelar después esta segunda preventa.

Resultado esperado: el compromiso vuelve a los valores normales.

---

# 26. Probar el usuario Consulta

Iniciar sesión con un usuario que tenga únicamente el rol **Consulta** de TradeOps.

Intentar abrir:

- importación
- preventa
- distribución
- incidencia
- conciliación comercial

Resultado esperado:

- puede leer documentos de su compañía
- no puede crear nuevos documentos operativos
- no puede editar los existentes
- no puede ejecutar acciones como:
  - Submit for Review
  - Validate / Create RFQ
  - Confirm Commitment
  - Start Distribution
  - Resolve Incident
  - Confirm Statement
  - Record Adjustment

Los permisos de Compras, Ventas e Inventario estándar son independientes y pueden restringir también el acceso del usuario Consulta a determinadas pantallas estándar.

---

# 27. Probar aislamiento multicompañía

Iniciar sesión con un usuario que pertenezca únicamente a una segunda compañía.

Primero comprobar que el usuario puede trabajar con registros propios de esa compañía.

Después intentar localizar los documentos creados en la primera compañía:

- importación
- preventa
- distribución
- incidencia
- conciliación

Resultado esperado: no aparecen en los listados.

Copiar además la URL normal de uno de los documentos de la compañía A e intentar abrirla con el usuario de B.

Resultado esperado: el acceso también debe quedar bloqueado.

Los puertos pueden ser globales y algunos contactos o productos pueden estar compartidos. Eso no debe confundirse con acceso a documentos operativos de otra compañía.

---

# 28. Probar el resumen operativo de la importación

Volver a la importación completada.

Usar la opción **Print / Imprimir** y seleccionar el resumen operativo de TradeOps.

Comprobar que el reporte contiene al menos:

- referencia de importación
- proveedor
- cliente
- productos
- cantidades esperadas
- cantidades recibidas
- gastos
- costo operativo total
- documentos relacionados

Valores esperados del caso principal:

| Concepto | Valor |
| --- | ---: |
| Compra total | 1600 |
| Gastos | 160 |
| Costo operativo total | 1760 |
| Producto A recibido | 10 |
| Producto B recibido | 2 |

## Nota sobre wkhtmltopdf

Si al arrancar Odoo aparece:

```text
You need Wkhtmltopdf to print a pdf version of the reports.
```

la generación PDF puede no funcionar en el entorno local. Eso es una dependencia del entorno y no invalida por sí solo el resto del flujo funcional.

---

# 29. Revisar la trazabilidad

Desde la importación principal comprobar la navegación hacia los documentos relacionados:

- Purchase / compra
- Receipts / recepciones
- Presale / preventa
- Quotation / presupuesto
- Sale / venta
- Distribution / distribución
- Incidents / incidencias
- Commercial Reconciliation / conciliación

Resultado esperado: los documentos mantienen relaciones comprensibles y no existen operaciones principales aisladas sin procedencia.

---

# 30. Estado esperado al finalizar

| Elemento | Resultado final esperado |
| --- | --- |
| Importación | Completed |
| Compra | Confirmada |
| Recepciones | Parcial + final completadas |
| Preventa principal | Converted |
| Preventa de sobrecompromiso | Cancelled |
| Venta | Confirmada por 2000 sin impuestos |
| Distribución | Closed |
| Incidencia | Resolved |
| Conciliación | Confirmed |
| Total conciliado original | 2000 |
| Ajuste | -50 |
| Total neto | 1950 |
| Usuario Consulta | Solo lectura |
| Usuario de otra compañía | Sin acceso a documentos de A |
| Reporte | Resumen operativo coherente |

---

# 31. Qué se valida con este recorrido

Este recorrido permite comprobar manualmente desde frontend:

- mantenimiento de datos maestros utilizados por TradeOps
- creación y validación de importaciones
- cálculo de costos operativos
- integración con Compras estándar
- preventas y compromisos comerciales
- advertencia de sobrecompromiso
- recepciones parciales y completas
- productos con seguimiento por lotes
- conversión a presupuesto y venta estándar
- distribución
- entregas parciales
- incidencias y resolución
- cierre de distribución
- conciliación comercial
- ajustes históricos inmutables
- permisos por perfil
- aislamiento multicompañía
- reporte operativo
- trazabilidad entre documentos

Este documento constituye una guía funcional de aceptación manual para la fase 1. No sustituye las pruebas automatizadas, de concurrencia, upgrade o backup/restore del repositorio, pero sí demuestra que el flujo principal puede ser ejecutado por un usuario normal desde la interfaz de Odoo.
