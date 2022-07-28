import glob
import os
import re
import shutil

from actions_server import JsonGet, http_server, Redirect, StaticResources, ProcessFileUploadThenRedirect, UploadedFile, JsonOkResponse, \
    ErrorResponse
from apscheduler.schedulers.background import BackgroundScheduler
from bootstrap.bootstrap import start_service
from bootstrap.storage import Storage

from FilesStorageResources import FilesStorageResources
from MobiReader import MobiReader

config, logger, timezone = start_service()

PORT = config.get('port', 8077)
STORAGE_DIR = os.getenv('STORAGE', '/app/data')
STORAGE = Storage(STORAGE_DIR)
MOBI_STORAGE = STORAGE.open_files_storage('mobi')
METADATA_STORAGE = STORAGE.open_key_value_storage('books')
COVER_STORAGE = STORAGE.open_files_storage('covers')
IMPORT_DIR = f'{STORAGE_DIR}/import'

scheduler = BackgroundScheduler(timezone=timezone)


def sanitize_file_name(name):
    return re.sub('[^a-zA-Z0-9_.]', '-', name)

def check_for_imports():
    logger.info(f'Checking for new ebooks in {IMPORT_DIR}')
    os.makedirs(IMPORT_DIR, exist_ok=True)
    mobi_paths = glob.glob(f'{IMPORT_DIR}/**/*.mobi', recursive=True)
    for mobi_path in mobi_paths:
        logger.info(f'Found new ebook: {mobi_path}')
        with MobiReader(mobi_path) as reader:
            filename = sanitize_file_name(os.path.basename(mobi_path))
            if filename in MOBI_STORAGE:
                logger.warning(f'ebook {filename} already exists; overwriting!')
            cover = reader.cover_tmp_path
            if cover is None:
                cover = './resources/cover.jpg'
            MOBI_STORAGE[filename] = mobi_path
            COVER_STORAGE[f'{filename}.jpg'] = cover
            METADATA_STORAGE[filename] = {
                'id': filename,
                'title': reader.title,
                'authors': reader.authors,
                'cover': f'{filename}.jpg'
            }
    for file in os.listdir(IMPORT_DIR):
        os.unlink(f'{IMPORT_DIR}/{file}')
    logger.info('Import finished - imported %s files' % len(mobi_paths))


def books(params):
    result = []
    for ebook in METADATA_STORAGE:
        id = ebook['id']
        data = {
            'title': ebook['title'],
            'authors': ebook['authors'],
            'mobi': f'/mobi/{id}',
            'cover': '/cover/' + ebook['cover']
        }
        result.append(data)
    return result


def process_upload(params, files):
    uploaded_file: UploadedFile = files['file']
    filename = sanitize_file_name(uploaded_file.original_file_name)
    if not filename.endswith('.mobi'):
        return ErrorResponse(400, "Uploaded file is not a .mobi file")
    tmpfile_path = f'{IMPORT_DIR}/{filename}'
    uploaded_file.save_as(tmpfile_path)
    os.chmod(tmpfile_path, 0o777)
    check_for_imports()
    return 'upload.html?status=ok'


ACTIONS = [
    JsonGet('/books', books),
    Redirect('/', '/index.html'),
    ProcessFileUploadThenRedirect('/process-upload', process_upload),
    FilesStorageResources('/mobi/', MOBI_STORAGE),
    FilesStorageResources('/cover/', COVER_STORAGE),
    StaticResources('/', './src/web'),
]

check_for_imports()
scheduler.add_job(check_for_imports, 'interval', seconds=config['refresh-interval-seconds'])
scheduler.start()
server = http_server(PORT, ACTIONS)
try:
    server.start(block_caller_thread=True)
finally:
    logger.info('Closing server')
    server.stop()
