function test()
{
    if (document.getElementById("id_description").value != "")
    {
        alert("reached condition");
        document.getElementById("submit").innerHTML = "Save";
    }
}
