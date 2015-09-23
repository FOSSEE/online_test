function render_question(frm)
{
    for(var i=1;i<=frm.description.length;i++)
    {
        document.getElementById('my'+i).innerHTML = frm.description[i-1].value;
    }
   
}

function increase(frm,n)
{
	var newValue = document.getElementById('id_points'+ (n-1)).value ;
		
	if( newValue == "")
	{
		document.getElementById('id_points'+(n-1)).value = "0.5";
		return;
	}
	document.getElementById('id_points' + (n-1)).value = parseFloat(newValue) + 0.5;
}

function decrease(frm,n)
{
	var newValue = document.getElementById('id_points'+ (n-1)).value ;
		
	if( newValue > 0)
	{
		document.getElementById('id_points' + (n-1)).value = parseFloat(newValue) - 0.5;
	}
	else
	{
		document.getElementById('id_points' + (n-1)).value = 0;
	}
}

function grade_data(showHideDiv)
{
       var ele=document.getElementById(showHideDiv);
       if (ele.style.display=="block")
       {
               ele.style.display = "none";
       }
       else
       {
               ele.style.display = "block";
       }
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

function data(showContent,showHideDiv,a,summary)
{
    var con = document.getElementById(showContent);
    var ele=document.getElementById(showHideDiv);
    var atag=document.getElementById(a);
    if (ele.style.display=="block")
    {
        con.style.display = "none"
        ele.style.display = "none";
		atag.text = summary;
    }
    else
    {
        con.style.display = "block";
        ele.style.display = "block";
    }
}

function textareaformat()
{
	var point = document.getElementsByName('points');
	var test =  document.getElementsByName('test');
	var option =  document.getElementsByName('options');
	var descriptions = document.getElementsByName('description');
	var snippets = document.getElementsByName('snippet');
	var language = document.getElementsByName('language')
	var type = document.getElementsByName('type');
    var tags = document.getElementsByName('tags');
	for (var i=0;i<point.length;i++)
	{
		point[i].id = point[i].id + i;
		descriptions[i+1].id=descriptions[i+1].id + i;
		test[i].id=test[i].id + i;
		snippets[i].id=snippets[i].id + i; 
		option[i].id=option[i].id + i;
		type[i].id = type[i].id + i;
		language[i].id = language[i].id + i;
        tags[i].id = tags[i].id + i;
	}
	for(var i=0;i<point.length;i++)
	{
		var point_id = document.getElementById('id_points'+i);
		point_id.setAttribute('class','mini-text');
	        var tags_id = document.getElementById('id_tags'+i);
		tags_id.setAttribute('class','ac_input');
        	tags_id.setAttribute('autocomplete','off');
		var language_id = document.getElementById('id_language'+i);
		var type_id = document.getElementById('id_type'+i);
		type_id.setAttribute('class','select-type');
		type_id.onchange = showOptions;
		var value = type_id.value;
		var desc_id = document.getElementById('id_description'+i);
		desc_id.onfocus = gainfocus;
		desc_id.onblur = lostfocus;
		var test_id = document.getElementById('id_test' + i);
		test_id.onfocus = gainfocus;
		test_id.onblur = lostfocus;
		var snippet_id = document.getElementById('id_snippet'+i);
		$(snippet_id).bind('focus', function(event){
			console.log("dv")
			this.rows = 5;
		});
		$(snippet_id).bind('keydown', function (event){
			catchTab(snippet_id,event);
		});

		$(language_id).bind('focus', function(event){
		this.style.border = '1px solid #ccc';
		});
		$(type_id).bind('focus', function(event){
		this.style.border = '1px solid #ccc';
		});

		var option_id = document.getElementById('id_options' + i);
		option_id.onfocus = gainfocus;
		option_id.onblur = lostfocus;		
		if(value == 'code' )
		{
			document.getElementById('id_options'+i).style.visibility='hidden';
			document.getElementById('label_option'+(i+1)).innerHTML = "";
		}
		document.getElementById('my'+ (i+1)).innerHTML = desc_id.value;
		jQuery().ready(function(){ 
          		  jQuery("#id_tags" + i).autocomplete("/taggit_autocomplete_modified/json", { multiple: true });
        	});

	}
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

function showOptions(e)
{
		var value = this.value;
		var no = parseInt(this.id.substring(this.id.length-1));
		if( value == 'mcq' || value == 'mcc')
		{	
			document.getElementById('id_options'+no).style.visibility = 'visible';
			document.getElementById('label_option'+ (no+1)).innerHTML = "Options : "
			document.getElementById('label_option'+ (no+1)).style.fontWeight = 'bold';
		}
		else
		{
			document.getElementById('id_options'+no).value = "";
			document.getElementById('id_options'+no).style.visibility = 'hidden';
			document.getElementById('label_option'+ (no+1)).innerHTML = "";
		}
}

function gainfocus(e)
{
	this.rows = 5;
}
function lostfocus(e)
{
	this.rows = 1;
}

function changeColor(element)
{
	element.style.border = 'solid red';
}
function autosubmit()
{
	var total_form = document.getElementsByName('summary').length;
	var empty_options = 0 ;
	var count_mcq = 0;
	var language;
	var type;

	for (var i=0;i<total_form;i++)
	{
		language = document.getElementById('id_language'+i);
	 	type = document.getElementById('id_type'+i);
		if(language.value == 'select')
		{
			changeColor(language);
			return false;
		}
		if(type.value == 'select')
		{
			changeColor(type);
			return false;
		}

		if (document.getElementById('id_type' + i).value == 'code')
		{
			continue;
		}
		else
		{
			count_mcq = count_mcq + 1;
			var options = document.getElementById('id_options' + i).value;
			var total_words = options.split("\n").length ;
			if ( total_words < 4)
				empty_options = empty_options + 1 ;
		}
	}
	if (empty_options > 0)
	{
		alert('Enter 4 options. One option per line.');
		return false;
	}
	return true;
}
