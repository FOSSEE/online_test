$(document).ready(function(){
$(".checkall").change( function(){
        if($(this).prop("checked")) {
                $("#enroll-all input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#enroll-all input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });
$(".enroll").change( function(){
        if($(this).prop("checked")) {
                $("#enroll input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#enroll input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });
$(".reject").change( function(){
        if($(this).prop("checked")) {
                $("#reject input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#reject input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });

$(function() {
    tinymce.init({ 
        selector: 'textarea#email_body',
        max_height: 200,
        height: 200
    });
});

$("#send_mail").click(function(){
    var subject = $("#subject").val();
    var body = tinymce.get("email_body").getContent();
    var status = false;
    var selected = [];
    $('#reject input:checked').each(function() {
        selected.push($(this).attr('value'));
    });
    if (subject == '' || body == ''){
        $("#error_msg").html("Please enter mail details");
        $("#dialog").dialog();
    }
    else if (selected.length == 0){
        $("#error_msg").html("Please select atleast one user");
        $("#dialog").dialog();
    }
    else {
        status = true;
    }
    return status;
});


// Table sorter for course details
$("table").tablesorter({});

// Get user course completion status
$('.user_data').click(function() {
    var data = $(this).data('item-id');
    course_id = data.split("+")[0];
    student_id = data.split("+")[1];
    var status_div = $("#show_status_"+course_id+"_"+student_id);
    if(!status_div.is(":visible")){
        var get_url = window.location.protocol + "//" + window.location.host +
                  "/exam/manage/get_user_status/" + course_id + "/" + student_id;
        $.ajax({
            url: get_url,
            timeout: 8000,
            type: "GET",
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            success: function(data) {
                    status_div.toggle();
                    status_div.html(data.user_data);
                },
            error: function(jqXHR, textStatus) {
                alert("Unable to get user data. Please Try again later.");
            } 
        });
    } else {
        status_div.toggle();
    }
});

$('[data-toggle="tooltip"]').tooltip();

}); // end document ready
