function test()
{

	document.getElementById('id_duration').setAttribute('class','mini-text');
	document.getElementById('id_pass_criteria').setAttribute('class','mini-text');
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
  var select = document.getElementById("id_prerequisite");
  var select_text = select.options[select.selectedIndex].text;
  if (select_text.beginsWith("----")){
  		window.alert("No prerequisite for this course.\n \
  						You can attempt the quiz.");
  		window.location.replace(location);
  } else {
  		window.alert(select_text + " is a prerequisite for this course.\n \
  						You are still allowed to attempt this quiz.")
  window.location.replace(location);	
  	}
  }
