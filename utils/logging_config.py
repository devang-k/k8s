from logging.handlers import RotatingFileHandler
from elasticsearch import Elasticsearch, exceptions
import datetime
import sys
import os
import time
import psutil
import tracemalloc
from functools import wraps
from dotenv import load_dotenv, find_dotenv
import requests
from requests.auth import HTTPBasicAuth
import logging
import threading
from contextlib import contextmanager
import uuid


env_file = find_dotenv(".env.dev")
load_dotenv(env_file)

ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL')
ELASTICSEARCH_USERNAME = os.getenv('ELASTICSEARCH_USERNAME')
ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD')

KIBANA_URL = os.getenv('KIBANA_URL')
KIBANA_USERNAME = os.getenv('KIBANA_USERNAME_ADMIN')
KIBANA_PASSWORD = os.getenv('KIBANA_PASSWORD_ADMIN')

ENABLE_ELASTIC_LOGGING = os.getenv('ENABLE_ELASTIC_LOGGING', 'true').lower() == 'true'
DEBUG_LEVEL_NUM = 1
WARNING_LEVEL_NUM = 2
PERFORMANCE_LEVEL_NUM = 3
OPERATIONAL_LEVEL_NUM = 4
ERROR_LEVEL_NUM = 5
NO_LOGGING_LEVEL_NUM = 99

logging.addLevelName(DEBUG_LEVEL_NUM, "DEBUG")
logging.addLevelName(WARNING_LEVEL_NUM, "WARNING")
logging.addLevelName(PERFORMANCE_LEVEL_NUM, "PERFORMANCE")
logging.addLevelName(OPERATIONAL_LEVEL_NUM, "OPERATIONAL")
logging.addLevelName(ERROR_LEVEL_NUM, "ERROR")
logging.addLevelName(NO_LOGGING_LEVEL_NUM, "NO_LOGGING")

log_context_storage = threading.local()

def update_logger_levels(elastic_log_level, log_level):
    logger = logging.getLogger('sivista_app')
    logger.setLevel(elastic_log_level)
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            handler.setLevel(log_level)
        elif isinstance(handler, ElasticsearchHandler):
            handler.setLevel(elastic_log_level)
        else:
            handler.setLevel(elastic_log_level)

def set_log_context(job_id, **kwargs):
    elastic_log_level = kwargs.get('elastic_log_level', 99)
    log_level = kwargs.get('log_level', 5)
    context_id = f"{job_id}_{uuid.uuid4()}"
    if not hasattr(log_context_storage, 'contexts'):
        log_context_storage.contexts = {}
    context_data = kwargs.copy()
    context_data['job_id'] = job_id
    log_context_storage.contexts[context_id] = context_data
    setattr(log_context_storage, 'context_id', context_id)
    update_logger_levels(elastic_log_level, log_level)

def clear_log_context():
    context_id = getattr(log_context_storage, 'context_id', None)
    if context_id and hasattr(log_context_storage, 'contexts'):
        log_context_storage.contexts.pop(context_id, None)

def get_log_context():
    context_id = getattr(log_context_storage, 'context_id', None)
    if context_id and hasattr(log_context_storage, 'contexts'):
        return log_context_storage.contexts.get(context_id, {})
    return {}

class ContextFilter(logging.Filter):
    def filter(self, record):
        context_data = get_log_context()
        for key, value in context_data.items():
            setattr(record, key, value)
        return True


class ElasticsearchLogger:
    def __init__(self):
        self.es_connected = False
        if ENABLE_ELASTIC_LOGGING:
            try:
                logging.debug("Attempting to connect to Elasticsearch...")
                self.es = Elasticsearch(
                    [ELASTICSEARCH_URL],
                    basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
                    request_timeout=10,
                    sniff_on_start=False,
                    sniff_on_connection_fail=False
                )
                self.es.ping()
                logging.info("Connected to Elasticsearch successfully.")
                self.es_connected = True
            except exceptions.ConnectionError as e:
                logging.error(f"Failed to connect to Elasticsearch on startup: {e}", exc_info=True)
            except Exception as e:
                logging.error(f"Unexpected error during Elasticsearch connection setup: {e}", exc_info=True)

            self.kibana_url = KIBANA_URL
            self.kibana_auth = (KIBANA_USERNAME, KIBANA_PASSWORD)
            self.kibana_connected = True
        else:
            self.es = None
            self.es_connected = False
            self.kibana_url = None
            self.kibana_auth = None
            self.kibana_connected = False

    def get_index_name(self, cell, project_id, job_id, user_id, log_type):
        return f"{cell}_{project_id}_{job_id}_{user_id}_{log_type}".lower()
    
    def create_kibana_dataview(self, index_name):
        if not ENABLE_ELASTIC_LOGGING or not self.es_connected:
            return

        headers = {
            "kbn-xsrf": "true",
            "Content-Type": "application/json"
        }
        kibana_api_endpoint = f"{self.kibana_url}/api/data_views/data_view"
        
        payload = {
            "data_view": {
                "title": index_name,
                "timeFieldName": "timestamp"
            }
        }

        try:
            response = requests.post(
                kibana_api_endpoint,
                headers=headers,
                json=payload,
                auth=HTTPBasicAuth(KIBANA_USERNAME, KIBANA_PASSWORD),
                timeout=10,
                verify=False
            )
            response.raise_for_status()
            print(f"Kibana Data View '{index_name}' created successfully.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409 or e.response.status_code == 400:
                pass
            else:
                print(f"Error creating Kibana Data View '{index_name}': {e}", file=sys.stderr)
                print(f"Response: {e.response.text}", file=sys.stderr)
        except requests.exceptions.ConnectionError as e:
            print(f"Could not connect to Kibana to create Data View for '{index_name}': {e}", file=sys.stderr)
            self.kibana_connected = False
        except Exception as e:
            print(f"An unexpected error occurred while creating Kibana Data View for '{index_name}': {e}", file=sys.stderr)



    def ensure_index_exists(self, index_name):
        if not ENABLE_ELASTIC_LOGGING or not self.es_connected:
            print(f"Skipping index creation/check: ENABLE_ELASTIC_LOGGING={ENABLE_ELASTIC_LOGGING}, es_connected={self.es_connected}")
            return

        try:
            index_exists = self.es.indices.exists(index=index_name)
            if not index_exists:
                self.es.indices.create(
                    index=index_name,
                    body={
                        "mappings": {
                            "dynamic": True
                        }
                    }
                )
                print(f"Index '{index_name}' created successfully.")
                self.create_kibana_dataview(index_name)
            else:
                # "Index already exists. Skipping creation.
                pass
        except exceptions.ConnectionError as e:
            print(f"Could not connect to Elasticsearch to check/create index '{index_name}': {e}", file=sys.stderr)
            self.es_connected = False
        except Exception as e:
            print(f"An unexpected error occurred while ensuring index exists for '{index_name}': {e}", file=sys.stderr)


    def log_to_es(self, cell, project_id, job_id, user_id, log_type, **kwargs):
        if not ENABLE_ELASTIC_LOGGING or not self.es_connected:
            print(ENABLE_ELASTIC_LOGGING, self.es_connected)
            return

        try:
            index_name = self.get_index_name(cell, project_id, job_id, user_id, log_type)
            print("index_name", index_name)
            self.ensure_index_exists(index_name)

            if self.es_connected:
                log_entry = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "cell": cell,
                    "project_id": project_id,
                    "jobID": job_id,
                    "userID": user_id,
                    "log_type": log_type,
                }
                log_entry.update(kwargs)
                self.es.index(index=index_name, body=log_entry)
        except exceptions.ConnectionError as e:
            print(f"Could not connect to Elasticsearch to log data for '{index_name}': {e}", file=sys.stderr)
            self.es_connected = False
        except Exception as e:
            print(f"Error logging to Elasticsearch for '{index_name}': {e}", file=sys.stderr)

    @classmethod
    def log(cls, cell, project_id, job_id, user_id, log_type, **kwargs):
        if not ENABLE_ELASTIC_LOGGING:
            return

        instance = cls()
        if instance.es_connected:
            instance.log_to_es(cell, project_id, job_id, user_id, log_type, **kwargs)
        else:
            print("Elasticsearch logging is enabled but connection failed. Skipping log.", file=sys.stderr)


class ElasticsearchHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.es_logger = ElasticsearchLogger()
    def setLevel(self, level):
        super().setLevel(level)
        # self.es_logger.setLevel(level)

    def emit(self, record):
        if self.level == NO_LOGGING_LEVEL_NUM:
            return
        log_to_es = getattr(record, 'log_to_es', False)
        if getattr(record, 'log_to_es', False):
            if self.es_logger.es_connected:
                message = self.format(record)
                excluded_keys = [
                    'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                    'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs', 'msg',
                    'name', 'pathname', 'process', 'processName', 'relativeCreated',
                    'stack_info', 'thread', 'threadName', 'log_to_es'
                ]

                log_entry = {
                    key: value for key, value in vars(record).items()
                    if key not in excluded_keys
                }
                
                log_entry["message"] = message
                log_entry["service"] = "Sivista"
                log_entry["log_severity"] = logging.getLevelName(record.levelno)

                if 'job_id' not in log_entry:
                    print("Job ID missing, cannot log to Elasticsearch.", file=sys.stderr)
                    return
                log_entry.setdefault('log_type', 'operation')

                self.es_logger.log_to_es(**log_entry)
            else:
                print("Elasticsearch connection not available. Skipping ES log.", file=sys.stderr)

class CustomLogger(logging.Logger):
    def debug(self, msg, *args, **kwargs):
        if self.isEnabledFor(DEBUG_LEVEL_NUM):  # Level 1
            extra = kwargs.get('extra', {})
            extra['log_to_es'] = True
            self._log(DEBUG_LEVEL_NUM, msg, args, extra=extra)

    def warning(self, msg, *args, **kwargs):
        if self.isEnabledFor(WARNING_LEVEL_NUM):  # Level 2
            extra = kwargs.get('extra', {})
            extra['log_to_es'] = True
            self._log(WARNING_LEVEL_NUM, msg, args, extra=extra)

    def performance(self, msg, *args, **kwargs):
        if self.isEnabledFor(PERFORMANCE_LEVEL_NUM):  # Level 3
            extra = kwargs.get('extra', {})
            extra['log_to_es'] = True
            self._log(PERFORMANCE_LEVEL_NUM, msg, args, extra=extra)

    def operation(self, msg, *args, **kwargs):
        if self.isEnabledFor(OPERATIONAL_LEVEL_NUM):  # Level 4
            extra = kwargs.get('extra', {})
            extra['log_to_es'] = True
            self._log(OPERATIONAL_LEVEL_NUM, msg, args, extra=extra)

    def error(self, msg, *args, **kwargs):
        if self.isEnabledFor(ERROR_LEVEL_NUM):  # Level 5
            extra = kwargs.get('extra', {})
            extra['log_to_es'] = True
            self._log(ERROR_LEVEL_NUM, msg, args, extra=extra)


def format_time(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours} hr")
    if minutes > 0:
        parts.append(f"{minutes} min")
    if seconds > 0 or not parts:
        parts.append(f"{seconds} sec")
    return ' '.join(parts)

def setup_es_logging():
    logging.setLoggerClass(CustomLogger)
    logging.Logger.manager.loggerDict.pop('sivista_app', None)
    logger = logging.getLogger('sivista_app')
    logging.getLogger('elastic_transport').setLevel(NO_LOGGING_LEVEL_NUM)
    logger.setLevel(DEBUG_LEVEL_NUM)

    logger.propagate = False

    if not any(isinstance(f, ContextFilter) for f in logger.filters):
        context_filter = ContextFilter()
        logger.addFilter(context_filter)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(ERROR_LEVEL_NUM)
        formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if not any(isinstance(h, ElasticsearchHandler) for h in logger.handlers):
        logger.es_handler = ElasticsearchHandler()
        logger.es_handler.setLevel(NO_LOGGING_LEVEL_NUM)
        logger.addHandler(logger.es_handler)

    return logger

def setup_logging(log_file):
    logger = logging.getLogger('sivista_app')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.propagate = False

def log_performance(service_name="SiVista", log_type="performance", **log_kwargs):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not ENABLE_ELASTIC_LOGGING:
                return func(*args, **kwargs)

            # Get the current log context
            context = get_log_context()
            elastic_log_level = context.get('elastic_log_level', NO_LOGGING_LEVEL_NUM)

            # Check if elastic_log_level allows performance logging (elastic_log_level <= PERFORMANCE_LEVEL_NUM)
            if elastic_log_level > PERFORMANCE_LEVEL_NUM:
                return func(*args, **kwargs)

            tracemalloc_started = False
            try:
                process = psutil.Process(os.getpid())
                memory_before_execution = process.memory_info().rss / (1024 * 1024)
                tracemalloc.start()
                tracemalloc_started = True
                start_snapshot = tracemalloc.take_snapshot()
                start_time = time.time()
                start_io_counters = process.io_counters()

                result = func(*args, **kwargs)

                end_time = time.time()
                end_io_counters = process.io_counters()
                end_snapshot = tracemalloc.take_snapshot()
                current_memory_usage, peak_memory_usage = tracemalloc.get_traced_memory()
                current_memory_rss_mb = process.memory_info().rss / (1024 * 1024)
                memory_consumed_mb = sum(stat.size / (1024 * 1024) for stat in end_snapshot.compare_to(start_snapshot, 'lineno'))
                execution_time_sec = end_time - start_time
                disk_usage_mb = ((end_io_counters.read_bytes + end_io_counters.write_bytes) - \
                                (start_io_counters.read_bytes + start_io_counters.write_bytes)) / (1024 * 1024)

                if context.get('user_id', 0) and context.get('project_id', 0) and context.get('job_id', 0):
                    ElasticsearchLogger.log(
                        cell=context.get('cell', 'N/A'),
                        project_id=context['project_id'],
                        job_id=context['job_id'],
                        user_id=context['user_id'],
                        elastic_log_level=context.get('elastic_log_level', 'INFO'),
                        log_type=log_type,
                        log_severity="INFO",
                        service_name=service_name,
                        execution_time=format_time(execution_time_sec),
                        function_name=func.__name__,
                        memory_before_execution=f"{memory_before_execution:.3f} MB",
                        current_memory_usage=f"{current_memory_rss_mb:.3f} MB",
                        peak_memory_usage=f"{peak_memory_usage / (1024 * 1024):.3f} MB",
                        memory_consumed=f"{memory_consumed_mb:.3f} MB",
                        disk_usage=f"{disk_usage_mb:.3f} MB",
                        **log_kwargs
                    )
                else:
                    print("Skipping Elasticsearch log due to invalid context attributes.")
                return result
            except Exception as e:
                error_message = str(e)
                if context.get('user_id', 0) and context.get('project_id', 0) and context.get('job_id', 0):
                    ElasticsearchLogger.log(
                        cell=context.get('cell', 'N/A'),
                        project_id=context['project_id'],
                        job_id=context['job_id'],
                        user_id=context['user_id'],
                        elastic_log_level=context.get('elastic_log_level', 5),
                        log_type=log_type,
                        log_severity="ERROR",
                        service_name=service_name,
                        function_name=func.__name__,
                        error_message=error_message,
                        **log_kwargs
                    )
                raise
            finally:
                if tracemalloc_started:
                    tracemalloc.stop()
        return wrapper
    return decorator