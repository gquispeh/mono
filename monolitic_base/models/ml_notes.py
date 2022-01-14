from odoo import fields, models, _
# -*- coding: utf-8 -*-
# Copyright 2020 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


class MLNotes(models.Model):
    _name = 'ml.notes'
    _description = 'Notes for models'
    _rec_name = "note"

    note = fields.Html(string='Note')
    user_id = fields.Many2one(comodel_name='res.users', string='User',
                              default=lambda x: x.env.user.id)
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments')
    res_id = fields.Many2one(comodel_name='ml.notes.mixing')


class MLNotesMixing(models.AbstractModel):
    _name = 'ml.notes.mixing'
    _description = "Mixing for Notes"

    note_ids = fields.One2many(comodel_name='ml.notes', inverse_name='res_id')

    def open_notes(self):
        view_id = self.env.ref('monolitic_base.ml_notes_mixing_view_form').id
        return {
            'name': _('Notes'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': view_id,
            'res_model': self._name,
            'target': 'new'
        }
