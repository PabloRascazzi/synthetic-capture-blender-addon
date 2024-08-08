import os
import bpy
import math
import mathutils
from bpy.props import CollectionProperty
from bpy_extras.io_utils import ExportHelper

bl_info = {
    "name": "Synthetic Capture",
    "author": "Pablo Rascazzi",
    "version": (1, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Misc > Synthetic Capture",
    "description": "Example with multiple operators",
    "category": "Render Automation"}


def create_capture_cameras(self, context):
    if context.scene.syncap.collection == None:
        print("Synthetic Capture: Create collection.")
        collection = bpy.data.collections.new("Synthetic Capture")
        context.scene.syncap.collection = collection
        context.scene.collection.children.link(collection)
        
        print("Synthetic Capture: Create cameras.")
        
        radius = context.scene.syncap.camera_distance
        longitude_quantity = context.scene.syncap.camera_longitude_quantity
        latitude_quantity = context.scene.syncap.camera_latitude_quantity
        
        for vi in range(0, longitude_quantity):
            phi = 2.0 * math.pi * (vi / longitude_quantity)
            for hi in range(0, latitude_quantity):
                theta = math.pi * ((hi+1) / (latitude_quantity+1))
                
                # Create camera.
                cam_id = (vi * latitude_quantity) + hi
                cam_name = "Camera #" + str(cam_id)
                cam = bpy.data.cameras.new(cam_name)
                cam.lens = 50
                cam.clip_end = 100.0
                
                # Calculate camera object position.
                x = radius * math.sin(theta) * math.cos(phi)
                y = radius * math.sin(theta) * math.sin(phi)
                z = radius * math.cos(theta)
                position = mathutils.Vector((x, y, z))
                
                # Calculate camera object orientation.
                direction = mathutils.Vector((0,0,0)) - position
                orientation = direction.to_track_quat('-Z', 'Y')

                # Create camera object.
                cam_obj = bpy.data.objects.new(cam_name, cam)
                cam_obj.location = position
                cam_obj.rotation_euler = orientation.to_euler()
                collection.objects.link(cam_obj)
    else:
        self.report({'WARNING'}, "Warning: cannot create new cameras because cameras already exists.")
    
    return None


def destroy_capture_cameras(self, context):
    if context.scene.syncap.collection != None:
        print("Synthetic Capture: Destroy cameras.")
        
        # Remove all cameras in the collection.
        for obj in context.scene.syncap.collection.objects:
            if obj.type == 'CAMERA':
                bpy.data.cameras.remove(obj.data)
        # Remove collection once empty.
        collection = context.scene.syncap.collection
        bpy.data.collections.remove(collection)
    else:
        self.report({'WARNING'}, "Warning: cannot destroy cameras because none exists.")
    
    return None


def update_synthetic_capture_cameras(self, context):
    bpy.ops.syncap.destroy_cameras()
    if context.scene.syncap.camera_show_hide == True:
        bpy.ops.syncap.create_cameras()
            
    return None


def render_capture_cameras(self, context):
    # Check if camera collection has been initialized, throw warning if not.
    if context.scene.syncap.collection != None:
        print("Synthetic Capture: Capture.")
        
        collection = context.scene.syncap.collection
        for cam in [obj for obj in collection.objects if obj.type == "CAMERA"]:
            context.scene.camera = cam
            file = os.path.join(context.scene.syncap.save_path, cam.name)
            context.scene.render.filepath = file
            bpy.ops.render.render(write_still=True)
        
        # TODO - save the camera information (position, orientation, etc) as metadata (optional).
        self.report({'INFO'}, 'Saved captured data "' + context.scene.syncap.save_path + '"')
        
    else:
        self.report({'WARNING'}, "Warning: cannot destroy cameras because none exists.")
    
    return None


class SyntheticCaptureProperties(bpy.types.PropertyGroup):
    camera_show_hide: bpy.props.BoolProperty(
        name="Show/Hide",
        description="Toggle to show or hide the synthetic capture cameras. Useful for visualizing the camera placements",
        default=True,
        update=update_synthetic_capture_cameras
    )
    
    camera_distance: bpy.props.FloatProperty(
        name="Distance",
        description="Radial distance between the cameras and the object to be captured",
        default=10, min=0.01,
        update=update_synthetic_capture_cameras
    )
    
    camera_longitude_quantity: bpy.props.IntProperty(
        name="Longitude Quantity",
        description="Amount of camera layers on the longitude",
        default=12, min=1,
        update=update_synthetic_capture_cameras
    )
    
    camera_latitude_quantity: bpy.props.IntProperty(
        name="Latitude Quantity",
        description="Amount of camera layers on the latitude",
        default=3, min=1,
        update=update_synthetic_capture_cameras
    )
    
    save_path: bpy.props.StringProperty(
        name="Save Path",
        description="Path to the save directory",
        default="",
        subtype='DIR_PATH',
        maxlen=1024
    )
    
    collection: bpy.props.PointerProperty(
        type=bpy.types.Collection, 
        name="Collection"
    )
    
    
class SYNCAP_OT_create_cameras_operation(bpy.types.Operator):
    bl_idname = "syncap.create_cameras"
    bl_label = "Create Cameras"
    bl_description = "" # TODO
    
    def execute(self, context):
        create_capture_cameras(self, context)
        return{'FINISHED'}
    
    
class SYNCAP_OT_destroy_cameras_operation(bpy.types.Operator):
    bl_idname = "syncap.destroy_cameras"
    bl_label = "Destroy Cameras"
    bl_description = "" # TODO
    
    def execute(self, context):
        destroy_capture_cameras(self, context)
        return{'FINISHED'}
    
    
class SYNCAP_OT_save_path_selector(bpy.types.Operator, ExportHelper):
    bl_idname = "syncap.save_path_selector"
    bl_label = "Path"
    bl_description = "Path to the save directory for the rendered results and metadata"

    filename_ext = ""

    def execute(self, context):
        context.scene.syncap.save_path = self.properties.filepath
        return{'FINISHED'}
    

class SYNCAP_OT_capture_operation(bpy.types.Operator):
    bl_idname = "syncap.capture"
    bl_label = "Capture"
    bl_description = "Automatically renders object using cameras spaced at specified intervals"
    
    def execute(self, context):
        render_capture_cameras(self, context)
        return{'FINISHED'}
   

class SYNCAP_PT_panel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Synthetic Capture"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    # bl_context = "scene" TODO

    def draw(self, context):
        layout = self.layout

        camera_box = self.layout.box()
        camera_box.use_property_split = True
        camera_box.use_property_decorate = False
        camera_box.label(text="Camera Options",icon='OUTLINER_DATA_CAMERA')
        camera_box.prop(context.scene.syncap, 'camera_show_hide', text='Show / Hide')
        camera_box.prop(context.scene.syncap, 'camera_distance', text='Distance:')
        camera_box_col = camera_box.column(align=True)
        camera_box_col.prop(context.scene.syncap, 'camera_longitude_quantity', text='Longitude:')
        camera_box_col.prop(context.scene.syncap, 'camera_latitude_quantity', text='Latitude:')

        output_box = self.layout.box()
        output_box.label(text="Output Options",icon='OUTPUT')
        output_box.prop(context.scene.syncap, 'save_path', text='Directory')
        
        layout.operator("syncap.capture")


def register():
    bpy.utils.register_class(SyntheticCaptureProperties)
    bpy.utils.register_class(SYNCAP_OT_create_cameras_operation)
    bpy.utils.register_class(SYNCAP_OT_destroy_cameras_operation)
    bpy.utils.register_class(SYNCAP_OT_capture_operation)
    bpy.utils.register_class(SYNCAP_OT_save_path_selector)
    bpy.utils.register_class(SYNCAP_PT_panel)
    bpy.types.Scene.syncap = bpy.props.PointerProperty(type=SyntheticCaptureProperties)


def unregister():
    bpy.utils.unregister_module(SyntheticCaptureProperties)
    bpy.utils.unregister_class(SYNCAP_OT_create_cameras_operation)
    bpy.utils.unregister_class(SYNCAP_OT_destroy_cameras_operation)
    bpy.utils.unregister_class(SYNCAP_OT_capture_operation)
    bpy.utils.unregister_class(SYNCAP_OT_save_path_selector)
    bpy.utils.unregister_class(SYNCAP_PT_panel)
    del bpy.types.Scene.syncap


if __name__ == "__main__":
    register()