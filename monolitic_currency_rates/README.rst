.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

========================
Monolitic Currency Rates
========================

This module add an independent rates for currencies exchanges in Sales, Purchases and Invoice Models
Also you can add margins in the currency that will be add in the rate conversion

Installation
============

To install this module, you need to:

#. No special installation is required

Configuration
=============

To configure this module, you need to:

1. Go to Accounting > Configuration > currencies
2. Add some margins in the currencies


Usage
=====

To use this module, you need to:

1. Create Sales/Purchase with a different currency and change the rate
2. Create an Invoice from the created Sale/Purchase
3. Validate the invoice to convert the amount.

It's is possible to create and change the rates directly from the invoice

Known issues / Roadmap
======================

* ...

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/QubiQ/qu-server-tools/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Jesus Ramoneda <jesus.ramoneda@qubiq.es>

Do not contact contributors directly about support or help with technical issues.

Maintainer
----------

.. image:: https://pbs.twimg.com/profile_images/702799639855157248/ujffk9GL_200x200.png
   :alt: QubiQ
   :target: https://www.qubiq.es

This module is maintained by QubiQ.

To contribute to this module, please visit https://github.com/QubiQ.
