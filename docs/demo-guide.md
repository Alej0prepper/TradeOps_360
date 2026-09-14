# Demostración de aceptación y defensa de TradeOps 360

## Dos evidencias distintas

`scripts/acceptance.py` ejecuta el flujo por ORM usando usuarios normales y deja datos ficticios persistidos; `scripts/ui-smoke.cjs` abre documentos en un navegador real y comprueba la generación del PDF. Eso demuestra comportamiento automatizado, **no que Alejandro haya ejecutado personalmente todos los pasos ni defendido el diseño**.

Puedes estudiar la base precargada con `dev.sh demo` o ejecutar el siguiente recorrido manual en otra base limpia. No mezcles sus registros con los de CI ni marques una aceptación sin identificar el commit.

## Datos del caso

Usa una compañía A y su moneda, un proveedor, un cliente, dos puertos diferentes y un almacén de A. El responsable prepara los puertos desde TradeOps → Configuration → Ports; contactos, productos, almacén y lista de precios se mantienen en sus aplicaciones estándar.

| Producto | Unidades previstas | Precio de compra | Precio de venta |
| --- | --- | --- | --- |
| A, almacenable | 10 | 100 | 125 |
| B, almacenable y con lote | 2 | 300 | 375 |

Registra 160 de flete. Compra total: 1.600; gastos asignados: 100 a A y 60 a B; costo operativo: 1.760. Costos unitarios: A = 110 y B = 330. Venta sin impuestos: 2.000; ajuste comercial posterior de −50: total ajustado 1.950. Configura los impuestos del caso para que no confundan los subtotales; no presentes estos importes como contabilidad.

## Recorrido por la interfaz

1. **Operador:** crea importación con cliente, proveedor, almacén, puertos, productos y flete. Revisa costos y pulsa **Submit for Review**.
2. **Responsable:** pulsa **Validate / Create RFQ**, abre la compra vinculada y comprueba cantidades/procedencia. Pulsa **Confirm Purchase / In Transit**.
3. **Operador:** crea preventa sobre esa importación, elige su lista de precios, introduce las dos líneas con precios de venta y pulsa **Confirm Commitment**. Prueba **Create Quotation** antes de terminar las recepciones: debe rechazarse sin crear presupuesto.
4. **Operador:** desde **Receive Goods** recibe A = 6 y B = 1. Asigna un lote al producto B y crea el pendiente estándar. Debe quedar **Partially Received**. Recibe después A = 4 y B = 1: debe quedar **Completed**, conservando ambas recepciones.
5. **Operador:** convierte la preventa mediante **Create Quotation**; abre **Quotation** y confirma por Ventas. La repetición no debe crear otra venta; la prueba concurrente demuestra el caso simultáneo.
6. **Operador:** crea distribución para esa venta y pulsa **Start Distribution**. Una reserva todavía muestra cero entregado. Valida la primera entrega A = 6 y B = 1; comprueba pendientes A = 4 y B = 1.
7. **Operador:** registra **Report Incident**, tipo Documentation Problem, con explicación. Completa la entrega pendiente. **Responsable:** abre la incidencia, escribe resolución, pulsa **Resolve Incident** y después **Close Distribution**.
8. **Operador:** devuelve dos unidades de A mediante Inventario, actualizando la cantidad entregada según la política estándar del caso. Comprueba entrega neta A = 8, pendiente = 2 y reapertura de distribución. Desde la devolución recibida, usa la acción estándar de retorno para generar la reentrega de esas dos unidades; valida la salida actualizando cantidades. Comprueba pendiente cero y vuelve a cerrar la distribución. Este es el mismo recorrido de ida y vuelta que verifica la fixture.
9. **Operador:** crea conciliación para el proveedor y selecciona las líneas de la venta. **Responsable:** pulsa **Confirm Statement**; registra −50 con motivo usando **Record Adjustment**. El subtotal original sigue siendo 2.000 y el ajustado 1.950.
10. Imprime el resumen de importación y abre compras, recepciones, presupuesto, entregas e incidencias vinculadas. Comprueba usuarios, fechas, resolución y mensajes de Chatter.

En una preventa adicional, compromete más de lo previsto para mostrar la advertencia y luego cancélala. No la llames reserva. Con un usuario Consulta, verifica que no aparecen acciones de modificación; las pruebas de servidor demuestran además el rechazo directo. Con un usuario exclusivo de B, confirma que no puede consultar los documentos de A.

## Defender el desarrollo

Explica estas decisiones señalando código y pruebas, no solo pantallas:

- Por qué una validación de importación crea `purchase.order` y no aumenta existencias.
- Por qué ocultar un botón no sustituye ACL, reglas por compañía ni validación del método.
- Cómo bloqueo de filas, restricción única y reintento evitan dos presupuestos.
- Por qué una conciliación confirmada necesita snapshots y ajustes separados.
- Por qué un backup debe recuperar código, base y filestore juntos.

El arreglo del wrapper es un ejemplo de cambio controlado: revisa su causa, `scripts/odoo-entrypoint.py`, `scripts/tests/test_odoo_entrypoint.py` y el ensayo Compose. Ejecuta:

```bash
python3 -m unittest discover -s scripts/tests -v
bash scripts/dev.sh test tradeops_phase1_test
```

## Acta de aceptación personal

Completa al realizar la sesión; no se rellena automáticamente:

| Dato | Resultado real |
| --- | --- |
| Commit y run de CI | Pendiente de registrar en la sesión |
| Persona que ejecuta / persona que revisa | Pendiente |
| Recorrido completo desde interfaz | Pendiente |
| Rechazo por permisos y por negocio mostrado | Pendiente |
| Decisión explicada y test localizado | Pendiente |
| Cambio controlado y regresión explicados | Pendiente |
| Observaciones y aceptación | Pendiente |

Esta acta cierra el componente humano de F1-22 y confirma la usabilidad de F1-19. CI no certifica conocimientos ni una autorización empresarial para producción.
