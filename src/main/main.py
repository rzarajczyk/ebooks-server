import glob
import os
import shutil

from actions_server import JsonGet, http_server, Redirect, StaticResources
from apscheduler.schedulers.background import BackgroundScheduler
from bootstrap.bootstrap import start_service

from FileUpload import FileUpload
from FilesStorageResources import FilesStorageResources
from MobiReader import MobiReader
from bootstrap.storage import Storage

config, logger, timezone = start_service()

PORT = config.get('port', 8077)
STORAGE_DIR = os.getenv('STORAGE', '/app/data')
STORAGE = Storage(STORAGE_DIR)
MOBI_STORAGE = STORAGE.open_files_storage('mobi')
METADATA_STORAGE = STORAGE.open_key_value_storage('books')
COVER_STORAGE = STORAGE.open_files_storage('covers')
IMPORT_DIR = f'{STORAGE_DIR}/import'

scheduler = BackgroundScheduler(timezone=timezone)


def check_for_imports():
    logger.info(f'Checking for new ebooks in {IMPORT_DIR}')
    os.makedirs(IMPORT_DIR, exist_ok=True)
    for mobi_path in glob.glob(f'{IMPORT_DIR}/**/*.mobi', recursive=True):
        logger.info(f'Found new ebook: {mobi_path}')
        with MobiReader(mobi_path) as reader:
            filename = os.path.basename(mobi_path)
            if filename in MOBI_STORAGE:
                logger.warning(f'ebook {filename} already exists; overwriting!')
            MOBI_STORAGE[filename] = mobi_path
            COVER_STORAGE[f'{filename}.jpg'] = reader.cover_tmp_path
            METADATA_STORAGE[filename] = {
                'id': filename,
                'title': reader.title,
                'authors': reader.authors,
                'cover': f'{mobi_path}.jpg'
            }
    for file in os.listdir(IMPORT_DIR):
        shutil.rmtree(f'{IMPORT_DIR}/{file}', ignore_errors=True)


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

ACTIONS = [
    JsonGet('/books', books),
    Redirect('/', '/index.html'),
    FileUpload('/process-upload'),
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
