# Decision 014 - Actualizaciones con evidencia historica y recuperacion consistente

## Contexto

La version anterior permite referencias `New` repetidas, importaciones completadas sin recepciones y conciliaciones sin snapshot del cierre. Una actualizacion no puede transformar esas afirmaciones en hechos que nunca registraron los documentos estandar.

## Decision

Los scripts `migrations/17.0.2.0.0` conservan la referencia original y una copia JSON de la cabecera historica. Las referencias vacias, genericas o repetidas reciben un identificador `LEGACY-...-id`, conservando su valor original. Los registros existentes quedan marcados para revision.

Las relaciones de preventa y venta se recuperan solo cuando la correspondencia por importacion/producto es unica. Colisiones normalizadas de puertos, relaciones ambiguas y monedas historicas distintas de la compania detienen la actualizacion con un diagnostico. No se eliminan filas para hacer pasar restricciones y no se inventan conversiones monetarias.

Los valores de conciliaciones antiguas se capturan al migrar y siguen marcados como historicos por revisar: no se fabrican fecha ni autor de una aprobacion pasada. No se generan recepciones fisicas para justificar un estado antiguo `completed`.

La aceptacion ejecuta tanto una actualizacion de la misma version con datos representativos como la actualizacion desde el commit anterior real. Un ensayo adicional restaura base y filestore en una base nueva y comprueba la identidad de un adjunto mediante SHA-256.

## Consecuencias

Se necesita un backup consistente anterior a cada actualizacion. Ante cualquier fallo se restaura el conjunto codigo/base/filestore; cambiar solo Git no revierte el esquema. Las operaciones historicas incompletas requieren revision funcional explicita. Los datos nuevos siguen el flujo completo y no heredan excepciones silenciosas.
