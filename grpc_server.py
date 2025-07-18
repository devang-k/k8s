import sys
 
try:
    # When running as a bundled app
    base_path = sys._MEIPASS
 
    # following paths are required to find klayout pylibs and base dependencies inside docker conatiner when code is packaged as an executable
    sys.path.insert(0,"/usr/lib/python3.10/")
    sys.path.insert(0,"/usr/local/lib/python3.10/dist-packages")
except AttributeError:
    # When running as a script
    pass
 
 
import grpc
import grpc_service.protobuf_stream_pb2_grpc as protobuf_stream_pb2_grpc
 
from grpc_service.servicer import SiVistaLayoutServicer
from concurrent import futures
from utils.logging_config import setup_es_logging
def serve():
    logger = setup_es_logging()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    protobuf_stream_pb2_grpc.add_SiVistaLayoutServicer_to_server(SiVistaLayoutServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info('Sivista App Logger Initialized')
    print("Server started, listening on port 50051")
    server.wait_for_termination()
 
if __name__ == '__main__':
    serve()
 