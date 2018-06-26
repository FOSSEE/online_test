function form_load()
{
    var tags = document.getElementsByName('tags');
    
    for (var i=0;i<tags.length;i++)
    {
        tags[i].id = tags[i].id + i;
    }
}
