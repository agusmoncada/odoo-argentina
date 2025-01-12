# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, fields
from odoo.exceptions import ValidationError

class AccountPaymentGroup(models.Model):

    _inherit = "account.payment.group"

    # @api.model
    # def _get_regimen_ganancias(self):
    #     result = []
    #     for line in self.
    #     return

    retencion_ganancias = fields.Selection([
        # _get_regimen_ganancias,
        ('imposibilidad_retencion', 'Imposibilidad de Retención'),
        ('no_aplica', 'No Aplica'),
        ('nro_regimen', 'Nro Regimen'),
    ],
        'Retención Ganancias',
    )
    regimen_ganancias_id = fields.Many2one(
        'afip.tabla_ganancias.alicuotasymontos',
        'Regimen Ganancias',
        ondelete='restrict',
    )
    company_regimenes_ganancias_ids = fields.Many2many(
        'afip.tabla_ganancias.alicuotasymontos',
    )
    temp_payment_ids = fields.Char('temp_payment_ids')

    @api.model
    def default_get(self, fields):
        res = super(AccountPaymentGroup, self).default_get(fields)
        if res.get('partner_type') == 'supplier':
            res.update({
                'company_regimenes_ganancias_ids': [(6,0,self.env.user.company_id.regimenes_ganancias_ids.ids)],
                'retencion_ganancias': 'nro_regimen',
                })
        else:
            res.update({
                'company_regimenes_ganancias_ids': [(6,0,[])]
                })
        return res

    #@api.depends('company_id.regimenes_ganancias_ids')
    #def _company_regimenes_ganancias(self):
    #    """
    #    Lo hacemos con campo computado y no related para que solo se setee
    #    y se exija si es pago de o a proveedor
    #    """
    #    for rec in self.filtered(lambda x: x.partner_type == 'supplier'):
    #        rec.company_regimenes_ganancias_ids = (
    #            rec.company_id.regimenes_ganancias_ids)
    #    for rec in self.filtered(lambda x: x.partner_type == 'customer'):
    #        rec.company_regimenes_ganancias_ids = [(6,0,[])]

    @api.onchange('commercial_partner_id')
    def change_retencion_ganancias(self):
        if self.commercial_partner_id.imp_ganancias_padron in ['EX', 'NC']:
            self.retencion_ganancias = 'no_aplica'
        else:
            cia_regs = self.company_regimenes_ganancias_ids
            partner_regimen = (
                self.commercial_partner_id.default_regimen_ganancias_id)
            if partner_regimen:
                def_regimen = partner_regimen
            elif cia_regs:
                def_regimen = cia_regs[0]
            else:
                def_regimen = False
            self.regimen_ganancias_id = def_regimen

    # sacamos esto por ahora ya que no es muy prolijo y nos se esta usando, si
    # lo llegamos a activar entonces tener en cuenta que en sipreco no queremos
    # que en borrador se setee ninguna regimen de ganancias
    # @api.model
    # def create(self, vals):
    #     """
    #     para casos donde se paga desde algun otro lugar (por ej. liquidador
    #     de impuestos), seteamos no aplica si no hay nada seteado
    #     """
    #     payment_group = super(AccountPaymentGroup, self).create(vals)
    #     if (
    #             payment_group.company_regimenes_ganancias_ids and
    #             payment_group.partner_type == 'supplier' and
    #             not payment_group.retencion_ganancias and
    #             not payment_group.regimen_ganancias_id):
    #         payment_group.retencion_ganancias = 'no_aplica'
    #     return payment_group
    def post(self):
        res = super(AccountPaymentGroup, self).post()
        for rec in self:
            if rec.temp_payment_ids:
                payment_ids = rec.temp_payment_ids.split(',')
                for payment_id in payment_ids:
                    payment = self.env['account.payment'].browse(int(payment_id))
                    payment.write({'used_withholding': True})
            withholding = None
            for payment in rec.payment_ids:
                if payment.tax_withholding_id:
                    withholding = True
            if withholding == True:
                for payment in rec.payment_ids:
                    payment.write({'used_withholding': True})

        return res
