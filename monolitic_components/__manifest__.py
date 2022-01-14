# Copyright 2019 Jesus Ramoneda <jesus.ramonedae@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monolitic Components",
    "summary": "Manage products as components",
    "version": "14.0.1.0.1",
    "category": "Product",
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
        "product",
        "sale",
    ],
    "data": [
        'data/category.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/menu.xml',
        'views/product_component_type.xml',
        'views/product_template.xml',
    ],
}
