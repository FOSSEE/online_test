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

function setSelectionRange(input, selectionStart, selectionEnd) {
  if (input.setSelectionRange) {
    input.focus();
    input.setSelectionRange(selectionStart, selectionEnd);
  }
  else if (input.createTextRange) {
    var range = input.createTextRange();
    range.collapse(true);
    range.moveEnd('character', selectionEnd);
    range.moveStart('character', selectionStart);
    range.select();
  }
}

function replaceSelection (input, replaceString) {
	if (input.setSelectionRange) {
		var selectionStart = input.selectionStart;
		var selectionEnd = input.selectionEnd;
		input.value = input.value.substring(0, selectionStart)+ replaceString + input.value.substring(selectionEnd);
    
		if (selectionStart != selectionEnd){ 
			setSelectionRange(input, selectionStart, selectionStart + 	replaceString.length);
		}else{
			setSelectionRange(input, selectionStart + replaceString.length, selectionStart + replaceString.length);
		}

	}else if (document.selection) {
		var range = document.selection.createRange();

		if (range.parentElement() == input) {
			var isCollapsed = range.text == '';
			range.text = replaceString;

			 if (!isCollapsed)  {
				range.moveStart('character', -replaceString.length);
				range.select();
			}
		}
	}
}


// We are going to catch the TAB key so that we can use it, Hooray!
function catchTab(item,e){
	if(navigator.userAgent.match("Gecko")){
		c=e.which;
	}else{
		c=e.keyCode;
	}
	if(c==9){
		replaceSelection(item,String.fromCharCode(9));
		setTimeout("document.getElementById('"+item.id+"').focus();",0);	
		return false;
	}
		    
}

var lineObjOffsetTop = 2;
       
       function createTextAreaWithLines(id)
       {
          var el = document.createElement('DIV');
          var ta = document.getElementById(id);
          ta.parentNode.insertBefore(el,ta);
          el.appendChild(ta);
         
          el.className='textAreaWithLines';
          el.style.width = (ta.offsetWidth + 30) + 'px';
          ta.style.position = 'absolute';
          ta.style.left = '30px';
          el.style.height = (ta.offsetHeight + 2) + 'px';
          el.style.overflow='hidden';
          el.style.position = 'relative';
          el.style.width = (ta.offsetWidth + 30) + 'px';
          var lineObj = document.createElement('DIV');
          lineObj.style.position = 'absolute';
          lineObj.style.top = lineObjOffsetTop + 'px';
          lineObj.style.left = '0px';
          lineObj.style.width = '27px';
          el.insertBefore(lineObj,ta);
          lineObj.style.textAlign = 'right';
          lineObj.className='lineObj';
          var string = '';
          for(var no=1;no<200;no++){
             if(string.length>0)string = string + '<br>';
             string = string + no;
          }
         
          //ta.onkeydown = function() { positionLineObj(lineObj,ta); };
          ta.onmousedown = function() { positionLineObj(lineObj,ta); };
          ta.onscroll = function() { positionLineObj(lineObj,ta); };
          ta.onblur = function() { positionLineObj(lineObj,ta); };
          ta.onfocus = function() { positionLineObj(lineObj,ta); };
          ta.onmouseover = function() { positionLineObj(lineObj,ta); };
          lineObj.innerHTML = string;
         
       }
       
       function positionLineObj(obj,ta)
       {
          obj.style.top = (ta.scrollTop * -1 + lineObjOffsetTop) + 'px';  
       
         
       }
       

