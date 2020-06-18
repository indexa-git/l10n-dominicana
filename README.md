[![License: AGPL-3](https://img.shields.io/badge/licence-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0.html)
![Unit Tests](https://github.com/odoo-dominicana/l10n-dominicana/workflows/Unit%20Tests/badge.svg)
![Linting](https://github.com/odoo-dominicana/l10n-dominicana/workflows/Linting/badge.svg)
[![codecov](https://codecov.io/gh/odoo-dominicana/l10n-dominicana/branch/11.0/graph/badge.svg)](https://codecov.io/gh/odoo-dominicana/l10n-dominicana)

# Localización Dominicana

Este repositorio consolida los módulos utilizados para poder realizar facturación en República Dominicana desde los módulos de Ventas, Contable y Punto de Ventas.

En esta versión están disponibles los siguientes módulos:

- [**ncf_manager**](https://github.com/dixgrake/l10n-dominicana/blob/11.0/docs/ncf_manager.rst): Este módulo agrega funcionalidades para manejar numero de comprobante fiscal NCF.

        - Secuencias Preconfiguradas para manejo de todos los NCF.
        - Validación de RNC y Cédula.
        - Validación de Estructura NCF y e-CF.

- [**ncf_pos**](https://github.com/dixgrake/l10n-dominicana/blob/11.0/docs/ncf_pos.rst): Incorpora funcionalidades de facturación con NCF al punto de venta.
      
        - WIP: compatibilidad con impresoras fiscales
  
- [**ncf_sale**](https://github.com/dixgrake/l10n-dominicana/blob/11.0/docs/ncf_sale.rst): Este módulo extiende la funcionalidad del ``ncf_manager`` hacia ventas, para realizar algunas validaciones antes de crear la factura. 

- [**ncf_purchase**](https://github.com/dixgrake/l10n-dominicana/blob/11.0/docs/ncf_purchase.rst): Este módulo extiende la funcionalidad del ``ncf_manager`` hacia compras, Se agrego un nuevo campo *Diario de Compras* en proveedores si este campo está configurado, las facturas generadas para estos proveedores toman este diario de manera predeterminada.
          
- [**ncf_invoice_template**](https://github.com/dixgrake/l10n-dominicana/blob/11.0/docs/ncf_invoice_template.rst): Este módulo sobre escribe el formato de las facturas para adaptarlo a la Norma General 06-2018 de la DGII.


## Contribuciones

Antes de hacer una contribución al repositorio a través de un PR, les recomendamos pasar por el [historial de commits de Odoo](https://github.com/odoo/odoo/commits/11.0) donde podrán visualizar el esquema el cual seguirá este repositorio.

También, antes de cualquier publicación deben leer la [guía de Contribución de OCA](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst) que es la base de nuestras políticas de contribución.

> Antes de poder hacer una contribución, si es la primera que realizas, debes crear un **issue** explicando el problema e indicando que harás un **PR**.
