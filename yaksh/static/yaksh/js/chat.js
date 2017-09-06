$(document).ready(function() {
    if ($("#chat_status").val() == "True"){
        $("#open_chat_icon").toggle();
    }
    var sender = $('#handle').val();
    var chatsock;
    var label;
    var timer;
    var page_title = document.title;
    var course_id = $("#course_id").val();

    $("#main").on("click", function(){
        // Open chat window
        var room_url = window.location.protocol + "//" +
                    window.location.host + "/exam/new/chat/" + course_id;
        ajax_request(room_url);

    });

    function ajax_request(chat_url) {
        // Get messages from ajax request
        $.ajax({
            url: chat_url,
            timeout:30000,
            type: "GET",
            dataType: 'json',
            contentType: 'application/json; charset=utf-8',
            success: function(msg) {
                request_success(msg);
            },
            error: function(jqXHR, textStatus) {
                alert("Unable to send messages");
            }
        });
        $("#chat_container").toggle();
    }

    function request_success(msg) {
        // On request success fill data
        label = msg['room_label'];
        create_ws(label);
        $("#msg_base").empty();
        if(msg['success']){
            for (var j=0; j<msg['messages'].length; j++){
                fill_data(msg['success'], msg['messages'][j]);
            }
        }
        else{
            fill_data(msg['success']);
        }
    }

    function create_ws(label) {
        // Create websocket connection with room
        var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
        chatsock = new ReconnectingWebSocket(ws_scheme + '://' + window.location.host +
            "/chat/" + label + "/" + course_id);
        chatsock.onmessage = function(message) {
            if(document.getElementById("no_msg_div") != null){
                $("#msg_base").empty();
            }
            var data = JSON.parse(message.data);
            fill_data(data['success'], data['messages'], "new")
        };
        chatsock.onerror = function(){
            $("#chat_err").toggle();
            chatsock.close();
        }
    }

    $("#chatform").on("submit", function(event) {
        // Submit chat message onto the websocket
        if($('#message').text().trim().length != 0){
            var message = {
                sender_id: sender,
                message: $('#message').html(),
            }
            chatsock.send(JSON.stringify(message));
        }
        $("#message").empty();
        return false;
    });

    // Create divs for showing sent and received messages
    var div_sent = "<div class='row msg_container base_sent'>\n"+
                    "<div class='col-xs-10 col-md-10'>\n" +
                    "<div class='messages msg_sent'>\n"

    var end_div_sent = "</div>\n</div>\n</div>"

    var div_receive = "<div class='row msg_container base_receive'>\n"+
                        "<div class='col-xs-10 col-md-10'>\n"+
                        "<div class='messages msg_receive'>"

    var end_div_receive = "</div>\n</div>\n</div>\n"


    function fill_data(success, msg, mode) {
        // Fill data in chat container
        $("#title").text(" Chat- "+$("#course_name").val());
        if(success){
            var id = msg['sender'];
            if (id == sender){
                // Set as sent message
                var mess = div_receive+"<p id='sender_name'>"+msg['sender_name']+"</p>"+
                            "<p>"+msg['message']+"</p>"+
                            "<p id='msg_time'>"+ msg['timestamp']+"</p>"+
                            end_div_receive;
            }
            else{
                if(mode=="new"){
                    $(".top-bar").css("background", "#32CD32");
                    timer = setInterval(function() {toggle_title(msg['sender_name']);}, 1500);
                }
                // Set as received message
                var mess = div_sent+"<p id='receiver_name'>"+msg['sender_name']+"</p>"+
                            "<p>"+msg['message']+"</p>"+
                            "<p id='msg_time'>"+ msg['timestamp']+"</p>"+
                            end_div_sent;
            }
            $("#msg_base").append(mess);
            $("#msg_base").stop().animate({
                scrollTop: $("#msg_base")[0].scrollHeight}, 10);
            }
        else {
            var no_msg_div = "<div class='text-center col-md-4' id='no_msg_div'>"+
                            "<span id='no_msg'>"+"No Messages"+"</span>"+
                            "</div>";
            $("#msg_base").scrollTop();
            $("#msg_base").append(no_msg_div);
            }
    }

    function toggle_title(sender) {
        if (document.title == page_title) { document.title =  sender + ' messsaged you'; }
        else { document.title = page_title; }
    }

    // Chat box functions
    $(document).on('click', '.panel-heading span.icon_minim', function (e) {
        // Minimize chat window and change icon
        var $this = $(this);
        if (!$this.hasClass('panel-collapsed')) {
            $this.parents('.panel').find('.panel-body').slideUp();
            $this.addClass('panel-collapsed');
            $this.removeClass('glyphicon-minus').addClass('glyphicon-plus');
        } else {
            $this.parents('.panel').find('.panel-body').slideDown();
            $this.removeClass('panel-collapsed');
            $this.removeClass('glyphicon-plus').addClass('glyphicon-minus');
        }
    });

    $(document).on('click', '.icon_close', function (e) {
        // Close chat window
        $("#chat_container").hide();
        chatsock.close();
    });

    $(document).on('click', '#message', function (e) {
        // Change title background on receiving new message
        $(".top-bar").css("background", "#666");
        clearInterval(timer);
        document.title = page_title;
    });

});
