$(document).ready(function() {
    if ($("#chat_status").val() == "True" && $("#quiz_status").val() == "False"){
        $("#open_chat_icon").toggle();
    }
    var sender = $('#handle').val();
    var chatsock;
    var label;
    var timer;
    var page_title = document.title;
    var course_id = $("#course_id").val();
    var room_url = window.location.protocol + "//" +
                    window.location.host + "/exam/chat/start_room/" + course_id;

    $("#open_chat").click(function() {
        $('#message').html("@" + $("#user").html());
        ajax_request(room_url);
        if(!$("#chat_container").is(':visible')) {
            $("#chat_container").toggle();
        }
    });

    $("#main").on("click", function(){
        // Open chat window
        ajax_request(room_url);
    });

    function ajax_request(chat_url) {
        // Get messages from ajax request
        $.ajax({
            url: chat_url,
            timeout:15000,
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
        if(msg['success']) {
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
            fill_data(data['success'], data['messages'], "new");
        };
        chatsock.onerror = function(){
            $("#chat_err").toggle();
            chatsock.close();
        };
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
    function get_sent_message_div(user_name, message, time) {

        // Create div for showing sent messages
        var div_sent = document.createElement("div");
        div_sent.setAttribute("class", "row msg_container base_sent");

        var sent_col_div = document.createElement("div");
        sent_col_div.setAttribute("class", "col-xs-10 col-md-8");

        var sent_msg_div = document.createElement("div");
        sent_msg_div.setAttribute("class", "messages msg_sent");

        var par_user = document.createElement("p");
        par_user.setAttribute("id", "sender_name");
        var user_text = document.createTextNode(user_name);
        par_user.appendChild(user_text);

        var par_time = document.createElement("p");
        par_time.setAttribute("id", "msg_time");
        var time_text = document.createTextNode(convert_date_time(time));
        par_time.appendChild(time_text);

        var par_msg = document.createElement("p");
        par_msg.setAttribute("id", "chat_msg");
        var msg_text = document.createElement("div");
        msg_text.innerHTML = message;
        par_msg.appendChild(msg_text);

        sent_msg_div.appendChild(par_user);
        sent_msg_div.appendChild(par_msg);
        sent_msg_div.appendChild(par_time);
        sent_col_div.appendChild(sent_msg_div);
        div_sent.appendChild(sent_col_div);

        return div_sent;
    }

    function get_receive_message_div(user_name, message, time) {

        // Create div for showing received messages
        var div_receive = document.createElement("div");
        div_receive.setAttribute("class", "row msg_container base_receive");

        var receive_col_div = document.createElement("div");
        receive_col_div.setAttribute("class", "col-xs-10 col-md-8");

        var receive_msg_div = document.createElement("div");
        receive_msg_div.setAttribute("class", "messages msg_receive");

        var par_user = document.createElement("p");
        par_user.setAttribute("id", "receiver_name");
        var user_text = document.createTextNode(user_name);
        par_user.appendChild(user_text);

        var par_time = document.createElement("p");
        par_time.setAttribute("id", "msg_time");
        var time_text = document.createTextNode(convert_date_time(time));
        par_time.appendChild(time_text);

        var par_msg = document.createElement("p");
        par_msg.setAttribute("id", "chat_msg");
        var msg_text = document.createElement("div");
        msg_text.innerHTML = message;
        par_msg.appendChild(msg_text);

        receive_msg_div.appendChild(par_user);
        receive_msg_div.appendChild(par_msg);
        receive_msg_div.appendChild(par_time);
        receive_col_div.appendChild(receive_msg_div);
        div_receive.appendChild(receive_col_div);

        return div_receive;
    }

    function get_no_message_div(){

        // Create a div for no message
        var msg_div = document.createElement("div");
        msg_div.setAttribute("class", "text-center col-md-4");
        msg_div.setAttribute("id", "no_msg_div");

        var msg_span = document.createElement("span");
        msg_span.setAttribute("id", "no_msg");
        var msg_text = document.createTextNode("No Messages");
        msg_span.appendChild(msg_text);
        msg_div.appendChild(msg_span);

        return msg_div;
    }

    function convert_date_time(utc_time){
        // Convert utc time to local timezone
        var local_time;
        var user_tz = $("#user_tz").val();
        var local_tz = moment.tz.zone(user_tz);
        if (local_tz != null){
            local_time = moment.utc(utc_time).tz(user_tz).format("YYYY-MM-DD HH:mm A");
        }
        else {
            local_time = moment.utc(utc_time).format("YYYY-MM-DD HH:mm A");
        }
        return local_time;
    }

    function fill_data(success, msg, mode) {
        // Fill data in chat container
        $("#title").text(" Chat- "+$("#course_name").val());
        if(success){
            var id = msg['sender'];
            if (id == sender){
                // Set as sent message
                var mess = get_sent_message_div(msg.sender_name, msg.message, msg.timestamp);
            }
            else{
                if(mode=="new"){
                    $(".top-bar").css("background", "#32CD32");
                    timer = setInterval(function() {toggle_title(msg['sender_name']);}, 1500);
                }
                // Set as received message
                var mess = get_receive_message_div(msg.sender_name, msg.message, msg.timestamp);
            }
            $("#msg_base").append(mess);
            $("#msg_base").stop().animate({
                scrollTop: $("#msg_base")[0].scrollHeight}, 10);
            }
        else {
            var no_msg_div = get_no_message_div();
            $("#msg_base").scrollTop();
            $("#msg_base").append(no_msg_div);
            }
    }

    function toggle_title(sender) {
        if (document.title == page_title) { document.title =  sender + ' sent a messsage'; }
        else { document.title = page_title; }
    }

    // Chat box functions
    $(document).on('click', '.panel-heading span.icon_minim', function (e) {
        // Minimize chat window and change icon
        var $this = $(this);
        if (!$this.hasClass('panel-collapsed')) {
            $this.parents('.panel').find('.panel-body').slideUp();
            $this.addClass('panel-collapsed');
            $this.removeClass('fa-minus').addClass('fa-plus');
        } else {
            $this.parents('.panel').find('.panel-body').slideDown();
            $this.removeClass('panel-collapsed');
            $this.removeClass('fa-plus').addClass('fa-minus');
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
