import argparse
import grpc
import grpc_service.protobuf_stream_pb2 as protobuf_stream_pb2
import grpc_service.protobuf_stream_pb2_grpc as protobuf_stream_pb2_grpc
import json
from google.protobuf import struct_pb2
import traceback

from utils.logging_config import setup_es_logging

def parse_args():
    parser = argparse.ArgumentParser(
            description="SiClarity SiVista SmartCell-Generation: Monolithic CFET"
        )
    parser.add_argument(
            "-job", "--job-id", dest="job_id", default="100"
        )
    return parser.parse_args()

def read_json_as_string(file_path):
    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            json_string = json.dumps(json_data)
            # print(json_string)
            return json_string
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return None

def read_netlist(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return None

def run(cell_name='INVD4'):
    args = parse_args()
    job_id = args.job_id
    json_string = read_json_as_string('tech/monCFET/techData.json')
    netlist_data = read_netlist('tech/monCFET/monCFET.spice')
    with grpc.insecure_channel('localhost:50051') as channel:
        stub =  protobuf_stream_pb2_grpc.SiVistaLayoutStub(channel)

        response = stub.GetVersion(protobuf_stream_pb2.Empty())
        print(f'Version: {response.message}')

        responses = stub.LayoutGen(protobuf_stream_pb2.LayoutGenRequest(
            netlist_data=netlist_data,
            job_id=job_id,
            cell=cell_name,
            s3_prefix='SiVistaDevRoot/Project/5/1/',
            tech_json=json_string,
            params={
                'run_layout_only': struct_pb2.Value(bool_value=True),
                'type': struct_pb2.Value(string_value='0'),
                'multi_height': struct_pb2.Value(bool_value=False),
                'elastic_log_level': struct_pb2.Value(number_value=1),
                'log_level': struct_pb2.Value(number_value=5),
                'project_id': struct_pb2.Value(number_value=10),
                'user_id': struct_pb2.Value(number_value=1),
                'project_name': struct_pb2.Value(string_value="test09")
            }
        ))
        
        for response in responses:
            print(response)

        responses = stub.Hyperexpressivity(protobuf_stream_pb2.HyperexpressivityRequest(
            gds_folder_path=f'{cell_name}/{cell_name}_layouts',
            job_id=job_id,
            cell=cell_name, 
            s3_prefix='SiVistaDevRoot/Project/5/1/',
            tech_json=json_string,
            netlist_data=netlist_data,
            params={
                'multi_height': struct_pb2.Value(bool_value=False)
            }
        ))
        for response in responses:
            print(response)

if __name__ == '__main__':
    from utils.logging_config import setup_es_logging
    setup_es_logging()
    
    cells = ['INVD4']
    for cell in cells:
        run(cell)
        print('---' * 20)
