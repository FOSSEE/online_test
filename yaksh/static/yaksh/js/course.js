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

    $(".send_check").change( function(){
        if($(this).prop("checked")) {
                $("#sender_list input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#sender_list input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });

    $(function() {
        tinymce.init({ 
            selector: 'textarea#email_body',
            max_height: 400,
            height: 400,
            plugins: "code image link"
        });
    });

    $("#send_mail").click(function(){
        var subject = $("#subject").val();
        var body = tinymce.get("email_body").getContent();
        var status = false;
        var selected = [];
        $('#sender_list input:checked').each(function() {
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
        if(!status_div.is(":visible")) {
            var get_url = $("#url-"+student_id).attr("data-url");
            lock_screen();
            $.ajax({
                url: get_url,
                timeout: 8000,
                type: "GET",
                dataType: "json",
                contentType: 'application/json; charset=utf-8',
                success: function(data) {
                    unlock_screen();
                    status_div.toggle();
                    status_div.html(data.user_data);
                    },
                error: function(jqXHR, textStatus) {
                    unlock_screen();
                    alert("Unable to get user data. Please Try again later.");
                } 
            });
        } else {
            status_div.toggle();
        }
    });

    $('[data-toggle="tooltip"]').tooltip();

    $('#upload').on('change',function(){
        //get the file name
        var files = [];
        for (var i = 0; i < $(this)[0].files.length; i++) {
            files.push($(this)[0].files[i].name);
        }
        $(this).next('.custom-file-label').html(files.join(', '));
    });

    $('[data-toggle="tab"]').tooltip({
        trigger: 'hover',
        placement: 'top',
        animate: false,
        container: 'body'
    });

}); // end document ready

function lock_screen() {
    document.getElementById("loader").style.display = "block";
}

function unlock_screen() {
    document.getElementById("loader").style.display = "none";
}
