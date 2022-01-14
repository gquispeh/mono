odoo.define('rma_portal_form_validation_ept', function (require) {"use strict";
    $(document).ready(function () {
   	 	var ajax = require('web.ajax');
   	 	$("select[name='country_id']").on('change', function () {
               if ($("#country_id").val()) {
                   ajax.jsonRpc("/shop/country_infos/" + $("#country_id").val(), 'call',{mode: 'shipping'}).then(
                       function(data) {
                           // placeholder phone_code
                           //$("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');

                           // populate states and display
                           var selectStates = $("select[name='state_id']");
                           // dont reload state at first loading (done in qweb)
                           if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
                               if (data.states.length) {
                                   selectStates.html('');
                                   _.each(data.states, function(x) {
                                       var opt = $('<option>').text(x[1])
                                           .attr('value', x[0])
                                           .attr('data-code', x[2]);
                                       selectStates.append(opt);
                                   });
                                   selectStates.parent('div').show();
                               }
                               else {
                                   selectStates.val('').parent('div').hide();
                               }
                               selectStates.data('init', 0);
                           }
                           else {
                               selectStates.data('init', 0);
                           }

                           // manage fields order / visibility
                           if (data.fields) {
                               if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)){
                                   $(".div_zip").before($(".div_city"));
                               }
                               else {
                                   $(".div_zip").after($(".div_city"));
                               }
                               var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
                               _.each(all_fields, function(field) {
                                   $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields)>=0);
                               });
                           }
                       }
                   );
               }
          
       });
    

   	 	//if any checkbox is checked
        function checkbox_validate() {
            var anyBoxesChecked = false;

            $('.rma_form input[type="checkbox"]').each(function () {
                if ($(this).is(":checked")) {
                    anyBoxesChecked = true;
                    $("#btnsubmit").removeAttr("disabled")
                    $(".form_error_msg").css("display", "none")
                }

            });

            if (anyBoxesChecked == false) {
                $("#btnsubmit").prop("disabled", true);
                $(".form_error_msg").css("display", "block").html("Please select atleast one product.");
            }
        }


        checkbox_validate()


        //set Required Attribute to select and textbox when checkbox is Tick.
        $(".tick_box").on('change', function () {
            var ischecked = $(this).is(":checked");

            if (ischecked) {
                $(this).parent().siblings().find("select").attr("required", "true")
                $(this).parent().siblings().find("input[type=text]").attr("required", "true")
                $("#btnsubmit").removeAttr("disabled")
                $(".form_error_msg").css("display", "none")

            } else {
                $(this).parent().siblings().find("select").removeAttr("required")
                $(this).parent().siblings().find("input[type=text]").removeAttr("required")

            }
        });

        //some Validations for Return Quantity
        $(".return_qty").keyup(function () {
            var return_qty = parseInt($(this).val());
            var delivered_qty = parseInt($(this).parents(".orders_vertical_align").find("#delivered_qty").val());
            checkbox_validate()

            if (return_qty == 0) {
                $(this).val(1);
            }
            if (return_qty < 0) {
                $(this).parents(".orders_vertical_align").siblings().find(".tick_box").prop("checked", false);
                $(this).parents(".orders_vertical_align").siblings().find(".tick_box").attr("required", "true")

            }

            if (return_qty > delivered_qty) {
                $(this).val(delivered_qty);
                $(this).parents(".orders_vertical_align").find(".tick_box").prop("checked", false);
                $(this).parent().find("select").attr("required", "true")
                $(this).parent().find("input[type=text]").attr("required", "true")
            }
	         if (return_qty <= delivered_qty) {
	        	 $(this).parents(".orders_vertical_align").find(".tick_box").prop("checked", true);
	             $(this).parents(".orders_vertical_align").find("select").attr("required", "true")
	            }
            

        });

        $("input#btnsubmit").mouseover(function () {
            checkbox_validate()
        })

        //bread-crumb
        $(".rma_breadcrumb").parents().siblings().find(".o_portal_submenu").css("display", "none");

    });
})
