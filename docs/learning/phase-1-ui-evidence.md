# Una prueba verde también puede tener evidencia defectuosa

## Hallazgo real

El run 34730107825 del commit `80763ca` terminó en verde, pero la inspección de `ui-reconciliation.png` mostró una pantalla vacía. Los 47 tests de modelos y la recuperación sí tenían evidencia; el smoke de navegador no demostraba de forma suficiente todos los documentos que afirmaba comprobar.

## Causa

El test reutilizaba una página y navegaba cambiando el fragmento `#id=...`. Odoo sustituye su formulario de manera asíncrona. Esperar solo a `.o_form_view` y comprobar una longitud de texto podía aceptar el formulario anterior mientras se cargaba el siguiente. Una captura posterior podía quedar vacía. Esperar a las fuentes no prueba que haya terminado el cambio de documento.

## Corrección

`scripts/ui-smoke.cjs` abre una página nueva por documento, conservando la sesión del usuario normal. Lee la referencia esperada mediante el ORM HTTP con los permisos de ese usuario y espera el mismo valor en el campo visible del formulario; para la incidencia usa su descripción. Comprueba identidad antes y después de capturar, sin pausas fijas ni permisos elevados.

El usuario Consulta se valida sobre la importación correcta. Se comprueba la ausencia de Refresh Receipts, una acción que sí aparece para Operador en ese mismo estado, para no confundir restricción de estado con restricción de rol.

## Regresión y evidencia

El JSON del navegador incluye modelo, ID, campo, valor esperado, valor observado y verificación de identidad. `scripts/validate_evidence.py` exige los seis documentos del manifiesto y rechaza evidencia sin identidad, un valor de otro documento o un ID incorrecto. Dos tests rápidos protegen estos rechazos. Las fixtures sintéticas de esos tests no se presentan como pruebas del navegador.

El nuevo control rechazó el archivo real `ui-smoke.json` de `80763ca`, aunque ese archivo decía `verified: true`. La corrección debe volver a pasar el workflow completo y sus capturas deben inspeccionarse antes de entregar la nueva revisión.

## Regla de aprendizaje

Una prueba debe esperar un resultado de negocio identificable, no solo la presencia de un contenedor reutilizable. El resultado verde y las capturas deben concordar; cuando no concuerdan, se corrige la prueba y se repite la verificación.
