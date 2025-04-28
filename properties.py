from bpy.types import PropertyGroup, Operator, UILayout
from xml.etree.ElementTree import Element
from bpy.props import *
import sys, inspect
from .enums import *
from .xml_util import *
from typing import get_type_hints

bake_maps = {}

def get_bake_maps(self, context):
    global bake_maps
    if bake_maps == {} :
        bake_maps = [(rendermap.__name__, rendermap.__name__, '') for rendermap in maps()]
    return bake_maps

class XNORMAL_OT_CallMenuRenderMap(Operator):
    bl_idname = "xnormal.call_menu"
    bl_label = ""
    bl_description = ""
    bl_options = {"INTERNAL"}
    map: EnumProperty(items=get_bake_maps)
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        dpi_value = context.preferences.system.dpi
        return context.window_manager.invoke_props_dialog(self, width=dpi_value*6)

    def draw(self, context):
        scene = context.scene
        confs = scene.xnormal_settings
        conf = confs.settings[confs.active_index]
        classes = [cls for cls in maps() if cls.__name__ == self.map]
        if len(classes) == 1 :
            classes[0].draw(getattr(conf.maps, self.map), self.layout)



def maps():
    classes = []
    for name, member in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(member) and issubclass(member, RenderMap) and member != RenderMap :
            member.__annotations__[member.id] = BoolProperty(default = False, name = member.__name__)
            classes.append(member)
    return classes

class RenderMap(PropertyGroup):
    id = ''

    def draw(self, context):
        pass

    @classmethod
    def write(cls, pgroup, xml:Element):
        generate = xml.find("GenerateMaps")
        conf = getattr(pgroup.maps, cls.__name__)
        set_xml(generate, cls.id, getattr(conf, cls.id))
        props = get_type_hints(cls)
        for prop_name, prop_def in props.items() :
            if 'subtype' in prop_def.keywords and prop_def.keywords['subtype'] == 'COLOR' :
                set_xml_color(generate, prop_name, getattr(conf, prop_name))
            else :
                set_xml(generate, prop_name, getattr(conf, prop_name))


class BaseTexture(RenderMap):
    id ='BakeHighpolyBaseTex'
    name = 'baseTexBaked'
    
    BakeHighpolyBaseTextureDrawObjectIDIfNoTexture: BoolProperty(name = 'Write ObejctID if no texture', description = '', default = True)
    BakeHighpolyBaseTextureNoTexCol: FloatVectorProperty(name = 'Use color', description = '', default = (0.0, 0.0, 0.0), min = 0.0, max = 1.0, subtype = 'COLOR')
    BakeHighpolyBaseTextureBackgroundColor: FloatVectorProperty(name = 'Background color', description = '', default = (0.0, 0.0, 0.0), min = 0.0, max = 1.0, subtype = 'COLOR')
    

    def draw(self, layout:UILayout):
        layout.prop(self,'BakeHighpolyBaseTextureDrawObjectIDIfNoTexture')
        if not self.BakeHighpolyBaseTextureDrawObjectIDIfNoTexture :
            layout.prop(self,'BakeHighpolyBaseTextureNoTexCol')
            
        layout.prop(self,'BakeHighpolyBaseTextureBackgroundColor')
    
class VertexColor(RenderMap):
    id ='BakeHighpolyVCols'
    name = 'vcol'
    BakeHighpolyVColsBackgroundCol:FloatVectorProperty(name = 'Background color', description = '', default = (1.0, 1.0, 1.0), min = 0.0, max = 1.0, subtype = 'COLOR')
    
    def draw(self, layout:UILayout):
        layout.prop(self, 'BakeHighpolyVColsBackgroundCol')
    
class Dervative(RenderMap):
    id = 'GenDerivNM'
    name = 'deriv'
    DerivNMBackgroundColor:FloatVectorProperty(name = 'Background color', description = '', default = (0.498, 0.498, 0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    
    def draw(self, layout:UILayout):
        layout.prop(self, 'DerivNMBackgroundColor')

class Thickness(RenderMap):
    id = 'GenThickness'
    name = 'thickness'
    properties = {}
    def draw(self, layout:UILayout):
        layout.label(text="No Option")


class Proximity(RenderMap):
    id = 'GenProximity'
    name = 'proximity'
    ProximityRaysPerSample:IntProperty(name = 'Rays', description = 'Rays', default = 128)
    ProximityConeAngle:FloatProperty(name = 'Spread angle', description = '', default = 80.00)
    ProximityLimitRayDistance:BoolProperty(name = 'Limit ray distance', description = '', default = False)
    ProximityFlipNormals:BoolProperty(name = 'Flip Normals', description = '', default = False)
    ProximityFlipValue:BoolProperty(name = 'Flip Value', description = '', default = False)
    ProximityBackgroundColor:FloatVectorProperty(name = 'Background color', description = '', default = (1.0, 1.0, 1.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')

    def draw(self, layout:UILayout):
        layout.prop(self, 'ProximityLimitRayDistance')
        layout.prop(self, 'ProximityFlipNormals')
        layout.prop(self, 'ProximityFlipValue')
        layout.prop(self, 'ProximityRaysPerSample')
        layout.prop(self, 'ProximityConeAngle')
        layout.prop(self, 'ProximityBackgroundColor')

class Cavity(RenderMap):
    id = 'GenCavity'
    name = 'cavity'
    CavityRaysPerSample:IntProperty(name = 'Rays', description = '', default = 128)
    CavityJitter:BoolProperty(name = 'Jitter', description = '', default = False)
    CavitySearchRadius:FloatProperty(name = 'Radius', description = '', default = 0.500000, precision = 6)
    CavityContrast:FloatProperty(name = 'Contrast', description = '', default = 1.250, precision = 3)
    CavitySteps:IntProperty(name= 'Steps', description = '', default = 4, min = 0)
    CavityBackgroundColor:FloatVectorProperty(name = 'Background color', description = '', default = (1.0, 1.0, 1.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')

    def draw(self, layout:UILayout):
        layout.prop(self, 'CavityJitter', text = 'Cavity map jitter')
        split = layout.split()
        col = split.column()
        col.prop(self, 'CavityRaysPerSample')
        col.prop(self, 'CavitySteps')
        col = split.column()
        col.prop(self, 'CavitySearchRadius')
        col.prop(self, 'CavityContrast')
        layout.prop(self, 'CavityBackgroundColor')

class WireframeRayFails(RenderMap):
    id = 'GenWireRays'
    name = 'wirerays'
    RenderWireframe:BoolProperty(name = 'Render wireframe', description = 'Render wireframe', default = True)
    RenderRayFails:BoolProperty(name = 'Render rayfails', description = '', default = True)
    RenderWireframeCol:FloatVectorProperty(name = 'Wireframe color', description = '', default = (1.0, 1.0, 1.0),min = 0.0, max = 1.0, precision = 3,  subtype = 'COLOR')
    RenderCWCol:FloatVectorProperty(name = 'CW', description = '', default = (0.0, 0.0, 1.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    RenderSeamCol:FloatVectorProperty(name = 'Seam', description = '', default = (0.0, 1.0, 0.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    RenderRayFailsCol:FloatVectorProperty(name = 'Color', description = '', default = (1.0, 0.0, 0.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    RenderWireframeBackgroundColor:FloatVectorProperty(name = 'Background color', description = '', default = (0.0, 0.0, 0.0),min = 0.0, max = 1.0, precision = 3,  subtype = 'COLOR')

    def draw(self, layout:UILayout):
        split = layout.split()
        col = split.column()
        col.prop(self, 'RenderWireframe')
        col.prop(self, 'RenderRayFails')
        col = split.column()
        col.prop(self, 'wire')
        row = layout.row()
        row.prop(self, 'RenderCWCol')
        row.prop(self, 'RenderWireframeCol', text = 'Wire color')
        row = layout.row()
        row.prop(self, 'RenderRayFailsCol', text = 'Rayfail color')
        row.prop(self, 'RenderSeamCol', text = 'Seam color')
        layout.prop(self, 'RenderWireframeBackgroundColor')

class Convexity(RenderMap):
    id = 'GenConvexity'
    name = 'convexity'
    ConvexityScale:FloatProperty(name = 'Scale', description = '', default = 1.000, precision = 3)
    ConvexityBackgroundColor:FloatVectorProperty(name = 'Background color', description = '', default = (1.0, 1.0, 1.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    
    def draw(self, layout:UILayout):
        layout.prop(self, 'ConvexityScale')
        layout.prop(self, 'ConvexityBackgroundColor')

class Curvature(RenderMap):
    id = 'GenCurv'
    name = 'curvature'
    CurvRaysPerSample:IntProperty(name = 'Rays', description = '', default = 128)
    CurvJitter:BoolProperty(name = 'Jitter', description = '', default = False)
    CurvConeAngle:FloatProperty(name = 'Spread angle', description = '', default = 162.00)
    CurvBias:FloatProperty(name = 'Bias', description = '', default = 0.0001000000, precision = 10)
    CurvAlgorithm:EnumProperty(items = algorithm, name = 'Algorithm', description = '', default = 'Average')
    CurvDistribution:EnumProperty(items = distribution, name = 'Distribution', description = '', default = 'Cosine')
    CurvSearchDistance:FloatProperty(name = 'Search distance', description = '', default = 1.00000000, precision = 8)
    CurvTonemap:EnumProperty(items = tonemapping, name = 'Tonemapping', description = 'Tone mapping method', default = 'Monocrome')
    CurvSmoothing:BoolProperty(name = 'Smoothing', description = '', default = True)
    CurvBackgroundColor:FloatVectorProperty(name = 'Background color', description = 'Background color', default = (0.0, 0.0, 0.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    
    def draw(self, layout:UILayout):
        row = layout.row(align=False)
        row.prop(self, 'CurvJitter')       
        row.prop(self, 'CurvSmoothing')    
        layout.prop(self, 'CurvRaysPerSample')
        layout.prop(self, 'CurvBias')
        layout.prop(self, 'CurvConeAngle') 
        layout.prop(self, 'CurvSearchDistance')            
        layout.prop(self, 'CurvAlgorithm')
        layout.prop(self, 'CurvTonemap')
        layout.prop(self, 'CurvDistribution')
        layout.prop(self, 'CurvBackgroundColor')

class Translucency(RenderMap):
    id = 'GenTranslu'
    name = 'translucency'
    TransluRaysPerSample:IntProperty(name = 'Rays',default = 128)
    TransluDistribution:EnumProperty(items = distribution,name = 'Distibution',default = 'Uniform')
    TransluBias:FloatProperty(name = 'Bias',default = 0.000500)
    TransluConeAngle:FloatProperty(name = 'Angle',default = 162.00)
    TransluJitter:BoolProperty(name = 'Jitter',default = False)
    TransluDist:FloatProperty(name = 'Search distance',default = 1.00000000)
    TransluBackgroundColor:FloatVectorProperty(name = 'Background color',default = (1.0, 1.0, 1.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    
    def draw(self, layout:UILayout):
        layout.prop(self, 'TransluRaysPerSample')
        layout.prop(self, 'TransluDistribution')
        split = layout.split()
        col = split.column()
        col.prop(self, 'TransluBias')
        col.prop(self, 'TransluJitter')
        col = split.column()
        col.prop(self, 'TransluConeAngle')
        col.prop(self, 'TransluDist')
        row = layout.row()
        layout.prop(self, 'TransluBackgroundColor')

class AO(RenderMap):
    id = 'GenAO'
    name = 'occlusion'
    AORaysPerSample:IntProperty(name = 'Rays', description = '', default = 128, min = 0)
    AODistribution:EnumProperty(items = distribution, name = 'Distribution', description = 'Distribution mode', default = 'Uniform')
    AOBias:FloatProperty(name = 'Bias', description = '', default = 0.080000, precision = 6)
    AOConeAngle:FloatProperty(name = 'Spread angle', description = '', default = 162.00)
    AOLimitRayDistance:BoolProperty(name = 'Limit ray distance', description = 'Limit ray distance', default = False)
    AOAttenConstant:FloatProperty(name = '', description = '', default = 1.00000)
    AOAttenLinear:FloatProperty(name = '', description = '', default = 0.00000)
    AOAttenCuadratic:FloatProperty(name = '', description = '', default = 0.00000)
    AOJitter:BoolProperty(name = 'Jitter', description = '', default = False)
    AOIgnoreBackfaceHits:BoolProperty(name = 'Ignore backface hits', description = '', default = False)
    AOAllowPureOccluded:BoolProperty(name = 'Allow 100% occlusion', description = 'Allow 100% occlusion', default = True)
    AOOccludedColor:FloatVectorProperty(name = 'Occluded color', description = 'Occluded color', default = (0.0, 0.0, 0.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    AOUnoccludedColor:FloatVectorProperty(name = 'Unoccluded color', description = 'Unoccluded color', default = (1.0, 1.0, 1.0), min= 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    AOBackgroundColor:FloatVectorProperty(name = 'Background color', description = '', default = (1.0, 1.0, 1.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    def draw(self, layout:UILayout):
        row = layout.row()
        row.prop(self, 'AOAllowPureOccluded')
        row.prop(self, 'AOJitter')
        row = layout.row()
        row.prop(self, 'AOLimitRayDistance')
        row.prop(self, 'AOIgnoreBackfaceHits')
        layout.prop(self, 'AORaysPerSample')
        layout.prop(self, 'AOBias')
        layout.prop(self, 'AOConeAngle')
        layout.label(text="Attenuation:")
        row = layout.row()            
        row.prop(self, 'AOAttenConstant', text = 'Constant')
        row.prop(self, 'AOAttenLinear', text = 'Linear')
        row.prop(self, 'AOAttenCuadratic', text = 'Quadratic')
        layout.prop(self, 'AODistribution')
        row = layout.row()
        row.prop(self, 'AOOccludedColor', text = 'Occluded')
        row.prop(self, 'AOUnoccludedColor', text = 'Unoccluded')
        row.prop(self, 'AOBackgroundColor', text = 'Background')

class Direction(RenderMap):
    id = 'GenDirections'
    name = 'direction'
    DirectionsSwizzleX:EnumProperty(items = swizzle_coords, name = '', description = '', default = 'X+')
    DirectionsSwizzleY:EnumProperty(items = swizzle_coords, name = '', description = '', default = 'Y+')
    DirectionsSwizzleZ:EnumProperty(items = swizzle_coords, name = '', description = '', default = 'Z+')
    DirectionsTS:BoolProperty(name = 'Tangent space', description = 'Generate tangent space normal map, otherwise use object space', default = True)
    DirectionsTonemap:EnumProperty(items = normalization, name = 'Normalization', description = 'Normalization', default = 'Interactive')
    DirectionsTonemapMin:FloatProperty(name = 'Min', description = '', default = 0.00000, precision = 5)
    DirectionsTonemapMax:FloatProperty(name = 'Max', description = '', default = 0.00000, precision = 5)
    DirectionsBackgroundColor:FloatVectorProperty(name = 'Background color', description = '', default = (0.0, 0.0, 0.0),min = 0.0, max = 1.0, precision = 3,  subtype = 'COLOR')
    def draw(self, layout:UILayout):
        layout.prop(self, 'DirectionsTS')
        layout.prop(self, 'DirectionsTonemap')
        if self.DirectionsTonemap == 'Manual':
            row = layout.row()
            row.prop(self, 'DirectionsTonemapMin')
            row.prop(self, 'DirectionsTonemapMax')
        split = layout.split()
        col = split.column()
        col.prop(self, 'DirectionsBackgroundColor')
        col = split.column()
        col.label(text='Swizzle:')
        col.prop(self, 'DirectionsSwizzleX')
        col.prop(self, 'DirectionsSwizzleY')
        col.prop(self, 'DirectionsSwizzleZ')

class Radiosity(RenderMap):
    id = 'GenRadiosityNormals'
    name = 'radiosity'
    RadiosityNormalsRaysPerSample:IntProperty(name = 'Rays', description = '', default = 128, min = 0)
    RadiosityNormalsEncodeAO:BoolProperty(name = 'Encode occlusion', description = '', default = True)
    RadiosityNormalsDistribution:EnumProperty(items = distribution, name = 'Distribution', description = 'Distribution', default = 'Uniform')
    RadiosityNormalsBias:FloatProperty(name = 'Bias', description = '', default = 0.080000, precision = 6)
    RadiosityNormalsConeAngle:FloatProperty(name = 'Spread angle', description = '', default = 162.00)
    RadiosityNormalsLimitRayDistance:BoolProperty(name = 'Limit ray distance', description = '', default = False)
    RadiosityNormalsAttenConstant:FloatProperty(name = '', description = '', default = 1.00000, precision = 5)
    RadiosityNormalsAttenLinear:FloatProperty(name = '', description = '', default = 0.00000, precision = 5)
    RadiosityNormalsAttenCuadratic:FloatProperty(name = '', description = '', default = 0.00000, precision = 5)
    RadiosityNormalsJitter:BoolProperty(name = 'Jitter', description = '', default = True)
    RadiosityNormalsCoordSys:EnumProperty(items = coord_system, name = 'Coordinate system', description = 'Coordinate system', default = 'AliB')
    RadiosityNormalsContrast:FloatProperty(name = 'Contrast', description = '', default = 1.00000, precision = 5)
    RadiosityNormalsAllowPureOcclusion:BoolProperty(name = 'Allow pure occlusion', description = '', default = False)
    RadNMBackgroundColor:FloatVectorProperty(name = 'Background color', description = 'Background color', default = (0.0, 0.0, 0.0), min = 0.0, max = 1.0, subtype = 'COLOR')
    
    def draw(self, layout:UILayout):
        split = layout.split()                       
        col = split.column()
        col.prop(self, 'RadiosityNormalsEncodeAO')
        col.prop(self, 'RadiosityNormalsAllowPureOcclusion')
        col.prop(self, 'RadiosityNormalsJitter')
        col = split.column()
        col.prop(self, 'RadiosityNormalsLimitRayDistance') 
        split = layout.split()
        col = split.column()
        col.prop(self, 'RadiosityNormalsRaysPerSample')
        col.prop(self, 'RadiosityNormalsBias')
        col = split.column()
        col.prop(self, 'RadiosityNormalsConeAngle')
        col.prop(self, 'RadiosityNormalsContrast')
        row = layout.row()
        row.prop(self, 'RadiosityNormalsCoordSys', text = 'Coordinates')
        row.prop(self, 'RadiosityNormalsDistribution')
        row = layout.row()
        row.prop(self, 'RadiosityNormalsAttenConstant', text = 'Constant')
        row.prop(self, 'RadiosityNormalsAttenLinear', text = 'Linear')
        row.prop(self, 'RadiosityNormalsAttenCuadratic', text = 'Quadratic')
        layout.prop(self, 'RadNMBackgroundColor')

class PRT(RenderMap):
    id = 'GenPRT'
    name = 'prt'
    PRTRaysPerSample:IntProperty(name = 'Rays', description = '', default = 128)
    PRTBias:FloatProperty(name = 'Bias', description = '', default = 0.080000, precision = 6)
    PRTConeAngle:FloatProperty(name = 'Spread angle', description = '', default = 179.50)
    PRTLimitRayDistance:BoolProperty(name = 'Limit ray distance', description = '', default = False)
    PRTJitter:BoolProperty(name = 'Jitter', description = '', default = True)
    PRTNormalize:BoolProperty(name = 'PRT color normalize', description = '', default = True)
    PRTThreshold:FloatProperty(name = 'Threshold', description = '', default = 0.005000, precision = 6)
    PRTBackgroundColor:FloatVectorProperty(name = 'Background color', description = 'Background color', default = (0.0, 0.0, 0.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    def draw(self, layout:UILayout):
        split = layout.split()
        col = split.column()
        col.prop(self, 'PRTLimitRayDistance')
        col = split.column()
        col.prop(self, 'PRTNormalize')
        col.prop(self, 'PRTJitter')
        split = layout.split()
        col = split.column()
        col.prop(self, 'PRTRaysPerSample')
        col.prop(self, 'PRTBias')
        col = split.column()
        col.prop(self, 'PRTConeAngle')
        col.prop(self, 'PRTThreshold')
        layout.prop(self, 'PRTBackgroundColor')
        
class BentNormal(RenderMap):
    id = 'GenBent'
    name = 'bent_normals'
    BentRaysPerSample:IntProperty(name = 'Rays', description = '', default = 128, min = 0)
    BentBias:FloatProperty(name = 'Bias', description = '', default = 0.080000, precision = 6)
    BentConeAngle:FloatProperty(name = 'Spread angle', description = '', default = 162.00)
    BentLimitRayDistance:BoolProperty(name = 'Limit ray distance', description = '', default = False)
    BentJitter:BoolProperty(name = 'Jitter', description = '', default = False)
    BentSwizzleX:EnumProperty(items = swizzle_coords, name = '', description = '', default = 'X+')
    BentSwizzleY:EnumProperty(items = swizzle_coords, name = '', description = '', default = 'Y+')
    BentSwizzleZ:EnumProperty(items = swizzle_coords, name = '', description = '', default = 'Z+')
    BentTangentSpace:BoolProperty(name = 'Tangent space', description = 'Generate tangent space normal map, otherwise use object space', default = False)
    BentDistribution:EnumProperty(items = distribution, name = 'Distribution', description = '', default = 'Uniform')
    BentBackgroundColor:FloatVectorProperty(name = 'Background color', description = 'Background color', default = (0.502, 0.502, 1.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    def draw(self, layout:UILayout):
        split = layout.split()
        col = split.column()
        col.prop(self, 'BentJitter')
        col.prop(self, 'BentLimitRayDistance')            
        col = split.column()
        col.prop(self, 'BentTangentSpace')
        layout.prop(self, 'BentRaysPerSample')                        
        layout.prop(self, 'BentBias')            
        layout.prop(self, 'BentConeAngle')
        layout.prop(self, 'BentDistribution', text = 'Distribution')
        split = layout.split()
        col = split.column()
        col.prop(self, 'BentBackgroundColor')
        col = split.column()
        col.label(text='Swizzle:')
        col.prop(self, 'BentSwizzleX')
        col.prop(self, 'BentSwizzleY')
        col.prop(self, 'BentSwizzleZ')
        
class Height(RenderMap):
    id = 'GenHeights'
    name = 'height'
    HMBackgroundColor:FloatVectorProperty(name = 'Background color', description = 'Background color of the height map', default = (1.0, 1.0, 1.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    HeightTonemap:EnumProperty(items = normalization, name = 'Normalization', description = 'Normalization mode', default = 'Interactive')
    HeightTonemapMin:FloatProperty(name = 'Min', description = '', default = 0.00000, precision = 5)
    HeightTonemapMax:FloatProperty(name = 'Max', description = '', default = 0.00000, precision = 5)
    def draw(self, layout:UILayout):        
        layout.prop(self, 'HeightTonemap')
        if self.HeightTonemap == 'Manual':
            row = layout.row()
            row.prop(self, 'HeightTonemapMin')
            row.prop(self, 'HeightTonemapMax')
        layout.prop(self, 'HMBackgroundColor')


class Normal(RenderMap):
    id = 'GenNormals'
    name = 'normals'
    SwizzleX:EnumProperty(items = swizzle_coords, name = '', description = '', default = 'X+')
    SwizzleY:EnumProperty(items = swizzle_coords, name = '', description = '', default = 'Y+')
    SwizzleZ:EnumProperty(items = swizzle_coords, name = '', description = '', default = 'Z+')
    TangentSpace:BoolProperty(name = 'Tangent space', description = 'Generate tangent space normal map. Otherwise, use object space', default = True)
    NMBackgroundColor:FloatVectorProperty(name = 'Background color', description = 'Background color of the normal map', default = (0.502, 0.502, 1.0), min = 0.0, max = 1.0, precision = 3, subtype = 'COLOR')
    def draw(self, layout:UILayout):
        split = layout.split()   
        col = split.column()
        col.prop(self, 'TangentSpace')
        col.separator()
        col.separator()
        col.prop(self, 'NMBackgroundColor')
        col = split.column()
        col.label(text='Swizzle:')
        col.prop(self, 'SwizzleX')
        col.prop(self, 'SwizzleY')
        col.prop(self, 'SwizzleZ')