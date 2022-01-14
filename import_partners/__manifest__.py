# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Import Partners",
    "summary": "Import partnerss",
    "version": "14.0.1.0.0",
    "category": "Partner",
    "website": "https://www.qubiq.es",
    "author": "QubiQ",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "base",
        "contacts",
        "queue_job",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/import_partner.xml",
        "wizards/import_client_segmentation.xml",
    ],
}
