# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account - Recurring Invoices Duplication module for Odoo
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

from openerp.osv import orm, fields


class AccountInvoiceDuplicationWizardLine(orm.TransientModel):
    _name = 'account.invoice.duplication.wizard.line'

    # Columns Section
    _columns = {
        'wizard_id': fields.many2one(
            'account.invoice.duplication.wizard', string='Wizard'),
        'date_invoice': fields.date(
            string='Invoice Date', required=True),
        'date_due': fields.date(
            string='Due Date', required=True),
    }
