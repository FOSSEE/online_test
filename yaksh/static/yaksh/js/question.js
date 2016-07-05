function submitCode()
{
    document.forms["code"].submit();
    var x = document.getElementById("status");
    x.innerHTML = "<strong>Checking answer ...</strong>";
    x = document.getElementById("check");
    x.disabled = true;
    x.value = "Checking Answer ...";
    if (document.getElementById("skip")!=null) {
    document.getElementById("skip").disabled = true;
    }
}
