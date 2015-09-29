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
