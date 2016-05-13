function test()
{

	document.getElementById('id_duration').setAttribute('class','mini-text');
	document.getElementById('id_pass_criteria').setAttribute('class','mini-text');
	document.getElementById('id_start_date').setAttribute('class','date-text');
    if (document.getElementById("id_description").value != "")
    {
        document.getElementById("submit").innerHTML = "Save";
    }
}

function usermode(location)
{
  var select = document.getElementById("id_prerequisite");
  var select_text = select.options[select.selectedIndex].text;
  window.alert(select_text + " is a prerequisite for this course.\n \
  				You are still allowed to attempt this quiz.")
  window.location.replace(location);
}