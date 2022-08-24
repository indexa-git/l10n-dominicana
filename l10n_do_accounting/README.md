
# Fiscal Accounting (Rep. Dominicana)

Este módulo implementa la gestión y emisión de comprobantes fiscales para el cumplimento de la norma 06-18 de la Dirección de Impuestos Internos de la República Dominicana.


## Funcionalidades principales

- Configuración de tipos de contribuyentes
- Implementación de tipos de Comprobantes Fiscales
- Gestión de secuencias de Comprobantes Fiscales
- Implementación de campos en facturas de ventas y compras requeridos para la generación de formatos de envío DGII
- Emisión de Notas de Crédito Fiscales
- Implementación de campos básicos para integración con Facturación Electrónica
- Emisión de todos los tipos de comprobantes fiscales de ventas
- Registro de facturas fiscales de compras
- Emisión de Comprobantes de Compras, Gastos Menores y Pagos al Exterior

## Configuración

### Compañía

El primer paso para la emisión de facturas fiscales dominicanas es configurar correctamente la compañía. Para esto debe editar o crear una compañía colocando todos los datos generales, principalmente la razón social, el país y el RNC.

![Company](https://github.com/indexa-git/l10n-dominicana/blob/930786dcadc742855446eeda5f937cd187f2a64c/l10n_do_accounting/static/img/company.png?raw=true)

### Plan contable

Para un correcto uso de la localización dominicana, debemos asegurarnos de configurar el Catálogo de Cuentas Dominicano (NIIF) en nuestra compañía. Para esto nos dirigimos a Facturación > Configuración > Ajustes y establecemos el plan contable.

![Ajustes](https://github.com/indexa-git/l10n-dominicana/blob/69303ca63125d70091260f7784bbc9484ab3ae00/l10n_do_accounting/static/img/ajustes.png?raw=true)

### Diarios

Una vez configurado el plan contable correcto, Odoo nos crea de manera automática todo el catálogo de cuentas, impuestos y diarios. Debemos asegurarnos de configurar nuestros diarios fiscales de Ventas y Compras. Para esto nos dirigmos a Facturación > Configuración > Diarios. Es desde esta vista también que configurarémos nuestras secuencias de comprobantes.

**Nota**: a partir de la versión 14.0 en los diarios no se coloca ni se gestiona la secuencia de comprobante a utilizar; esto debido a cambios implementados por Odoo en la manera en que se obtienen las secuencias en las facturas. Para más detalles técnicos consultar los siguientes commits de Odoo: 

- https://github.com/odoo/odoo/commit/dfd01b8c5c7e1177f37bf199790a0732a61eed78
- https://github.com/odoo/odoo/commit/e8286ce4d9e28c98436a4422621356c76c386d3f

![Diarios](https://raw.githubusercontent.com/indexa-git/l10n-dominicana/abb34dfa73ec3f0ab4904da7d64c292126cf4ec3/l10n_do_accounting/static/img/diario.png)

Para colocar la **primera secuencia (y solo la primera)** de comprobante fiscal para cualquier tipo de documento debemos introducirlo manualmente en la factura:

![Contactos](https://raw.githubusercontent.com/indexa-git/l10n-dominicana/abb34dfa73ec3f0ab4904da7d64c292126cf4ec3/l10n_do_accounting/static/img/primera_factura_ventas.png)


## Cómo usar

### Contactos

Para la creación de facturas fiscales dominicanas, es requerida una correcta configuración de nuestros contactos. Debemos asegurar establecer al menos la razón social, el país, el NIF (número de identificación fiscal o RNC/Cédula) y el tipo de contribuyente. Este último determinará los tipos de comprobantes disponibles para este contacto.

![Contactos](https://raw.githubusercontent.com/indexa-git/l10n-dominicana/1e01f366e81bb16ee207a28710b2a6de5e70bc8b/l10n_do_accounting/static/img/contacto.png)

### Facturas de ventas

![Ventas](https://github.com/indexa-git/l10n-dominicana/blob/dd6bd5e2be661fd24a00e21b5b87a884897cec8b/l10n_do_accounting/static/img/factura_ventas.png)

### Facturas de compras

![Compras](https://github.com/indexa-git/l10n-dominicana/blob/552b2c761987e5de4932ebabad73dd02554dcf1f/l10n_do_accounting/static/img/factura_compras.png)

### Comprobantes de Compras, Gastos Menores y Pagos al Exterior

Los de Comprobantes de Compras, Gastos Menores y Pagos al Exterior son documentos fiscales cuya secuencia de comprobante se genera internamente, por lo cual no puede ser digitada como en las Facturas de Compras comunes.

- **Comprobante de compras**: se debe colocar un proveedor cuyo Tipo de contribuyente sea Cliente de Consumo
- **Gastos Menores**: se debe colocar un proveedor cuyo Tipo de contribuyente sea Cliente de Consumo
- **Pagos al Exterior**: se debe colocar un proveedor cuyo Tipo de contribuyente sea Extranjero

## Dependencias

- **l10n_do** (Dominican Republic - Accounting) de Odoo
- **l10n_latam_invoice_document** (LATAM Document) de Odoo

## Créditos

### Autores

- [José López](https://github.com/jlopezg)
- [Gustavo Valverde](https://github.com/gustavovalverde)

### Mantenido por

Este módulo es mantenido por INDEXA Inc.

