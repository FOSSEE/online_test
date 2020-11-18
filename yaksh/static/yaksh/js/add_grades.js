$(function() {
        tinymce.init({
            selector: 'textarea#id_description',
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
    });
