      var time_left = {{ time_left }};
      function submitCode()
      {
	    document.forms["code"].submit();
	    var x = document.getElementById("status");
	    x.innerHTML = "<strong>Checking answer ...</strong>";
	    x = document.getElementById("check");
	    x.disabled = true;
	    x.value = "Checking Answer ...";
	    document.getElementById("skip").disabled = true;
      }
      
      function secs_to_time(secs)
      {
	    var h = Math.floor(secs/3600);
	    var h_s = (h > 0) ? h+'h:' : '';
    	    var m = Math.floor((secs%3600)/60);
	    var m_s = (m > 0) ? m+'m:' : '';
	    var s_s = Math.floor(secs%60) + 's';
	    return h_s + m_s + s_s;
      }

      function update_time()
      {
	    time_left -= 1;
	    if (time_left) 
            {
	            var elem = document.getElementById("time_left");
		    var t_str = secs_to_time(time_left);
		    elem.innerHTML = "<strong>" + t_str + "</strong>";
	            setTimeout("update_time()", 1000);
            }
	    else 
            {
		    document.forms["code"].submit();
    	    }	
      }
