function load_data()
{
    var url_root = document.getElementById('url_root').value;
    var value = document.getElementById('mode').value;
    var pathArray = window.location.pathname.split( '/' );
    length = pathArray.length;
    var digit = parseInt(pathArray[length-2]);

    if (! isNaN(digit) && value == 'Automatic') 
    {
         window.location = url_root + "/exam/manage/designquestionpaper/automatic/" + digit;
    }
    else if(!isNaN(digit) && value == 'Manual')
    {
         window.location = url_root + "/exam/manage/designquestionpaper/manual/" + digit;
    }
    else if(value == 'Automatic')
    {
         window.location = window.location.pathname + "automatic";
    }
    else if( value == 'Manual')
    {
         window.location = window.location.pathname + "manual";
    }
}
