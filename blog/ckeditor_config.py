# CKEditor 5 settings
CKEDITOR_5_CUSTOM_CSS = """
    :root {
        --ck-color-text: black;
    }
    .django-ckeditor-5 {
        color: black !important;
    }
    .ck-editor__editable {
        color: black !important;
    }
    .ck-content {
        color: black !important;
    }
"""

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'underline', 'strikethrough', '|',
            'fontSize', 'fontFamily', '|',
            'fontColor', 'fontBackgroundColor', '|',
            'alignment', '|',
            'bulletedList', 'numberedList', '|',
            'link', 'blockQuote', '|',
            'undo', 'redo'
        ],
        'fontSize': {
            'options': [
                9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25
            ]
        },
        'alignment': {
            'options': ['left', 'center', 'right', 'justify']
        },
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraf', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Başlık 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Başlık 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Başlık 3', 'class': 'ck-heading_heading3'}
            ]
        },
    }
}

CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
CKEDITOR_5_UPLOAD_PATH = "uploads/" 