import grpc_service.protobuf_stream_pb2 as protobuf_stream_pb2
import grpc_service.protobuf_stream_pb2_grpc as protobuf_stream_pb2_grpc
from grpc_service.sivista_runner import SiVistaRunner
from google.protobuf import struct_pb2
from lib_utils_version import get_lib_utils_version
from utils.config import project_root
import re
import os
import sys
import logging
from utils.logging_config import set_log_context
# main class for GRPC
class SiVistaLayoutServicer(protobuf_stream_pb2_grpc.SiVistaLayoutServicer):
    def LayoutGen(self, request, context):
        logger = logging.getLogger("sivista_app")
        yield protobuf_stream_pb2.SiVistaResponse(status='200', message='Starting the layout generation flow.')
        
        project_type = request.params.get("type", struct_pb2.Value(string_value='0')).string_value
        run_layout_only = request.params.get("run_layout_only", struct_pb2.Value(bool_value=True)).bool_value
        multi_height = request.params.get("multi_height", struct_pb2.Value(bool_value=False)).bool_value
        s3_prefix = request.s3_prefix + 'Stage1/' if run_layout_only else request.s3_prefix + 'Stage3/'
        permutations_folder_path = f'{request.job_id}/{request.cell}/{request.cell}_optimizedGDS' if run_layout_only else f'{request.job_id}/{request.cell}/{request.cell}_permutations'
        elastic_log_level = int(request.params.get("elastic_log_level", struct_pb2.Value(number_value=0)).number_value)
        log_level = int(request.params.get("log_level", struct_pb2.Value(number_value=0)).number_value)
        project_id = int(request.params.get("project_id", struct_pb2.Value(number_value=0)).number_value)
        user_id = int(request.params.get("user_id", struct_pb2.Value(number_value=0)).number_value)
        project_name = request.params.get("project_name", struct_pb2.Value(string_value='')).string_value
        set_log_context(
            cell=request.cell,
            elastic_log_level=elastic_log_level,
            log_level=log_level,
            job_id=request.job_id,
            project_id=project_id,
            user_id=user_id,
            project_name=project_name
            )


        runner = SiVistaRunner({
            'cell': request.cell,
            'netlist_data': request.netlist_data,
            'job_id': request.job_id,
            'type':project_type,
            'permutations_folder': permutations_folder_path,
            'tech_data': request.tech_json,
            'project_id': project_id,
            'user_id': user_id,
            'project_name': project_name,
        })
        
        if project_type == '1':
            runner.layouts_folder = permutations_folder_path
            runner.genetic_algo_flow_prep()
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            runner.run_genetic_algorithm()
            yield  protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            runner.make_gds_thumbnails(runner.layouts_folder)
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

        elif project_type == '2' or multi_height:
            runner.layout_flow_prep()
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            runner.run_large_transistor_poc()
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            runner.run_permutations(flow1=run_layout_only, double_height=True)
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            runner.run_metrics()
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            runner.run_pex()
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            # runner.run_extract_relative_resistance()
            # yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            runner.make_gds_thumbnails(runner.permutations_folder)
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

        else:
            runner.layout_flow_prep()
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            runner.run_layouts()
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            runner.run_permutations(flow1=run_layout_only)
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            runner.run_metrics()
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            runner.run_pex()
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            # runner.run_extract_relative_resistance()
            # yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

            runner.make_gds_thumbnails(runner.permutations_folder)
            yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

        runner.move_local_to_s3(s3_prefix)
        yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

        runner.save_log_file(request.s3_prefix)
        yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

    def Hyperexpressivity(self, request, context):
        yield protobuf_stream_pb2.SiVistaResponse(status='200', message='Starting the hyperexpressivity flow.')

        multi_height = request.params.get("multi_height", struct_pb2.Value(bool_value=False)).bool_value
        runner = SiVistaRunner({
            'cell': request.cell,
            'gds_folder_path': request.job_id + '/' + request.gds_folder_path,
            'job_id': request.job_id,
            'netlist_data': request.netlist_data,
            'tech_data': request.tech_json,
            'shared_memory': ''
        })
        
        runner.hyperexpressivity_flow_prep(f'{request.s3_prefix}Stage1/{request.gds_folder_path}/')
        yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

        runner.run_permutations(double_height=multi_height)
        yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

        runner.make_gds_thumbnails(runner.permutations_folder)
        yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

        runner.run_metrics()
        yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

        runner.run_pex()
        yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

        # runner.run_extract_relative_resistance()
        # yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

        runner.move_local_to_s3(f'{request.s3_prefix}Stage2/')
        yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)

        runner.save_log_file(request.s3_prefix)
        yield protobuf_stream_pb2.SiVistaResponse(status=runner.status, message=runner.message)
    
    def GetVersion(self, request, context):

        # Get the absolute path to a required file.
        try:
            # When running as a bundled app
            base_path = sys._MEIPASS
        except AttributeError:
            # When running as a script
            base_path = os.getcwd()
        
        file_path = os.path.join(base_path, 'version.conf')
        with open(file_path, 'r') as file:
            content = file.read()
        match = re.search(r'VERSION="([\d\.]+)"', content)
        if match:
            sivista_version = match.group(1)
            lib_utils_version = get_lib_utils_version()
            version = f'("{sivista_version}", "{lib_utils_version}")'
        else:
            version = '("0.0.0.0", "0.0.0.0")'
        return protobuf_stream_pb2.SiVistaResponse(status='200', message=version)

    def GetFile(self, request, context):
        request.file_path = f'{project_root}/{request.file_path}'
        print(f"Received request for file: {request.file_path}")
        if not os.path.isfile(request.file_path):
            return protobuf_stream_pb2.SiVistaResponse(status='404', message=f"File not found at {request.file_path}")
        try:
            with open(request.file_path, "rb") as f:
                content = f.read()
            return protobuf_stream_pb2.SiVistaResponse(status='200', message=content)
        except Exception as e:
            return protobuf_stream_pb2.SiVistaResponse(status='500', message=f"Error reading file: {str(e)}")
