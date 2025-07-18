import grpc
import grpc_service.grpc_service_pb2 as grpc_service_pb2
import grpc_service.grpc_service_pb2_grpc as grpc_service_pb2_grpc
import traceback
from utils.config import third_party_grpc

def get_lib_utils_version():
    try:
        with grpc.insecure_channel(third_party_grpc) as channel:
            stub = grpc_service_pb2_grpc.LVSServiceStub(channel)
            version = stub.Version(grpc_service_pb2.Empty())
            return version.message
    except Exception as e:
        print(traceback.format_exc())
        return "Error in lib_utils connection"