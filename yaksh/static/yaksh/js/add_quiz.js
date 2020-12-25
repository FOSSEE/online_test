function test()
{
	document.getElementById('id_duration').setAttribute('class','mini-text form-control');
	document.getElementById('id_pass_criteria').setAttribute('class','mini-text form-control');
  tinymce.init({
      selector: 'textarea#id_instructions',
      setup : function(ed) {
            ed.on('change', function(e) {
               tinymce.triggerSave();
            });
      },
      max_height: 400,
      height: 400,
      plugins: "image code link",
      convert_urls: false
  });
}

String.prototype.beginsWith = function (string) {
    return(this.indexOf(string) === 0);
};

function usermode(location)
{
  window.location.replace(location);
}
