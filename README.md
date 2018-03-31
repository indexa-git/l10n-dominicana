[![Waffle.io - Columns and their card count](https://badge.waffle.io/odoo-dominicana/l10n-dominicana.svg?columns=all)](https://waffle.io/odoo-dominicana/l10n-dominicana)

[![Throughput Graph](https://graphs.waffle.io/odoo-dominicana/l10n-dominicana/throughput.svg)](https://waffle.io/odoo-dominicana/l10n-dominicana/metrics/throughput)

# Localización RD para Facturación Fiscal

Este repositorio consolida los módulos utilizados para poder realizar facturación en República Dominicana desde los módulos de Ventas, Contable y Punto de Ventas.

Principalmente se enfoca en la gestión de los Números de Comprobantes Fiscal (**NCF**) y facilita ciertas funcionalidades para el uso de los mismos como:
- Secuencias **Preconfiguradas** para manejo de todos los NCF
   - Facturas con Valor Fiscal (para Ventas)
   - Facturas para Consumidores Finales
   - Gubernamentales
   - Notas de Débito y Crédito
   - Registro de Ingreso Único
   - Registro de Proveedores Informales
   - Registro de Gastos Menores

- Validación en **tiempo real** de comprobantes
	- Estructura correcta del NCF digitado
	- Validación de relación **NCF-RNC** con WebService de DGII

- Consulta de **tasas de banco** en tiempo real
	- Actualización diaria de tasa USD desde el Banco Central
	- Importador de Archivo de Tasas del Banco Central para generación de histórico

- Creación de contactos por **RNC** o **Cédula**
	- Consulta con el WebService de DGII

- Emisión de Facturas Fiscales desde el **Punto de Venta**
	- **WIP**: compatibilidad con impresoras fiscales

## Contribuciones

Antes de hacer una contribución al repositorio a través de un PR, les recomendamos pasar por el [historial de commits de Odoo](https://github.com/odoo/odoo/commits/11.0) donde podrán visualizar el esquema el cual seguirá este repositorio.

También, antes de cualquier publicación deben leer la [guía de Contribución de Odoo](https://github.com/odoo/odoo/wiki/Contributing) que es la base de nuestras políticas de contribución.

> Antes de poder hacer una contribución, si es la primera que realizas, debes crear un **issue** explicando el problema e indicando que harás un **PR**.
