import os
import uuid
from werkzeug.utils import secure_filename


def allowed_file(filename, allowed_extensions):
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in allowed_extensions
    )


def save_upload(file, upload_dir, allowed_extensions):
    """Save an uploaded file and return (stored_filename, original_name)."""
    if not file or not file.filename:
        return None, None
    if not allowed_file(file.filename, allowed_extensions):
        raise ValueError('File type not allowed')

    original = secure_filename(file.filename)
    ext = original.rsplit('.', 1)[1].lower()
    stored = f'{uuid.uuid4().hex}.{ext}'
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, stored))
    return stored, original
