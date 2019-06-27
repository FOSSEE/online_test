const courseSelectField = $("#courses");

courseSelectField.change(function(e) {
  const { value } = e.target;

  $("#unit-group")
    .html("")
    .load(`/permissions/units/get/?course_id=${value}`);
});
