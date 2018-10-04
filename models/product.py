# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

import odoo.addons.decimal_precision as dp

class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price = fields.Float(
        'Cost', company_dependent=True,
        digits=dp.get_precision('Product Price'),
        groups="account.group_account_manager",
        help="Cost of the product template used for standard stock valuation in accounting and used as a base price on purchase orders. "
             "Expressed in the default unit of measure of the product.")
