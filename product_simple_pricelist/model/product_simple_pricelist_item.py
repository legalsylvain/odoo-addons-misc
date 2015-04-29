# -*- encoding: utf-8 -*-
##############################################################################
#
#    Product - Simple Pricelist module for Odoo
#    Copyright (C) 2015-Today GRAP (http://www.grap.coop)
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model
from openerp.addons import decimal_precision as dp


class ProductSimplePricelistItem(Model):
    _name = 'product.simple.pricelist.item'
    _auto = False
    _table = 'product_simple_pricelist_item'

    _STATE_KEYS = [
        ('set', 'Set'),
        ('not_set', 'Not Set'),
    ]

    # Custom Section
    def _get_product_id_from_id(self, str_id):
        return int(str_id[:9])

    def _get_pricelist_version_id_from_id(self, str_id):
        return int(str_id[9:])

    # Button Section
    def change_price_wizard(self, cr, uid, ids, context=None):
        ctx = context.copy()
        ctx['pricelist_version_id'] = self._get_pricelist_version_id_from_id(
            ids[0])
        ctx['product_id'] = self._get_product_id_from_id(ids[0])
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.simple.pricelist.item.update.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }

    def _get_price(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for pspi in self.browse(cr, uid, ids, context=context):
            res[pspi.id] = pspi.specific_price and pspi.specific_price or\
                pspi.list_price
        return res

    # Column Section
    _columns = {
        'pricelist_id': fields.many2one(
            'product.pricelist', 'Pricelist', readonly=True),
        'pricelist_version_id': fields.many2one(
            'product.pricelist.version', 'Pricelist Version', readonly=True),
        'pricelist_item_id': fields.many2one(
            'product.pricelist.item', 'Pricelist Item', readonly=True),
        'product_id': fields.many2one(
            'product.product', 'Product', readonly=True),
        'company_id': fields.many2one(
            'res.company', 'Company', readonly=True),
        'specific_price': fields.float(
            'Specific Price', readonly=True,
            digits_compute=dp.get_precision('Product Price')),
        'standard_price': fields.float(
            'Standard Price', readonly=True,
            digits_compute=dp.get_precision('Purchase Price')),
        'list_price': fields.float(
            'List Price', readonly=True,
            digits_compute=dp.get_precision('Product Price')),
        'state': fields.selection(
            _STATE_KEYS, 'State'),
        'price': fields.function(
            _get_price, string='Price', type='float',
            digits_compute=dp.get_precision('Product Price')),
        'difference': fields.float(
            'Difference', readonly=True),
    }

    # View Section
    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
            SELECT
                to_char(pp.id, 'FM099999999')
                    || to_char(pplv.id, 'FM099999999') AS id,
                pt.company_id AS company_id,
                pt.name AS product_name,
                pt.sale_ok AS sale_ok,
                pp.id AS product_id,
                pt.standard_price,
                pt.list_price,
                ppl.name,
                ppl.id as pricelist_id,
                pplv.id as pricelist_version_id,
                ppli.id as pricelist_item_id,
                ppli.price_surcharge as specific_price,
                CASE WHEN ppli.id is null
                    THEN 'not_set'
                    ELSE 'set'
                    END as state,
                CASE WHEN (ppli.id is null or pt.list_price = 0)
                    THEN 0
                    ELSE (ppli.price_surcharge - pt.list_price) / pt.list_price
                    END as difference
            FROM product_product pp
            INNER JOIN product_template pt
                ON pp.product_tmpl_id = pt.id
            JOIN product_pricelist ppl
                ON ppl.company_id = pt.company_id
                AND ppl.is_simple = True
            LEFT OUTER JOIN product_pricelist_version pplv
                ON pplv.pricelist_id = ppl.id
            LEFT OUTER JOIN product_pricelist_item ppli
                ON ppli.product_id = pp.id
                AND ppli.price_version_id = pplv.id
        )""" % (self._table))
