$(document).ready(function(){
    $question_type = $("#id_question_type");
    $marks = $("#id_marks");
    $language = $("#id_language");

    function question_filter() {
        $.ajax({
            url: "/exam/ajax/questions/filter/",
            type: "POST",
            data: {
                question_type: $question_type.val(),
                marks: $marks.val(),
                language: $language.val()
            },
            dataType: "html",
            success: function(output) {
                var questions = $(output).filter("#questions").html();
                $("#filtered-questions").html(questions);
            }
        });
    }

    $question_type.change(function() {
        question_filter()
    });

    $language.change(function() {
        question_filter()
    });

    $marks.change(function() {
        question_filter()
    });

    $("#checkall").change(function(){
        if($(this).prop("checked")) {
                $("#filtered-questions input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#filtered-questions input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });
});