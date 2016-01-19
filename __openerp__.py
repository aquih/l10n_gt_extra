# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009-2012 Soluciones Tecnologócias Prisma S.A. All Rights Reserved.
# José Rodrigo Fernández Menegazzo, Soluciones Tecnologócias Prisma S.A.
# (http://www.solucionesprisma.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Guatemala - Reportes y funcionalidad extra',
    'version': '1.0',
    'category': 'Localization',
    'description': """ Rerporte requeridos por la SAT y otra funcionalidad extra para llevar un contabilidad en Guatemala. """,
    'author': 'José Rodrigo Fernández Menegazzo',
    'website': 'http://solucionesprisma.com/',
    'depends': ['l10n_gt'],
    'data': [
        'account_invoice_view.xml',
        'res_partner_view.xml',
        'reports.xml',
    ],
    'demo': [],
    'installable': True,
    'images': ['images/config_chart_l10n_gt.jpeg','images/l10n_gt_chart.jpeg'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
