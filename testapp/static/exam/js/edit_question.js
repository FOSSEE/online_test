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
	var type = document.getElementsByName('type');
    var tags = document.getElementsByName('tags');
	
	for (var i=0;i<point.length;i++)
	{
		point[i].id = point[i].id + i;
		descriptions[i+1].id=descriptions[i+1].id + i;
		test[i].id=test[i].id + i;
		option[i].id=option[i].id + i;
		type[i].id = type[i].id + i;
        tags[i].id = tags[i].id + i;
	}

	for(var i=0;i<point.length;i++)
	{
		var point_id = document.getElementById('id_points'+i);
		point_id.setAttribute('class','mini-text');
    
        var tags_id = document.getElementById('id_tags'+i);
		tags_id.setAttribute('class','ac_input');
        tags_id.setAttribute('autocomplete','off');
       
        jQuery().ready(function() 
        { 
            jQuery("#id_tags" + i).autocomplete("/taggit_autocomplete_modified/json", { multiple: true }); 
        });
    		
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

		var option_id = document.getElementById('id_options' + i);
		option_id.onfocus = gainfocus;
		option_id.onblur = lostfocus;
		
		if(value != 'mcq')
		{
			document.getElementById('id_options'+i).style.visibility='hidden';
			document.getElementById('label_option'+(i+1)).innerHTML = "";

		}

		document.getElementById('my'+ (i+1)).innerHTML = desc_id.value;
	}
}

function showOptions(e)
{
		var value = this.value;
		var no = parseInt(this.id.substring(this.id.length-1));
		if( value == 'mcq')
		{	
			document.getElementById('id_options'+no).style.visibility = 'visible';
			document.getElementById('label_option'+ (no+1)).innerHTML = "Options : "
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

function autosubmit()
{
	var total_form = document.getElementsByName('summary').length;
	var empty_options = 0 ;
	var count_mcq = 0;
		
	for (var i=0;i<total_form;i++)
	{
		if (document.getElementById('id_type' + i).value != 'mcq')
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
