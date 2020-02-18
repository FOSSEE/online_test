window.onload = function() {
    document.getElementById("listbtn").onclick = function() {
        showListView();
        localStorage.setItem('.courseview', 'list');
        return false;
    };

    document.getElementById("gridbtn").onclick = function() {
        showGridView();
        localStorage.setItem('.courseview', 'grid');
        return false;
    };

    let itemClass = localStorage.getItem('.courseview');

    if(itemClass == "list") {
        showListView();
    } else {
        showGridView();
    }

    function showListView() {
        $('#listview').addClass('active');
        $('#listview').removeClass('fade');
        $('#gridview').addClass('fade');
        $('#gridview').removeClass('active');
        $('#listbtn').addClass('active');
        $('#gridbtn').removeClass('active');
    }

    function showGridView() {
        $('#listview').addClass('fade');
        $('#listview').removeClass('active');
        $('#gridview').addClass('active');
        $('#gridview').removeClass('fade');
        $('#gridbtn').addClass('active');
        $('#listbtn').removeClass('active');
    }
}