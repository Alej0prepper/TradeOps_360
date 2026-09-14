# Primera fase: objetivos y trazabilidad

Este documento conserva los 22 objetivos y sus criterios de aceptación del plan aprobado. El [contrato funcional](functional-spec.md) desarrolla las reglas; el [sprint autorizado](sprint-functional.md) fija el alcance.

## Cómo interpretar el estado

**Diseñado** significa que la regla está documentada; **implementado**, que existe código; **verificado automáticamente**, que hay evidencia satisfactoria del mismo commit; **demostrado**, que alguien ejecutó y explicó el caso de uso. No son estados intercambiables.

La corrección de arranque `710fa642803069f98503466e629509692f0d2be6` pasó el workflow **34729198813**, incluidos 45 tests de Odoo y la restauración Docker. Es un antecedente, no un certificado de revisiones posteriores. Los cambios nuevos deben volver a pasar toda la validación.

Para la versión que se entregue, abrir su ejecución de GitHub Actions, comprobar `head_sha`, todos los pasos y `phase-1-evidence/data/evidence/final-result.json`. El campo `source_revision` identifica la revisión; `missing_model_tests` debe ser cero. No reutilizar resultados de otro commit ni presentar los tests sintéticos del verificador como pruebas de Odoo.

## Objetivos y criterios

### F1-01. Documentar el alcance y las reglas de la primera fase

**Terminado cuando:** existe un documento funcional con un ejemplo completo y no quedan decisiones esenciales escondidas detrás de expresiones como “después vemos cómo funciona”.

**Implementación/evidencia:** `docs/functional-spec.md`, `docs/demo-guide.md`. Reglas explícitas y límites contables/comerciales.

### F1-02. Hacer reproducible el entorno de desarrollo

**Terminado cuando:** puedes instalar el proyecto en una base nueva siguiendo únicamente el README, sin configuraciones secretas ni correcciones manuales no documentadas.

**Implementación/evidencia:** `README.md`, `compose.yaml`, `scripts/dev.sh`; CI `ci-compose.sh` instala una base nueva y configura acceso.

### F1-03. Crear la ficha funcional y técnica de cada módulo

**Terminado cuando:** puedes explicar para qué existe cada módulo, qué le corresponde y qué deliberadamente no debe hacer.

**Implementación/evidencia:** `docs/modules/`; plantilla en `docs/templates/module-spec.md`. Revisión documental.

### F1-04. Completar los datos maestros y su mantenimiento

**Terminado cuando:** un usuario autorizado prepara todos los datos de una importación sin recurrir al shell, y los datos históricos no quedan dañados al archivar un catálogo.

**Implementación/evidencia:** `trade_core/models/trade_port.py`, vistas de contactos/puertos; tests de catálogo y permisos. La preparación manual se ensaya con el guion.

### F1-05. Implementar roles y permisos completos

**Terminado cuando:** el flujo funciona con usuarios normales y un usuario sin autorización recibe un rechazo también al intentar ejecutar directamente una operación protegida.

**Implementación/evidencia:** ACL/grupos y guardas de todos los addons; tests de permisos, hijos y acciones directas; fixture con usuarios normales.

### F1-06. Garantizar aislamiento y coherencia por compañía

**Terminado cuando:** las pruebas con dos compañías demuestran que no hay lecturas indebidas ni cruces inválidos, incluidas las líneas e incidencias.

**Implementación/evidencia:** Record rules globales y `check_company`; tests de importaciones/formularios y `test_multicompany.py` de distribución y conciliación.

### F1-07. Implementar numeración y reglas de duplicación y borrado

**Terminado cuando:** no quedan operaciones identificadas únicamente como `New`, duplicar no conserva vínculos o estados finales incorrectos y borrar no destruye evidencia de operaciones ya ejecutadas.

**Implementación/evidencia:** `trade_core/models/common.py`, secuencias y reglas específicas; test de estado inicial/copia segura y protecciones de documentos.

### F1-08. Completar el flujo de estados de importación

**Terminado cuando:** puedes recorrer el flujo desde la interfaz y las pruebas rechazan saltos de estado, cambios indebidos y cancelaciones incompatibles con operaciones físicas ya realizadas.

**Implementación/evidencia:** `trade_import` y `purchase_order.py`; tests de estados, cancelación, protección de fuentes y recepción parcial.

### F1-09. Corregir y cerrar el cálculo de costos operativos

**Terminado cuando:** los gastos asignados cuadran con el total de gastos, los costos de las líneas cuadran con la cabecera y los casos límite tienen pruebas.

**Implementación/evidencia:** Tests de prorrateo, redondeo y recomputación; aceptación con compra 1 600, gastos 160 y total operativo 1 760.

### F1-10. Conectar la importación con compras y recepciones estándar

**Terminado cuando:** una importación de diez unidades puede recibir seis y después cuatro, conservar ambas recepciones y completarse solo cuando se satisface la regla de cierre acordada. Una recepción cancelada no cuenta como mercancía recibida.

**Implementación/evidencia:** Tests de recepción 6+4 y lotes; aceptación multirreceptora con productos trazados. Inventario estándar mantiene el stock.

### F1-11. Completar el ciclo de vida y las validaciones de preventa

**Terminado cuando:** una preventa no conserva productos incompatibles después de una modificación y no puede confirmarse vacía ni alterarse indebidamente después de convertirse.

**Implementación/evidencia:** `test_trade_presale.py`, `test_forms.py`; incluye cambios de cabecera, elegibilidad y protección tras conversión.

### F1-12. Implementar visibilidad del sobrecompromiso comercial

**Terminado cuando:** el usuario detecta claramente que ha comprometido más mercancía de la prevista y los cálculos se actualizan al confirmar, cancelar o convertir preventas.

**Implementación/evidencia:** `trade_presale/models/trade_import.py`; test de advertencia y demanda contada una sola vez.

### F1-13. Cerrar la conversión a venta estándar

**Terminado cuando:** la conversión se ejecuta una sola vez, un fallo no deja registros parciales y el presupuesto puede continuar por el proceso estándar de venta y entrega.

**Implementación/evidencia:** Tests de conversión más `scripts/concurrency.py`, dos transacciones independientes, un presupuesto. Resultado `concurrency.json`.

### F1-14. Corregir el seguimiento de entregas

**Terminado cuando:** una reserva no aparece como entrega, seis unidades entregadas de diez dejan cuatro pendientes, la siguiente entrega actualiza el resultado y una devolución se refleja según la política documentada.

**Implementación/evidencia:** Tests de reserva, entregas parciales, unidades mixtas y devolución que reabre distribución.

### F1-15. Completar el registro y seguimiento de incidencias

**Terminado cuando:** un operador registra una incidencia, un responsable la resuelve y ambos pasos quedan trazados sin alterar indebidamente la entrega.

**Implementación/evidencia:** Tests de descripción, resolución por Responsable, inmutabilidad y compañía; aceptación registra y resuelve sin mover stock artificialmente.

### F1-16. Definir y proteger la conciliación comercial

**Terminado cuando:** no se mezclan compañías, monedas o proveedores incompatibles; una conciliación confirmada está protegida; y una corrección conserva trazabilidad. El documento no se presenta como prueba de pago ni como saldo contable si no lo es.

**Implementación/evidencia:** Tests de procedencia, compañía/moneda, unicidad, snapshot y corrección/replay; total 2 000 y ajuste −50.

### F1-17. Crear una suite de regresión de la primera fase

**Terminado cuando:** cada regla crítica tiene evidencia automatizada pertinente y puedes explicar qué protege cada grupo de pruebas. No basta con contar tests.

**Implementación/evidencia:** Tests de los cinco addons; el verificador exige la ejecución identificable de todos los métodos del source, no solo un total.

### F1-18. Automatizar la validación del repositorio

**Terminado cuando:** una entrega defectuosa hace fallar la validación y un resultado satisfactorio acredita que realmente se instalaron los módulos y se ejecutaron las pruebas previstas.

**Implementación/evidencia:** `.github/workflows/phase-1.yml`; instala Odoo, ejecuta pruebas y conserva resultados. Tests del propio verificador rechazan evidencia incompleta.

### F1-19. Completar la experiencia de usuario y un resumen operativo

**Terminado cuando:** otra persona puede ejecutar el caso principal con instrucciones breves y obtener un resumen comprensible sin conocer el código ni usar el shell.

**Implementación/evidencia:** `scripts/ui-smoke.cjs` abre seis formularios, comprueba consulta y genera PDF; screenshots y resumen en artefacto. Uso independiente por otra persona: pendiente de registrar, no demostrado por este smoke.

### F1-20. Verificar actualización, respaldo y restauración

**Terminado cuando:** has ejecutado el procedimiento, no solo escrito una lista de comandos, y puedes demostrar que recuperas un estado utilizable.

**Implementación/evidencia:** Actualización actual y desde `b72cf69`, dos rutas de restauración, verificación de documentos y SHA-256 de adjunto. Resultados `legacy-upgrade.json`, `verified-*.json`, `compose-restore.json`.

### F1-21. Convertir el repositorio en una referencia de aprendizaje

**Terminado cuando:** puedes volver a una funcionalidad y reconstruir por qué existe y cómo se verifica, sin tener que releer todo el historial del chat.

**Implementación/evidencia:** README, arquitectura, fichas, plantilla, decisiones, aprendizaje, operación y trazabilidad. Revisión de enlaces automatizada.

### F1-22. Ejecutar la demostración final y defender el desarrollo

**Terminado cuando:** no solo puedes enseñar pantallas; puedes explicar cómo funciona el proyecto, cómo detectarías un fallo y cómo entregarías un cambio sin romper lo anterior.

**Implementación/evidencia:** Caso automático en `acceptance.py`, guion en `docs/demo-guide.md`, ejercicio de cambio/regresión. La ejecución manual y defensa personal de Alejandro se registran allí; no están certificadas por CI.

## Cierre del sprint

Los objetivos técnicos cuentan con implementación y comprobaciones; su verificación depende del resultado completo para la revisión elegida. **F1-19 conserva una parte de usabilidad por otra persona y F1-22 una defensa personal que deben registrarse, no atribuirse al agente.**

El caso de aceptación incluye varios productos y gastos, preventa antes del cierre de recepción, recepción parcial/final, presupuesto, venta, entrega parcial, incidencia, devolución, conciliación, aislamiento entre compañías, actualización y restauración. La [guía de demostración](demo-guide.md) añade el ensayo manual, la localización del código y un cambio controlado con regresión.

No se amplía esta fase con API externa, pagos propios, valoración contable personalizada, FX, flota avanzada o una biblioteca de dashboards. El costo es operativo y la conciliación comercial. **La fase solo se declara cerrada cuando los 22 criterios se aceptan sobre una misma versión.**
