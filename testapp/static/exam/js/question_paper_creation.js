$(document).ready(function(){
    /* selectors for the 3 step tabs*/
    $fixed_tab = $("#fixed-tab");
    $random_tab = $("#random-tab");
    $finish_tab = $("#finish-tab");

    $question_type = $("#id_question_type");
    $marks = $("#id_marks");

    $total_marks = $("#total_marks");
    /* ajax requsts on selectors change */
    $question_type.change(function() {
        $.ajax({
            url: "/exam/ajax/questionpaper/marks/",
            type: "POST",
            data: {
                question_type: $question_type.val()
            },
            dataType: "html",
            success: function(output) {
                $marks.html(output);
            }
        });
    });

    $marks.change(function() {
        var fixed_question_list = [];
        var fixed_inputs = $("input[name=fixed]");
        var random_question_list = [];
        var random_inputs = $("input[name=random]");
        for(var i = 0; i < fixed_inputs.length; i++){
                fixed_question_list.push($(fixed_inputs[i]).val());
        }
        for(var i = 0; i < random_inputs.length; i++){
                random_question_list.push($(random_inputs[i]).val());
        }
        $.ajax({
            url: "/exam/ajax/questionpaper/questions/",
            type: "POST",
            data: {
                question_type: $question_type.val(),
                marks: $marks.val(),
                fixed_list: fixed_question_list,
                random_list: random_question_list
            },
            dataType: "html",
            success: function(output) {
                if($fixed_tab.hasClass("active")) {
                    var questions = $(output).filter("#questions").html();
                    $("#fixed-available").html(questions);
                } else if($random_tab.hasClass("active")) {
                    var questions = $(output).filter("#questions").html();
                    var numbers = $(output).filter("#num").html();
                    $("#random-available").html(questions);
                    $("#number-wrapper").html(numbers);
                }
            }
        });
    });

    /* adding fixed questions */
    $("#add-fixed").click(function(e) {
        var count = 0;
        var selected = [];
        var html = "";
        var $element;
        var total_marks = parseFloat($total_marks.text());
        var marks_per = parseFloat($marks.val())
        $("#fixed-available input:checkbox").each(function(index, element) {
            if($(this).attr("checked")) {
                qid = $(this).attr("data-qid");
                if(!$(this).hasClass("ignore")) {
                    selected.push(qid);
                    $element = $("<div class='qcard'></div>");
                    html += "<li>" + $(this).next().html() + "</li>";
                    count++;
                }
            }
        });
        html = "<ul>" + html + "</ul>";
        selected = selected.join(",");
        var $input = $("<input type='hidden'>");
        $input.attr({
            value: selected,
            name: "fixed"
        });
        $remove = $("<a href='#' class='remove' data-num="+count+" data-marks = "+marks_per +">&times;</div>");
        $element.html(count + " question(s) added").append(html).append($input).append($remove);
        $("#fixed-added").prepend($element);
        total_marks = total_marks + count * marks_per;
        $total_marks.text(total_marks)
    e.preventDefault();
    });

    /* adding random questions */
    $("#add-random").click(function(e) {
        $numbers = $("#numbers");
        random_number = $numbers.val()
        if($numbers.val()) {
            $numbers.removeClass("red-alert");
            var count = 0;
            var selected = [];
            var html = "";
            var $element;
            var total_marks = parseFloat($total_marks.text());
            var marks_per = parseFloat($marks.val())
            $("#random-available input:checkbox").each(function(index, element) {
                if($(this).attr("checked")) {
                    qid = $(this).attr("data-qid");
                    if(!$(this).hasClass("ignore")) {
                        selected.push(qid);
                        $element = $("<div class='qcard'></div>");
                        html += "<li>" + $(this).next().html() + "</li>";
                        count++;
                    }
                }
            });
            html = "<ul>" + html + "</ul>";
            selected = selected.join(",");
            var $input_random = $("<input type='hidden'>");
            $input_random.attr({
                value: selected,
                name: "random"
            });
            var $input_number = $("<input type='hidden'>");
            $input_number.attr({
                value: $numbers.val(),
                name: "number"
            });
            $remove = $("<a href='#' class='remove' data-num="+random_number+" data-marks = "+marks_per +">&times;</div>");
            $element.html(random_number + " question(s) will be selected from " + count + " question(s)").append(html).append($input_random).append($input_number).append($remove);
            $("#random-added").prepend($element);
            total_marks = total_marks + random_number * marks_per;
            $total_marks.text(total_marks)
        } else {
            $numbers.addClass("red-alert");
        }
    e.preventDefault();
    });

    /* removing added questions */
    $(".qcard .remove").live("click", function(e) {
        var marks_per = $(this).attr('data-marks');
        var num_question = $(this).attr('data-num');
        var sub_marks = marks_per*num_question;
        var total_marks = parseFloat($total_marks.text());
        total_marks = total_marks - sub_marks;
        $total_marks.text(total_marks);

        $(this).parent().slideUp("normal", function(){ $(this).remove(); });
    e.preventDefault();
    });

    /* showing/hiding selectors on tab click */
    $(".tabs li").click(function() {
        if($(this).attr("id") == "finish-tab") {
            $("#selectors").hide();
        } else {
            $question_type.val('select');
            $marks.val('select')
            $("#selectors").show();
        }
    });
    /* check all questions on checked*/
    $("#checkall").live("click", function(){
        if($(this).attr("checked")) {
             if($("#fixed-tab").hasClass("active")) {
                $("#fixed-available input:checkbox").each(function(index, element) {
                $(this).attr('checked','checked');
                });
            }
            else {
                $("#random-available input:checkbox").each(function(index, element) {
                $(this).attr('checked','checked');
                });
            }
         }
         else {
            if($("#fixed-tab").hasClass("active")) {
                $("#fixed-available input:checkbox").each(function(index, element) {
                $(this).removeAttr('checked');
                });
            }
            else {
                $("#random-available input:checkbox").each(function(index, element) {
                $(this).removeAttr('checked');
                });
            }
        }
    });

    /* show preview on preview click */
    $("#preview").click(function(){
        questions = getQuestions()
        if(questions.trim() == ""){
            $('#modal_body').html("No questions selected");
        }
        else {
            $('#modal_body').html(questions);
        }
        $("#myModal").modal('show');
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

    /* Check at least one question is present before saving */
    $('#save').click(function(){
        questions = getQuestions();
        if(questions.trim() == ""){
            $("#modalSave").modal("show");
        }
        else {
            document.forms["frm"].submit();
        }
    });

    /* Fetch selected questions */
    function getQuestions(){
        var fixed_div = $("#fixed-added").html();
        var random_div = $("#random-added").html();
        return fixed_div+random_div;
    }
}); //document
