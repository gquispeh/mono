# Copyright 2019 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ClientClassification(models.Model):
    _name = "monolitic.client.classification"
    _description = "Monolitic Clasificación Cliente"

    name = fields.Char(string='Client Strategic Classification')
