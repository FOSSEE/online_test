$(document).ready(function(){
    var checked_vals = [];
    $('input:checkbox[name="quiz_lesson"]').click(function() {
        if($(this).prop("checked") == true){
            checked_vals.push($(this).val());
        }
        else{
            checked_vals.pop($(this).val());
        }
    });
    $('#design_course_form').submit(function(eventObj) {
        var input_order = $("input[name*='order']");
        var order_list = []
        if (input_order){
            $(input_order).each(function(index) {
                order_list.push($(this).data('item-id')+":"+$(this).val());
            });
        }
        $(this).append('<input type="hidden" name="choosen_list" value='+checked_vals+'>');
        $(this).append('<input type="hidden" name="ordered_list" value='+order_list+'>');
        return true;
    });
    var msg = "Check Prerequisite is set to Yes by default \n" + 
              "To change, select the Change checkbox and Click Change Prerequisite button \n";
    $("#prereq_msg").attr("title", msg);
});