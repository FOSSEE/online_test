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

function setSelectionRange(input, selectionStart, selectionEnd) 
{
    if (input.setSelectionRange) 
    {
		input.focus();
		input.setSelectionRange(selectionStart, selectionEnd);
    }
    else if (input.createTextRange) 
    {
		var range = input.createTextRange();
		range.collapse(true);
		range.moveEnd('character', selectionEnd);
		range.moveStart('character', selectionStart);
		range.select();
    }
}

function replaceSelection (input, replaceString) 
{
    if (input.setSelectionRange) 
    {
		var selectionStart = input.selectionStart;
		var selectionEnd = input.selectionEnd;
		input.value = input.value.substring(0, selectionStart)+ replaceString + input.value.substring(selectionEnd);
		if (selectionStart != selectionEnd)
		{ 
			setSelectionRange(input, selectionStart, selectionStart + 	replaceString.length);
		}
		else
		{
			setSelectionRange(input, selectionStart + replaceString.length, selectionStart + replaceString.length);
		}
    }
    else if (document.selection) 
    {
		var range = document.selection.createRange();
		if (range.parentElement() == input) 
		{
			var isCollapsed = range.text == '';
			range.text = replaceString;
			if (!isCollapsed)  
			{
				range.moveStart('character', -replaceString.length);
				range.select();
			}
		}
    }
}

function autoresize()
{
    var ta = document.getElementById('answer');
    var divta = document.getElementById('AnswerWithLines');
    ta.style.height="";
    var height = ta.scrollHeight;
    ta.style.height = 'auto';
    ta.style.height = height+'px';
    divta.style.height = height+'px';
}

function catchTab(item,e)
{
    if(navigator.userAgent.match("Gecko"))
    {
		c=e.which;
    }
    else
    {
		c=e.keyCode;
    }
    if(c==9)
    {
		replaceSelection(item,String.fromCharCode(9));
		setTimeout("document.getElementById('"+item.id+"').focus();",0);	
		return false;
    }
}

var lineObjOffsetTop = 0;

function addLineNumbers(id)
{
    var el = document.createElement('DIV');
    var ta = document.getElementById(id);
    var content = document.getElementById('snippet').value;
    ta.parentNode.insertBefore(el,ta);
    el.appendChild(ta);
    el.style.width = (ta.offsetWidth + 30) + 'px';
    ta.style.position = 'absolute';
    ta.style.left = '30px';
    ta.scrollHeight=""
    el.style.border = 'none';
    el.style.overflow='hidden';
    el.style.position = 'relative';
    el.style.width = (ta.offsetWidth + 30) + 'px';
    var lineObj = document.createElement('DIV');
    lineObj.style.position = 'absolute';
    lineObj.style.top = lineObjOffsetTop + 'px';
    lineObj.style.width = '27px';
    lineObj.style.fontSize= '18px';
    lineObj.style.foregroundColor='black';
    el.insertBefore(lineObj,ta);
    lineObj.style.textAlign = 'right';
    lineObj.className='lineObj';
    var string = '';
    split_content = content.split('\n');
    if(id == "answer")
    {
                el.className='AnswerWithLines';
                el.id='AnswerWithLines';
                el.style.height = (ta.scrollHeight) + 'px';
		for(var no=split_content.length+1;no<1000;no++)
		{
			if(string.length>0)string = string + '<br>';
			string = string + no;
		}
	}
	else
	{
                el.className='SnippetWithLines';
                el.id='SnippetWithLines';
                el.style.height = (ta.scrollHeight) + 'px';
		for(var no=1;no<=split_content.length;no++)
		{
			if(string.length>0)string = string + '<br>';
			string = string + no;
		}
	}
	ta.onmousedown = function() { positionLineObj(lineObj,ta); };
    ta.onscroll = function() { positionLineObj(lineObj,ta); };
    ta.onblur = function() { positionLineObj(lineObj,ta); };
    ta.onfocus = function() { positionLineObj(lineObj,ta); };
    ta.onmouseover = function() { positionLineObj(lineObj,ta); };
    ta.onkeyup = function(){autoresize();};
    lineObj.innerHTML = string;
}
       
function positionLineObj(obj,ta)
{
    obj.style.top = (ta.scrollTop * -1 + lineObjOffsetTop) + 'px';  
}
