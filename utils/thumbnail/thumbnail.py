import pya
from os import listdir
from os.path import join, isfile

def gds_to_image_klayout(gds_files_path, layer_properties, width=512, height=512):
    app = pya.Application.instance()
    mw = app.main_window()
    files = [join(gds_files_path, name) for name in listdir(gds_files_path) if isfile(join(gds_files_path, name)) and name.endswith('.gds')]
    for file in files:
        mw.load_layout(file, 0)
        lv = mw.current_view()
        lv.load_layer_props(layer_properties)
        out = file.replace('gds','png')
        lv.save_image(out, width, height)

if __name__ == '__main__':
    global gds_folder, layer_properties
    gds_to_image_klayout(gds_folder, layer_properties)