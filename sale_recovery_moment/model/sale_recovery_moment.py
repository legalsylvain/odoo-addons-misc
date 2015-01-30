# -*- encoding: utf-8 -*-
##############################################################################
#
#    Sale - Recovery Moment Module for Odoo
#    Copyright (C) 2014 GRAP (http://www.grap.coop)
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


from openerp.osv import fields
from openerp.osv.orm import Model
from openerp.osv.orm import except_orm
from openerp.tools.translate import _


class sale_recovery_moment(Model):
    _description = 'Recovery Moment'
    _name = 'sale.recovery.moment'
    _order = 'min_recovery_date, max_recovery_date, place_id'

    # Field Functions Section
    def _get_order(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for srm in self.browse(cr, uid, ids, context=context):
            res[srm.id] = {
                'valid_order_qty': 0,
                'order_qty': len(srm.order_ids),
            }
            for order in srm.order_ids:
                if order.state not in ('draft', 'cancel'):
                    res[srm.id]['valid_order_qty'] += 1
        return res

    def _get_complete_name(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for srm in self.browse(cr, uid, ids, context=context):
            address_format = srm.country_id \
                and srm.country_id.address_format \
                or "%(street)s\n%(street2)s\n%(city)s %(state_code)s" \
                " %(zip)s\n%(country_name)s"
            args = {
                'street': srm.street and srm.street or '',
                'street2': srm.street2 and srm.street2 or '',
                'zip': srm.zip and srm.zip or '',
                'city': srm.city and srm.city or '',
                'state_code': srm.state_id and srm.state_id.code or '',
                'state_name': srm.state_id and srm.state_id.name or '',
                'country_code': srm.country_id and srm.country_id.code or '',
                'country_name': srm.country_id and srm.country_id.name or '',
            }
            res[srm.id] = srm.name + ' - ' \
                + (address_format % args).replace('\n', ' ')
        return res

    def _get_quota_description(
            self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for srm in self.browse(cr, uid, ids, context=context):
            if srm.max_order_qty:
                res[srm.id] = _('%d / %d Orders') % (
                    srm.valid_order_qty, srm.max_order_qty)
            elif srm.valid_order_qty:
                res[srm.id] = _('%d Order(s)') % (
                    srm.valid_order_qty)
            else:
                res[srm.id] = _('No Orders')
        return res

    def _get_picking(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        spo_obj = self.pool['stock.picking.out']
        for srm in self.browse(cr, uid, ids, context=context):
            order_ids = [x.id for x in srm.order_ids]
            res[srm.id] = spo_obj.search(cr, uid, [
                ('sale_id', 'in', order_ids)], context=context)
        return res

    def _get_name(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for srm in self.browse(cr, uid, ids, context=context):
            res[srm.id] = srm.code + ' - ' + srm.group_id.short_name\
                + ' - ' + srm.min_recovery_date
        return res

    def _get_moment_from_group(self, cr, uid, ids, context=None):
        """Return Moment ids depending on changes of Group"""
        res = []
        srmg_obj = self.pool['sale.recovery.moment.group']
        for srmg in srmg_obj.browse(cr, uid, ids, context=context):
            res.extend([x.id for x in srmg.moment_ids])
        return res

    # Columns Section
    _columns = {
        'code': fields.char(
            'Code', readonly=True, required=True),
        'name': fields.function(
            _get_name, type='char', store={
                'sale.recovery.moment': (
                    lambda self, cr, uid, ids, context=None: ids,
                    ['code', 'min_recovery_date'], 10),
                'sale.recovery.moment.group': (
                    _get_moment_from_group,
                    ['short_name'], 10),
            }),
        'place_id': fields.many2one(
            'sale.recovery.place', 'Place', required=True),
        'group_id': fields.many2one(
            'sale.recovery.moment.group', 'Recovery Moment Group',
            ondelete='cascade', required=True,),
        'company_id': fields.related(
            'group_id', 'company_id', type='many2one', relation='res.company',
            string='Company', store=True, readonly=True),
        'min_recovery_date': fields.datetime(
            string='Minimum date for the Recovery', required=True),
        'max_recovery_date': fields.datetime(
            string='Minimum date for the Recovery', required=True),
        'description': fields.text('Description'),
        'order_ids': fields.one2many(
            'sale.order', 'moment_id', 'Sale Orders', readonly=True),
        'order_qty': fields.function(
            _get_order, type='integer', multi='order',
            string='Sale Orders Quantity'),
        'valid_order_qty': fields.function(
            _get_order, type='integer', multi='order',
            string='Valid Sale Orders Quantity'),
        'max_order_qty': fields.integer(
            'Max Order Quantity'),
        'quota_description': fields.function(
            _get_quota_description, type='char', string='Quota Description'),
        'picking_ids': fields.function(
            _get_picking, type='one2many',
            relation='stock.picking.out', string='Stock Picking Quantity'),
    }

    # Defaults Section
    _defaults = {
        'code': (
            lambda obj, cr, uid, context:
            obj.pool.get('ir.sequence').get(
                cr, uid, 'sale.recovery.moment')),
    }

    # Constraint Section
    def _check_recovery_dates(self, cr, uid, ids, context=None):
        for srm in self.browse(cr, uid, ids, context=context):
            if srm.min_recovery_date >= srm.max_recovery_date:
                return False
        return True

    _constraints = [
        (
            _check_recovery_dates,
            'Error ! The minimum Date of Recovery must be before the maximum'
            ' Date of Recovery.',
            ['min_recovery_date', 'max_recovery_date']),
    ]

    # Overload Section
    def unlink(self, cr, uid, ids, context=None):
        for srm in self.browse(cr, uid, ids, context=context):
            if srm.valid_order_qty:
                raise except_orm(
                    _('Error!'),
                    _("You can not delete this Recovery Moment because there"
                        " is %d Valid Sale Orders associated.\nPlease move"
                        " Sale orders on an other Recovery Moment and contact"
                        " your customers.") % (len(srm.valid_order_qty)))
        return super(sale_recovery_moment, self).unlink(
            cr, uid, ids, context=context)
