# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'
    
    local_url = fields.Char(
        string='Attachment URL',
        related='attachment_id.local_url'
    )
    public = fields.Boolean(
        string='Is public',
        related='attachment_id.public'
    )
