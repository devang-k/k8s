import grpc
import grpc_service.grpc_service_pb2 as grpc_lvs_pb2
import grpc_service.grpc_service_pb2_grpc as grpc_lvs_pb2_grpc
from json import dumps, dump
from datetime import datetime
from utils.config import third_party_grpc
from utils.writer.gds_writer import GDSWriter
import logging
logger = logging.getLogger('sivista_app')

class LVSClientHandler:

    def __init__(self, layer_properties, file_name, batch_size, netlist_path, cell_name, tech, output_folder, suffix=True, limiter=None):
        self.layer_properties = layer_properties
        self.gds_jsons = {}
        self.lvs_clean_count = 0
        self.file_name = file_name.replace('.gds','')
        self.summary_report = []
        self.batch_size = batch_size
        self.netlist_path = netlist_path
        self.cell_name = cell_name
        self.tech = tech
        self.output_folder = output_folder
        self.suffix = suffix
        self.writer = GDSWriter()
        self.limiter = limiter

    def add_gds_json(self, key, gds_json):
        self.gds_jsons[key] = gds_json
        if len(self.gds_jsons) == self.batch_size:
            self.run()
            self.gds_jsons = {}

    def run(self):
        with open(self.netlist_path, 'r') as file:
            netlist_contents = file.read()
        #LVS checks
        lvs_results = {}
    
        with grpc.insecure_channel(third_party_grpc) as channel:
            stub = grpc_lvs_pb2_grpc.LVSServiceStub(channel)
            request = grpc_lvs_pb2.BulkLVSRequest(
                cell_name=self.cell_name,
                netlist_path=netlist_contents,
                scaling_factor=self.tech.scaling_factor,
                width=self.layer_properties.nanosheetWidth,
                length=max(self.layer_properties.wireWidth["npoly"], self.layer_properties.wireWidth["ppoly"]),
                technology=self.tech.technology,
                layer_stack=dumps(self.tech.layer_map),
                gdsjsons=dumps(self.gds_jsons),
                height_req=self.tech.height_req
            )
            lvs_response = stub.BulkLVS(request)
            lvs_results = lvs_response.result
        lvs_results = sorted(lvs_results.items(), key=lambda x: int(x[0]))
        
        # Write only the LVS clean layouts to GDS files
        for file_code, result in lvs_results:
            if self.limiter and self.lvs_clean_count >= self.limiter:
                return
            layout_data = {
                'runDate': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'drc': True,
                'lvs': result,
                'layoutName': self.file_name
            }
            if result == 'True':
                self.lvs_clean_count += 1
                layout_data['permutationLayout'] = f'{self.file_name}_{self.lvs_clean_count}'
                if self.suffix:
                    file_name = f"{self.output_folder}/{self.file_name}_{self.lvs_clean_count}"
                else:
                    file_name = f"{self.output_folder}/{self.file_name}"
                self.writer.write(self.gds_jsons[file_code], f"{file_name}.gds")
                print(f"\r Generating second degree permutations for {self.lvs_clean_count}",end = '')
                logger.info(f"LVS clean layout generated: {file_name}.gds")
            self.summary_report.append(layout_data)