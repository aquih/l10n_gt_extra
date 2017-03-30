# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields

class account_invoice(osv.osv):
    _inherit = "account.invoice"

    def _numero_factura(self, cr, uid, ids, field_name, arg, context):
        result = {}

        for factura in self.browse(cr, uid, ids):
            if factura.state != "cancel":
                result[factura.id] = factura.number
            else:
                result[factura.id] = factura.internal_number

        return result

    def _validar_factura_proveedor(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)

        if not obj.supplier_invoice_number:
            return True

        facturas = self.search(cr, uid, [('supplier_invoice_number','=',obj.supplier_invoice_number), ('partner_id','=',obj.partner_id.id), ('type','=','in_invoice')])
        if len(facturas) > 1:
            return False
        else:
            return True

    _constraints = [
        (_validar_factura_proveedor, 'La factura está duplicada', ['supplier_invoice_number']),
    ]

    _columns = {
        'tipo_gasto': fields.selection((('compra', 'Compra/Bien'), ('servicio', 'Servicio'), ('importacion', 'Importación/Exportación'), ('combustible', 'Combustible'), ('mixto', 'Mixto')), 'Tipo de Gasto', required=True),
        'pequenio_contribuyente': fields.boolean('Pequeño contribuyente'),
        'numero_factura': fields.function(_numero_factura, type='char', method=True, string='Numero Factura'),
    }

    _defaults = {
        'tipo_gasto': lambda *a: 'compra',
    }
account_invoice()
