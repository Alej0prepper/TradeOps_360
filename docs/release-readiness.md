# Revisión de entrega de la primera fase

Esta checklist complementa la [operación reproducible](operations.md), los [22 objetivos](phase-1-objectives.md) y la [demostración](demo-guide.md). No convierte un entorno didáctico en un despliegue de producción aprobado.

## Antes de probar
Confirmar la revisión exacta, los digests de Odoo/PostgreSQL y una base de prueba separada. Nunca ejecutar la carga demo sobre datos reales. Ejecutar `python3 scripts/static_check.py` y `python3 -m unittest discover -s scripts/tests -v`.

## Pruebas y evidencia
Ejecutar `bash scripts/dev.sh test tradeops_phase1_test`. Para cerrar la validación técnica, exigir además el workflow completo del mismo commit: pruebas de modelos, concurrencia, aceptación, migración, restauración, navegador/PDF y los comandos Compose documentados. Revisar `final-result.json`, `runtime.txt`, logs y screenshots. Un workflow fallido no es una entrega verificada aunque sus tests anteriores estén verdes.

## Actualización y recuperación
Guardar código/revisión, configuración segura, dump y filestore consistentes; detener escritores. Actualizar una copia representativa, comprobar documentos y relaciones, restaurar en una base nueva y verificar un adjunto. Una vuelta de Git no revierte el esquema. Conservar fuera de Git las copias reales y los secretos.

## Aceptación funcional
Ejecutar el flujo completo con un operador normal y un responsable; incluir rechazos por rol y regla de negocio. Confirmar que las etiquetas distinguen compromiso, stock, costo operativo e importe comercial. Registrar la aceptación de otra persona y la defensa técnica del desarrollador sin atribuirlas a CI.

## Entrega
Solo fusionar o publicar una versión aprobada explícitamente. Este sprint no fusiona `main`, no despliega en producción y no borra bases ni volúmenes para simular recuperación.
