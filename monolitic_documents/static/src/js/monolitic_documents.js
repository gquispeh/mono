odoo.define('monolitic_document.MonoliticDocuments', function (require) {
    "use strict";
    const DocumentsInspector = require('documents.DocumentsInspector');

    DocumentsInspector.include({
        /**
         * @override @private
         */
        _renderFields: function () {
            this._super.apply(this, arguments);
            if (this.records.length === 1) {
                this._renderField('public', {mode: 'edit'});
                this._renderField('local_url', {mode: 'edit'});
            }
        },

    });

});
