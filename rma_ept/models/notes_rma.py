from odoo import fields, models, _


class MlNotesRMA(models.Model):
    _name = "ml.notes.rma"
    _description = 'RMA Notes'
    _inherit = "ml.notes"

    note_type = fields.Selection(
        string="Type",
        selection=[
            ("problem_detected", "Problema Detectado"),
            ("actions_to_take", "Acciones a tomar"),
            ("technic_resolution", "Resolución Técnica"),
            ("administrative_resolution", "Resolución Administrativa"),
        ],
    )


class MLNotesMixing(models.AbstractModel):
    _name = "ml.notes.mixing.rma"
    _description = "Mixin for RMA Notes"

    note_ids = fields.One2many(comodel_name="ml.notes.rma", inverse_name="res_id")

    def open_notes(self):
        view_id = self.env.ref("rma_ept.ml_notes_rma_mixing_view_form").id
        return {
            "name": _("Notes"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_id": self.id,
            "view_id": view_id,
            "res_model": self._name,
            "target": "new",
        }
