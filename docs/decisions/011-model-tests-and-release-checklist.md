# Decision 011: probar reglas de dominio y liberar mediante staging

Las reglas de TradeOps se verifican cerca del modelo mediante
`TransactionCase`, donde el ORM, las restricciones y las operaciones de
negocio pueden ejecutarse de forma transaccional. Cada addon mantiene sus
pruebas junto al código que protege.

La validación de una entrega no se limita a las pruebas automatizadas. La guía
de release exige una base de prueba limpia, una actualización en staging,
backup de base de datos y filestore, y un smoke test de los flujos críticos.
No se añade configuración de despliegue ni automatización CI porque el
repositorio no define su infraestructura de Odoo.
