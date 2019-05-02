# -*- encoding: utf-8 -*-

{
    'name': 'Guatemala - Reportes y funcionalidad extra',
    'version': '1.0',
    'category': 'Localization',
    'description': """ Reportes requeridos por la SAT y otra funcionalidad extra para llevar un contabilidad en Guatemala. """,
    'author': 'José Rodrigo Fernández Menegazzo',
    'website': 'http://solucionesprisma.com/',
    'depends': ['l10n_gt', 'account_tax_python', 'account_cancel','product','purchase'],
    'data': [
        'data/l10n_gt_extra_base.xml',
        'views/account_view.xml',
        'views/res_partner_view.xml',
        'views/product_views.xml',
        'views/purchase_views.xml',
        'views/report.xml',
        'views/reporte_banco.xml',
        'views/reporte_partida.xml',
        'views/reporte_compras.xml',
        'views/reporte_ventas.xml',
        'views/reporte_inventario.xml',
        'views/reporte_diario.xml',
        'views/reporte_mayor.xml',
        'views/l10n_gt_extra_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
