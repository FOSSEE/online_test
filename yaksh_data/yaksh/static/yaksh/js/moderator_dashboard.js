$(document).ready(function(){
$(".selectall").change(function(){
        if($(this).prop("checked")) {
                $("#trial input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#trial input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });
});
