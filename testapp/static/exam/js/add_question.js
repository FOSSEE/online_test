function increase(frm)
{
	if(frm.points.value == "")
	{
		frm.points.value = "0.5";
		return;
	}
	frm.points.value = parseFloat(frm.points.value) + 0.5;
}

function decrease(frm)
{
	if(frm.points.value > 0)
	{
		frm.points.value = parseFloat(frm.points.value) - 0.5;
	}
	else
	{
		frm.points.value=0;
	}

	
}

function textareaformat()
{

	document.getElementById('id_type').setAttribute('class','select-type');
	
	document.getElementById('id_points').setAttribute('class','mini-text');
    document.getElementById('id_tags').setAttribute('class','tag-text');

	$('#id_description').bind('focus', function( event ){
         document.getElementById("id_description").rows=5;
         document.getElementById("id_description").cols=40;
      });

	$('#id_description').bind('blur', function( event ){
         document.getElementById("id_description").rows=1;
         document.getElementById("id_description").cols=40;
      });
	
	$('#id_description').bind('keypress', function (event){
		document.getElementById('my').innerHTML = document.getElementById('id_description').value ;
	});

	$('#id_test').bind('focus', function( event ){
         document.getElementById("id_test").rows=5;
         document.getElementById("id_test").cols=40;
      });

	$('#id_test').bind('blur', function( event ){
         document.getElementById("id_test").rows=1;
         document.getElementById("id_test").cols=40;
      });
	$('#id_options').bind('focus', function( event ){
         document.getElementById("id_options").rows=5;
         document.getElementById("id_options").cols=40;
      });

	$('#id_options').bind('blur', function( event ){
         document.getElementById("id_options").rows=1;
         document.getElementById("id_options").cols=40;
      });
	
	$('#id_type').bind('change',function(event){
		var value = document.getElementById('id_type').value;
		if(value == 'mcq')
		{
			document.getElementById('id_options').style.visibility='visible';
			document.getElementById('label_option').innerHTML="Options :"

		}
		else
		{
			document.getElementById('id_options').style.visibility='hidden';
			document.getElementById('label_option').innerHTML = "";
		}
	});

		document.getElementById('my').innerHTML = document.getElementById('id_description').value ;
		var value = document.getElementById('id_type').value;
		if(value == 'mcq')
		{
			document.getElementById('id_options').style.visibility='visible';
			document.getElementById('label_option').innerHTML="Options :"

		}
		else
		{
			document.getElementById('id_options').style.visibility='hidden';
			document.getElementById('label_option').innerHTML = "";
		}	
}

function autosubmit()
{
	if (document.getElementById('id_type').value == 'mcq')
	{
		var value = document.getElementById('id_options').value;
		if(value.split('\n').length != 4)
		{
			alert("Enter 4 options. One option per line.");
			return false;
		}
		return true;
	}

}
