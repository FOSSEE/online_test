$(document).ready(function(){
    $question_type = $('#id_question_type');
    $qpaper_id = $('#qpaper_id');
    $marks = $('#id_marks');
    $show = $('#show');
    $question_type.change(function() {
        this.form.submit();
    });

    $marks.change(function() {
        this.form.submit();
    });

    /* showing/hiding selectors on tab click */
    $(".tabs li").click(function() {
        if($(this).attr("id") == "finish-tab") {
            $("#selectors").hide();
            $('#is_active').val("finish");
        } else {
            if($(this).attr("id") == "fixed-tab") {
                $('#is_active').val("fixed");
            }
            if($(this).attr("id") == "random-tab") {
                $('#is_active').val("random");
            }
                $question_type.val('select');
                $marks.val('select')
                $("#selectors").show();
        }
    });

    /* tab change on next or previous button click */
    $("#fixed-next").click(function(){
        $("#random").click();
    });
    $("#random-next").click(function(){
        $("#finished").click();
    });

    $("#random-prev").click(function(){
        $("#fixed").click();
    });

    $("#finish-prev").click(function(){
        $("#random").click();
    });

    var checked_vals = [];
    $('input:checkbox[name="questions"]').click(function() {
        if($(this).prop("checked") == true){
            checked_vals.push(parseInt($(this).val()));
        }
        else{
            checked_vals.pop(parseInt($(this).val()));
        }
    });
    $('#design_q').submit(function(eventObj) {
        $(this).append('<input type="hidden" name="checked_ques" value='+checked_vals+'>');
        return true;
    });

    $('#add_checkall').on("change", function () {
        if($(this).prop("checked")) {
            $("#fixed-available input:checkbox").each(function(index, element) {
                if(isNaN($(this).val())) {return};
                $(this).prop("checked", true);
                checked_vals.push(parseInt($(this).val()))
            });
        } else {
            $("#fixed-available input:checkbox").each(function(index, element){
                $(this).prop('checked', false);
                checked_vals.pop(parseInt($(this).val()));
            });
        }
    });

    $('#remove_checkall').on("change", function () {
        if($(this).prop("checked")) {
            $("#fixed-added input:checkbox").each(function (index, element) {
                if(isNaN($(this).val())) { return };
                $(this).prop('checked', true);
                checked_vals.push(parseInt($(this).val()));
            });
        } else {
            $("#fixed-added input:checkbox").each(function (index, element) {
                $(this).prop('checked', false);
                checked_vals.pop(parseInt($(this).val()));
            });
        }
    });

});//document
function append_tag(tag){
    var tag_name = document.getElementById("question_tags");
    if (tag_name.value != null){
        tag_name.value = tag.value+", "+tag_name.value;
    }
    else{
        tag_name.value = tag.value;
    }
}

