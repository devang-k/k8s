import pya
def compare_gds(file1, file2):
        diff = pya.LayoutDiff()
        # Load the layouts
        layout1 = pya.Layout()
        layout1.read(file1)
        
        layout2 = pya.Layout()
        layout2.read(file2)
        
        # Check if the layouts are identical
        return diff.compare(layout1, layout2)