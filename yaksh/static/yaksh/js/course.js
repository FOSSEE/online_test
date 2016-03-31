$(document).ready(function(){
$(".checkall").click( function(){
        if($(this).attr("checked")) {
                $("#enroll-all input:checkbox").each(function(index, element) {
                $(this).attr('checked', true);
                });
        }
        else {
                $("#enroll-all input:checkbox").each(function(index, element) {
                $(this).attr('checked', false);
                });
        }
    });
$(".enroll").click( function(){
        if($(this).attr("checked")) {
                $("#enroll input:checkbox").each(function(index, element) {
                $(this).attr('checked', true);
                });
        }
        else {
                $("#enroll input:checkbox").each(function(index, element) {
                $(this).attr('checked', false);
                });
        }
    });
$(".reject").click( function(){
        if($(this).attr("checked")) {
                $("#reject input:checkbox").each(function(index, element) {
                $(this).attr('checked', true);
                });
        }
        else {
                $("#reject input:checkbox").each(function(index, element) {
                $(this).attr('checked', false);
                });
        }
    });
});
