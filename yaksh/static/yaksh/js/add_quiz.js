function test()
{

	document.getElementById('id_duration').setAttribute('class','mini-text form-control');
	document.getElementById('id_pass_criteria').setAttribute('class','mini-text form-control');
    if (document.getElementById("id_description").value != "")
    {
        document.getElementById("submit").innerHTML = "Save";
    }
    var template = "<p id='rendered_text' align='justify'></p>";
    $(template).insertBefore("#id_instructions");
    $('#id_instructions').keypress(function (event){
    document.getElementById('rendered_text').innerHTML = document.getElementById('id_instructions').value ;
  });
    document.getElementById('rendered_text').innerHTML = document.getElementById('id_instructions').value ;
}

String.prototype.beginsWith = function (string) {
    return(this.indexOf(string) === 0);
};

function usermode(location)
{
  window.location.replace(location);
}
