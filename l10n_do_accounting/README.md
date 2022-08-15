
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

#### Compañía

El primer paso para la emisión de facturas fiscales dominicanas es configurar correctamente la compañía. Para esto debe editar o crear una compañía colocando todos los datos generales, principalmente el país y el RNC.

<colocar captura de pantalla aqui>

#### Plan contable

Para un correcto uso de la localización dominicana, debemos asegurarnos de configurar el Catálogo de Cuentas Dominicano (NIIF) en nuestra compañía. Para esto nos dirigimos a Facturación > Configuración > Configuración y colocampos el plan contable.

<colocar captura de pantalla aqui>

#### Diarios

Una vez configurado el plan contable correcto, Odoo nos crea de manera automática todo el catálogo de cuentas, impuestos y diarios. Debemos asegurar que configurar nuestros diarios fiscales de Ventas y Compras. Para esto nos dirigmos a Facturación > Configuración > Diarios. Es desde esta vista también que configurarémos nuestras secuencias de comprobantes.

<colocar captura de pantalla aqui (ventas y compras)>



## Cómo usar

#### Facturas de ventas

<insertar gif>

#### Facturas de compras

<insertar gif>

#### Comprobantes de Compras, Gastos Menores y Pagos al Exterior

<insertar gif>

## Dependencias

- **l10n_do** (Dominican Republic - Accounting) de Odoo
## Créditos

### Autores

- [José López](https://github.com/jlopezg)
- [Gustavo Valverde](https://github.com/gustavovalverde)

### Mantenido por

Este módulo es mantenido por INDEXA Inc.

<insertar logo de indexa>
