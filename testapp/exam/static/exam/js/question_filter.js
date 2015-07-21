$(document).ready(function(){
    $question_type = $("#id_question_type");
    $marks = $("#id_marks");
    $language = $("#id_language");

    $question_type.change(function() {
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
    });

    $language.change(function() {
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
    });

    $marks.change(function() {
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
    });

    $("#checkall").live("click", function(){
        if($(this).attr("checked")) {
                $("#filtered-questions input:checkbox").each(function(index, element) {
                $(this).attr('checked','checked');
                });
        }
        else {
                $("#filtered_questions input:checkbox").each(function(index, element) {
                $(this).removeAttr('checked');
                });
        }
    });
});