from dotenv import load_dotenv, find_dotenv
import os
import sys
from cryptography.fernet import Fernet
import grpc
import grpc_service.protobuf_stream_pb2 as grpc_pb2
import grpc_service.protobuf_stream_pb2_grpc as grpc_pb2_grpc
import sys
from dotenv import load_dotenv, find_dotenv

klayout_configs = {
    'layerproperties': 'tech/monCFET/mcfet.lyp',
    'path': 'klayout'
}

env = os.getenv('ML_ENV', '.env.dev')
env_file = find_dotenv(env)
load_dotenv(env_file)
storage_type = os.getenv('STORAGE_TYPE')
third_party_grpc = os.getenv('THIRD_PARTY_GRPC')
shared_memory = os.getenv('SHARED_MEMORY')
from pathlib import Path
current_file = Path(__file__).resolve()
project_root = current_file.parents[1]
if env=='.env.dev':
    configs = {
        'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID_DEV'),
        'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY_DEV'),
        'AWS_STORAGE_BUCKET_NAME': os.getenv('AWS_STORAGE_BUCKET_NAME_DEV'),
        'AWS_S3_REGION_NAME': os.getenv('AWS_S3_REGION_NAME_DEV'),
        'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS_DEV'),
        'GOOGLE_STORAGE_BUCKET_NAME': os.getenv('GOOGLE_STORAGE_BUCKET_NAME_DEV'),
        'ELASTICSEARCH_URL': os.getenv('ELASTICSEARCH_URL'),
        'ELASTICSEARCH_USERNAME': os.getenv('ELASTICSEARCH_USERNAME'),
        'ELASTICSEARCH_PASSWORD': os.getenv('ELASTICSEARCH_PASSWORD'),
    }
    
elif env=='.env.qa':
    configs = {
        'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID_QA'),
        'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY_QA'),
        'AWS_STORAGE_BUCKET_NAME': os.getenv('AWS_STORAGE_BUCKET_NAME_QA'),
        'AWS_S3_REGION_NAME': os.getenv('AWS_S3_REGION_NAME_QA'),
        'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS_QA'),
        'GOOGLE_STORAGE_BUCKET_NAME': os.getenv('GOOGLE_STORAGE_BUCKET_NAME_QA'),
        'ELASTICSEARCH_URL': os.getenv('ELASTICSEARCH_URL'),
        'ELASTICSEARCH_USERNAME': os.getenv('ELASTICSEARCH_USERNAME'),
        'ELASTICSEARCH_PASSWORD': os.getenv('ELASTICSEARCH_PASSWORD'),
    }

local_file_configs = {
    'base_path': os.getenv('LOCAL_BASE_PATH')
}

base_path=""
# Get the absolute path to a required file.
try:
    # When running as a bundled app
    base_path = sys._MEIPASS
    model_paths = {
        "moe": {
            "cfet": {
                "encoder_path": os.path.join(base_path, "pex_extraction/data/encoder-06-2024-wgts.pth"),
                "predictor_path": os.path.join(base_path, "pex_extraction/data/moe-06-2024-wgts.keras"),
                "scaler_path": os.path.join(base_path, "pex_extraction/data/scaler-06-2024.pkl"),
            },
            "gaa": {
                "encoder_path": os.path.join(base_path, "pex_extraction/data/encoder-gaa-wgts.pth"),
                "predictor_path": os.path.join(base_path, "pex_extraction/data/moe-gaa-wgts.keras"),
                "scaler_path": os.path.join(base_path, "pex_extraction/data/scaler-06-2024.pkl"),
            },
        },
        "gnn": {
            "cfet": {
                "encoder_path": os.path.join(base_path, "pex_extraction/data/autoencoder-cfet-wgts.pth"),
                "predictor_path": os.path.join(base_path, "pex_extraction/data/gnn-cfet-wgts.pth"),
                "scaler_path": os.path.join(base_path, "pex_extraction/data/scaler-06-2024.pkl"),
                "model_init_params": os.path.join(base_path, "pex_extraction/data/gnn-cfet-tuned-params.pkl"),
                "resistance_predictor_path": os.path.join(base_path, "pex_extraction/data/attn-rgcn-dual-tech-05-01-2025.pt"),
                "resistance_norm_params": os.path.join(base_path, "pex_extraction/data/attn-rgcn-dual-tech-05-01-2025-normalization-params.pt"),
            },
            "gaa": {
                "encoder_path": os.path.join(base_path, "pex_extraction/data/inc_autoencoder_wgts_gaa_fsp_single_multi_var_26jun25-v10.pth"),
                "predictor_path": os.path.join(base_path, "pex_extraction/data/gnn-wgts-gaa-fsp-single-multi-var-26jun25-v10.pth"),
                "scaler_path": os.path.join(base_path, "pex_extraction/data/scaler-06-2024.pkl"),
                "model_init_params": os.path.join(base_path, "pex_extraction/data/gnn-tuned-params-gaa-fsp-single-multi-var-26jun25-v10.pkl"),
                "resistance_predictor_path": os.path.join(base_path, "pex_extraction/data/attn-rgcn-dual-tech-05-01-2025.pt"),
                "resistance_norm_params": os.path.join(base_path, "pex_extraction/data/attn-rgcn-dual-tech-05-01-2025-normalization-params.pt"),
 
            },
        },
    }
except AttributeError:
    # When running as a script
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_paths = {
        "moe": {
            "cfet": {
                "encoder_path": os.path.join(base_path, "pex_extraction/data/cfet/encoder-06-2024-wgts.pth"),
                "predictor_path": os.path.join(base_path, "pex_extraction/data/cfet/moe-06-2024-wgts.keras"),
                "scaler_path": os.path.join(base_path, "pex_extraction/data/cfet/scaler-06-2024.pkl"),
            }
        },
        "gnn": {
            "cfet": {
                "encoder_path": os.path.join(base_path, "pex_extraction/data/cfet/autoencoder-cfet-wgts.pth"),
                "predictor_path": os.path.join(base_path, "pex_extraction/data/cfet/gnn-cfet-wgts.pth"),
                "scaler_path": os.path.join(base_path, "pex_extraction/data/cfet/scaler-06-2024.pkl"),
                "model_init_params": os.path.join(base_path, "pex_extraction/data/cfet/gnn-cfet-tuned-params.pkl"),
                "resistance_predictor_path": os.path.join(base_path, "pex_extraction/data/cfet_resistance/attn-rgcn-dual-tech-05-01-2025.pt"),
                "resistance_norm_params": os.path.join(base_path, "pex_extraction/data/cfet_resistance/attn-rgcn-dual-tech-05-01-2025-normalization-params.pt"),
            },
            "gaa": {
                "encoder_path": os.path.join(base_path, "pex_extraction/data/gaa/inc_autoencoder_wgts_gaa_fsp_single_multi_var_26jun25-v10.pth"),
                "predictor_path": os.path.join(base_path, "pex_extraction/data/gaa/gnn-wgts-gaa-fsp-single-multi-var-26jun25-v10.pth"),
                "scaler_path": os.path.join(base_path, "pex_extraction/data/gaa/scaler-06-2024.pkl"),
                "model_init_params": os.path.join(base_path, "pex_extraction/data/gaa/gnn-tuned-params-gaa-fsp-single-multi-var-26jun25-v10.pkl"),
                "resistance_predictor_path": os.path.join(base_path, "pex_extraction/data/gaa_resistance/attn-rgcn-dual-tech-05-01-2025.pt"),
                "resistance_norm_params": os.path.join(base_path, "pex_extraction/data/gaa_resistance/attn-rgcn-dual-tech-05-01-2025-normalization-params.pt"),
            },
        },
    }



env = os.getenv('LIB_ENV', '.env.dev')
env_file = find_dotenv(env)
load_dotenv(env_file)
SHARED_MEMORY = os.getenv('SHARED_MEMORY')
FTEP = os.getenv('FTEP')
EXTNSION_TYPE = os.getenv('EXTNSION_TYPE')

# Get the absolute path to a required file.
try:
    # When running as a bundled app
    base_path = sys._MEIPASS
    path_to_key = os.path.join(base_path,'secret.key')
except AttributeError:
    # When running as a script
    path_to_key = 'secret.key'


class FileReader:
    def __init__(self, path_to_key: str = ''):
        self.path_to_key = path_to_key
        # Load the Fernet key
        with open(self.path_to_key, 'rb') as key_file:
            key = key_file.read()
        self.fernet = Fernet(key)

class SubModuleReader(FileReader):
    def __init__(self, path_to_key, root_path: str = ''):
        super().__init__(path_to_key)
        current_dir = os.path.dirname(__file__)
        parent_dir = os.path.dirname(current_dir)
        self.root_path = parent_dir + '/stdcell_generation_shared/'

    def read_file(self, file_path: str) -> str:
        file_path = self.root_path + file_path
        with open(file_path, "r") as file:
            content = file.read()
        return content


def run_encrypted_python(enc_file_path: str, key_file_path: str =  path_to_key):
    """Decrypt and execute an encrypted Python file at runtime."""
    if not os.path.isfile(key_file_path):
        raise FileNotFoundError(f"Key file not found: {key_file_path}")
    # if not os.path.isfile(enc_file_path):
    #     raise FileNotFoundError(f"Encrypted file not found: {enc_file_path}")
    file_reader = SubModuleReader(key_file_path)
    encrypted_data = file_reader.read_file(enc_file_path)
    return encrypted_data