# GRPC client that calls the external GRPC server
import grpc
import grpc_service.grpc_service_pb2 as grpc_service_pb2
import grpc_service.grpc_service_pb2_grpc as grpc_service_pb2_grpc
import json
import traceback
from utils.config import third_party_grpc

def main(args):
    try:
        args = json.dumps(args)
    except:
        args['tech'] = str(args['tech'])
        args = json.dumps(args)
    try:
        with grpc.insecure_channel(third_party_grpc) as channel:
            stub = grpc_service_pb2_grpc.LVSServiceStub(channel)
            response = stub.LayoutGen(grpc_service_pb2.LayoutGenRequest(
                args=args
            ))
            return response.message
    except Exception as e:
        print(f"Error in gRPC call: {e}")
        print(traceback.format_exc())
        return {
            "status": '500',
            "message": f"Error in gRPC call: {e}"
        }