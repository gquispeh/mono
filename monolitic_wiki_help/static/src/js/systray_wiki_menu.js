odoo.define('monolitic_wiki_help.wiki', function(require) {
   "use strict";
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    window.click_num = 0;

    var ActionMenu = Widget.extend({
        template: 'monolitic_wiki_help.wiki',
        events: {
            'click .my_icon': 'onclick_myicon',
        },

        onclick_myicon:function(){
            var times = 0;
            var self = this;

            self._rpc({
                model: 'ir.ui.menu',
                method: 'get_menu_id',
                args: [[self.id], window.location.href.replace(window.location.origin, "")],
            }).then(function (new_url){
                if (new_url && times == 0){
                    times++;
                    window.open(new_url);
                } else if (times == 0){
                    times++;
                    alert("Wiki page not found for this module");
                }
            });
        },
    });

   SystrayMenu.Items.push(ActionMenu);
   return ActionMenu;
});
