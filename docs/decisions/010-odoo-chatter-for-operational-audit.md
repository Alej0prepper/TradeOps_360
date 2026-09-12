# Decision 010: reutilizar Chatter para la trazabilidad operacional

TradeOps integra los modelos operacionales con `mail.thread` en vez de crear
tablas propias para mensajes, notificaciones o auditoría. Importaciones y
distribuciones añaden también `mail.activity.mixin`, lo que permite asignar
actividades estándar cuando exista una política de responsables.

Los cambios de estado relevantes usan `tracking=True`; las acciones de negocio
que ya existen publican un mensaje breve en el Chatter. No se programa una
actividad automáticamente porque el proyecto todavía no define responsables ni
transiciones de importación. Tampoco se implementa una API externa ni un
dashboard: ambos son escenarios conceptuales de la clase, no una integración o
reporte concreto especificado para este punto.
