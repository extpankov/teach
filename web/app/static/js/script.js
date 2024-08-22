$(document).ready(function() {
    $('.file-input').on('change', function(e) {
        var file = this.files[0];
        if (!file) {
            return; // Не продолжать, если файл не выбран
        }

        var formData = new FormData();
        formData.append('file', file);

        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function(response) {
                if (response.pdf_filename) {
                    window.open('/pdfs/' + response.pdf_filename, '_blank');
                } else {
                    alert('Ошибка при обработке файла: ' + response.error);
                }
            },
            error: function(xhr, status, error) {
                console.error('Ошибка:', error);
            }
        });
    });
});
