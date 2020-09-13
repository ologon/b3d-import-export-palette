bl_info = {
    "name": "Brush Palette",
    "author": "Spadafina Alfredo",
    # Final version number must be two numerals to support x.x.00
    "version": (1, 1, 0),
    "blender": (2, 80, 0),
    "description": "Import/Export Brush Palette (.gpl)",
    "location": "Paint Tool Options > Brush > Color Palette",
    "category": "Import-Export"
}

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from os import path
import urllib.request
import json

class VIEW3D_MT_LoadPaletteMenu(bpy.types.Menu):
    """Optional tools for load palette"""
    bl_idname = 'VIEW3D_MT_LoadPaletteMenu'
    bl_label = "Palette Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("iepalette.lospec", icon="OUTLINER_OB_LIGHTPROBE")
        layout.operator("iepalette.lospecrandom", icon="GPBRUSH_RANDOMIZE")

class VIEW3D_OP_LospecRandomPalette(bpy.types.Operator):
    """Load a random palette from Lospec"""
    bl_idname = "iepalette.lospecrandom"
    bl_label = "Random Lospec Palette"

    def execute(self, context):
        try:
            rand_url = urllib.request.urlopen("https://lospec.com/palette-list/random")
            bpy.ops.iepalette.lospec(palette_uri=rand_url.geturl())
        except urllib.error.URLError as e:
            self.report({'ERROR'}, e.reason)
        return {'FINISHED'}

class VIEW3D_OP_LoadLospecPalette(bpy.types.Operator):
    """Import palette from Lospec"""
    bl_idname = "iepalette.lospec"
    bl_label = "Load Lospec Palette"

    palette_uri: bpy.props.StringProperty(
        name="Palette URL",
        description="Palette URL from the lospec site",
        default=""
    )

    def execute(self, context):
        target_uri = self.palette_uri
        if not target_uri.startswith("https://lospec.com/palette-list/"):
            self.report({'ERROR'}, "URL doesn't look like a lospec palette")
        else:
            target_uri += ".json"
            pal_raw = None
            try:
                response = urllib.request.urlopen(target_uri)
                pal_raw = response.read().decode("utf-8")
                # The lospec json API doesn't return 404 for palettes that cannot be found. 
                # The workaround is to detect when we received a HTML document instead of a JSON response
                if pal_raw.startswith("<!DOCTYPE html>"):
                    pal_raw = None
            except urllib.error.URLError as e:
                self.report({'ERROR'}, e.reason)
            
            if pal_raw is None:
                self.report({'ERROR'}, "Lospec palette could not be found")
            else:
                pal_json = json.loads(pal_raw)
                
                new_pal = None
                bl_palettes = bpy.data.palettes
                
                pal_name = pal_json["name"]
                pal_idx = bl_palettes.find(pal_name)
                if pal_idx is not -1:
                    new_pal = bl_palettes[pal_idx]
                else:
                    new_pal = bl_palettes.new(pal_name)
                
                new_pal.colors.clear()

                pal_colors = pal_json["colors"]
                for color_data in pal_colors:
                    color_val = None
                    try:
                        color_val =(
                            int(color_data[0:2], 16) / 255.0,
                            int(color_data[2:4], 16) / 255.0,
                            int(color_data[4:6], 16) / 255.0
                        )
                    except e:
                        self.reprt({'ERROR'}, "Error parsing color {}, {}".format(color_data, e))
                    
                    if color_val is not None:
                        bl_color = new_pal.colors.new()
                        bl_color.color = color_val
                
                VIEW3D_OP_ImportPalette.set_palette(context, new_pal)
                self.report({'INFO'}, "Lospec palette: {}, {} colors".format(pal_name, len(pal_colors)))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        row = col.row()
        row.operator("wm.url_open", text="Palette List").url = "https://lospec.com/palette-list"
        row.operator("wm.url_open", text="Random").url = "https://lospec.com/palette-list/random"
        col.label(text="Paste the URL of a Lospec palette")
        col.prop(self, "palette_uri")


class VIEW3D_OP_ImportPalette(bpy.types.Operator, ImportHelper):
    """Import color palette"""      
    bl_idname = "iepalette.import"        
    bl_label = "Import"         
    bl_options = {'REGISTER', 'UNDO'}  
    
    filter_glob: bpy.props.StringProperty(
        default="*.gpl",
        options={'HIDDEN'},
    )

    @staticmethod
    def set_palette(context, palette):
        context.tool_settings.image_paint.palette = palette
        context.tool_settings.gpencil_paint.palette = palette
    
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

        VIEW3D_OP_ImportPalette.set_palette(context, palette)

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
        if context.active_object.mode == 'PAINT_GPENCIL':
            palette = context.tool_settings.gpencil_paint.palette
        
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
    VIEW3D_OP_LoadLospecPalette,
    VIEW3D_OP_LospecRandomPalette,
    VIEW3D_MT_LoadPaletteMenu
)


def draw_properties(self, context):
    layout = self.layout
    
    row = layout.row()
    row.operator("iepalette.import", icon='IMPORT')
    row.operator("iepalette.export", icon='EXPORT')
    row.menu('VIEW3D_MT_LoadPaletteMenu', icon='DOWNARROW_HLT', text='')


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.VIEW3D_PT_tools_brush_swatches.prepend(draw_properties)
    bpy.types.VIEW3D_PT_tools_grease_pencil_brush_mix_palette.prepend(draw_properties)
        

def unregister():
    bpy.types.VIEW3D_PT_tools_brush_swatches.remove(draw_properties)
    bpy.types.VIEW3D_PT_tools_grease_pencil_brush_mix_palette.remove(draw_properties)
    
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()