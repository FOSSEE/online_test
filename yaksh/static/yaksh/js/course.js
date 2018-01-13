$(document).ready(function(){
$(".checkall").change( function(){
        if($(this).prop("checked")) {
                $("#enroll-all input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#enroll-all input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });
$(".enroll").change( function(){
        if($(this).prop("checked")) {
                $("#enroll input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#enroll input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });
$(".reject").change( function(){
        if($(this).prop("checked")) {
                $("#reject input:checkbox").each(function(index, element) {
                $(this).prop('checked', true);
                });
        }
        else {
                $("#reject input:checkbox").each(function(index, element) {
                $(this).prop('checked', false);
                });
        }
    });

$(function() {
    tinymce.init({ 
        selector: 'textarea#email_body',
        max_height: 200,
        height: 200
    });
  });

$("#send_mail").click(function(){
    var subject = $("#subject").val();
    var body = tinymce.get("email_body").getContent();
    var status = false;
    var selected = [];
    $('#reject input:checked').each(function() {
        selected.push($(this).attr('value'));
    });
    if (subject == '' || body == ''){
        $("#error_msg").html("Please enter mail details");
        $("#dialog").dialog();
    }
    else if (selected.length == 0){
        $("#error_msg").html("Please select atleast one user");
        $("#dialog").dialog();
    }
    else {
        status = true;
    }
    return status;
});

// Download course status as csv
function exportTableToCSV($table, filename) {
    var $headers = $table.find('tr:has(th)')
        ,$rows = $table.find('tr:has(td)')

        // Temporary delimiter characters unlikely to be typed by keyboard
        // This is to avoid accidentally splitting the actual contents
        ,tmpColDelim = String.fromCharCode(11) // vertical tab character
        ,tmpRowDelim = String.fromCharCode(0) // null character

        // actual delimiter characters for CSV format
        ,colDelim = '","'
        ,rowDelim = '"\r\n"';

        // Grab text from table into CSV formatted string
        var csv = '"';
        csv += formatRows($headers.map(grabRow));
        csv += rowDelim;
        csv += formatRows($rows.map(grabRow)) + '"';

        // Data URI
        var csvData = 'data:application/csv;charset=utf-8,' + encodeURIComponent(csv);

    // For IE (tested 10+)
    if (window.navigator.msSaveOrOpenBlob) {
        var blob = new Blob([decodeURIComponent(encodeURI(csv))], {
            type: "text/csv;charset=utf-8;"
        });
        navigator.msSaveBlob(blob, filename);
    } else {
        $(this)
            .attr({
                'download': filename,'href': csvData
        });
    }

    function formatRows(rows){
        return rows.get().join(tmpRowDelim)
            .split(tmpRowDelim).join(rowDelim)
            .split(tmpColDelim).join(colDelim);
    }
    // Grab and format a row from the table
    function grabRow(i,row){
        var $row = $(row);
        var $cols = $row.find('td'); 
        if(!$cols.length) $cols = $row.find('th');

        return $cols.map(grabCol)
                    .get().join(tmpColDelim);
    }
    // Grab and format a column from the table 
    function grabCol(j,col){
        var $col = $(col),
            $text = $col.text();

        return $text.replace('"', '""').replace("View Unit Status", '').replace("View Units", ""); // escape double quotes

    }
}


$("#export").click(function (event) {
    var outputFile = $("#course_name").val().replace(" ", "_") + '.csv';

    exportTableToCSV.apply(this, [$('#course_table'), outputFile]);
});

});

function view_status(unit){
    title_list = $(unit).attr("title").split("/");
    $(unit).attr("title", title_list.join("\n"));
}
