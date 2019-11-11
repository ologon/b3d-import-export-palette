bl_info = {
    "name": "Brush Palette",
    "author": "Spadafina Alfredo",
    # Final version number must be two numerals to support x.x.00
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "description": "Import/Export Brush Palette (.gpl)",
    "location": "Paint Tool Options > Brush > Color Palette",
    "category": "Import-Export"
}

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from os import path


class VIEW3D_OP_ImportPalette(bpy.types.Operator, ImportHelper):
    """Import color palette"""      
    bl_idname = "iepalette.import"        
    bl_label = "Import"         
    bl_options = {'REGISTER', 'UNDO'}  
    
    filter_glob: bpy.props.StringProperty(
        default="*.gpl",
        options={'HIDDEN'},
    )
    
    def execute(self, context):        
        filename = path.splitext(path.basename(self.filepath))[0]
        
        try:
            file = open(self.filepath, "r")
        except:
            self.report({'ERROR'}, "Could not read file")
            return {'CANCELLED'}
        
        lines = file.readlines()
        if lines[0].replace('\n','') != "GIMP Palette":
            self.report({'ERROR'}, "Not a GIMP Palette file")
            return {'CANCELLED'}
            
        palette = bpy.data.palettes.new(filename)
        del lines[0]
        for line in lines:
            if not line.startswith("#"):
                line = line.replace('\t', ' ')
                colors = line.split()
                if len(colors) > 3:
                    newcol = palette.colors.new()
                    newcol.color = (int(colors[0])/255.0, int(colors[1])/255.0, int(colors[2])/255.0)
                
        file.close()
        self.report({'INFO'}, "Imported Palette %s" % (palette.name_full))

        return {'FINISHED'}   
    
    
class VIEW3D_OP_ExportPalette(bpy.types.Operator, ExportHelper):
    """Export color palette"""      
    bl_idname = "iepalette.export"        
    bl_label = "Export"         
    bl_options = {'REGISTER', 'UNDO'} 
    
    filename_ext = ".gpl" 
    filter_glob: bpy.props.StringProperty(
        default="*.gpl",
        options={'HIDDEN'},
    )

    def execute(self, context):       
        palette = context.tool_settings.image_paint.palette
        
        try:
            file = open(self.filepath, "w")
        except:
            self.report({'ERROR'}, "Could not write file")
            return {'CANCELLED'}
        
        file.write("GIMP Palette\n")
        file.write("#Palette Name: %s\n" % (palette.name_full))
        file.write("#Description: Exported from Blender\n")
        file.write("#Colors: %s\n" % (len(palette.colors)))
        
        for item in palette.colors:
            r = int(item.color[0]*255.0)
            g = int(item.color[1]*255.0)
            b = int(item.color[2]*255.0)
            hex = "%0.2X"*3 % (r, g, b)
            file.write("%s\t%s\t%s\t#%s\n" % (r, g, b, hex.lower()))
            
        file.close()
        self.report({'INFO'}, "Exported Palette %s" % (path.basename(self.filepath)))

        return {'FINISHED'}    
    

classes = (
    VIEW3D_OP_ImportPalette,
    VIEW3D_OP_ExportPalette,
)


def draw_properties(self, context):
    layout = self.layout
    
    row = layout.row()
    row.operator("iepalette.import")
    row.operator("iepalette.export")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.VIEW3D_PT_tools_brush_swatches.prepend(draw_properties)
        

def unregister():
    bpy.types.VIEW3D_PT_tools_brush_swatches.remove(draw_properties)
    
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()