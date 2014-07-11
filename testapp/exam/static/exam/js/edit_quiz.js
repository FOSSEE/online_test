function form_load()
{
    var tags = document.getElementsByName('tags');
	
	for (var i=0;i<tags.length;i++)
	{
        tags[i].id = tags[i].id + i;
	}

	for(var i=0;i<tags.length;i++)
	{
        var tags_id = document.getElementById('id_tags'+i);
		tags_id.setAttribute('class','ac_input');
        tags_id.setAttribute('autocomplete','off');
       
        jQuery().ready(function() 
        { 
            jQuery("#id_tags" + i).autocomplete("/taggit_autocomplete_modified/json", { multiple: true }); 
        });
    }
}
