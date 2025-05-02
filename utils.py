import bpy
from bpy.types import Object, Context, Mesh, Material
import bmesh

def unlink_xnormal_collection():
	bpy.context.scene.collection.children.unlink(xnormal_collection())

def xnormal_collection():
	collection = bpy.data.collections.get("xNormal_Exports") or bpy.data.collections.new("xNormal_Exports")
	collection.hide_viewport = False
	if collection.name not in bpy.context.scene.collection.children:
		bpy.context.scene.collection.children.link(collection)
	return collection

def snapshot_mesh(context:Context, ob:Object, rm_materials:list[Material], shapekey:str = None, uv:str = None):
	ob_name = ob.name
	collection = xnormal_collection()
	# 一時コレクションにリンクしておく
	if ob.name not in collection.objects:
		collection.objects.link(ob)

	for o in bpy.context.scene.objects:
		o.hide_set(o != ob)
		o.select_set(o == ob)
	context.view_layer.objects.active = ob
	before = set(bpy.context.scene.objects)
	
	if ob.type == 'MESH':
		bpy.ops.object.duplicate()
	else : #非メッシュならコンバート
		bpy.ops.object.convert(target='MESH', keep_original=True, merge_customdata=True)

	after = set(bpy.context.scene.objects)

	duplicated_objs = after - before
	if not len(duplicated_objs): return None
	ob = list(duplicated_objs)[0]
	
	mesh:Mesh = ob.data

	uvs = mesh.uv_layers.keys()
	if uv and uv in uvs:
		for uv_layer in uvs:
			if uv_layer != uv:
				mesh.uv_layers.remove(mesh.uv_layers[uv_layer])

	has_shape = shapekey is not None and mesh.shape_keys is not None and shapekey in mesh.shape_keys.key_blocks
	if has_shape:
		mesh.shape_keys.key_blocks[shapekey].driver_remove('value')
		mesh.shape_keys.key_blocks[shapekey].value = 0.0
	
	rm_mat_indice = [i for i, slot in enumerate(ob.material_slots) if slot.material in rm_materials]

	bm = bmesh.new()
	bm.from_object(ob, context.evaluated_depsgraph_get())
	bm.faces.ensure_lookup_table()
	bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4], quad_method='BEAUTY', ngon_method='BEAUTY')
	
	#シェイプキーベイク
	if has_shape:
		mesh.shape_keys.key_blocks[shapekey].value = 1.0
		shape_bm = bmesh.new()
		shape_bm.from_object(ob, context.evaluated_depsgraph_get())
		
		bm.verts.ensure_lookup_table()
		shape_bm.verts.ensure_lookup_table()

		for bm_vert, shape_vert in zip(bm.verts, shape_bm.verts):
			bm_vert.co = shape_vert.co
	
	#不要マテリアル除去
	bmesh.ops.delete(bm, geom=[face for face in bm.faces if face.material_index in rm_mat_indice], context='FACES')
	
	name = ob_name + "_xNormal"
	snap_mesh = bpy.data.meshes.new(name)
	snap_ob = bpy.data.objects.new(name, snap_mesh)
	snap_ob.matrix_world = ob.matrix_world.copy()

	bm.to_mesh(snap_mesh)
	
	bpy.data.objects.remove(ob, do_unlink=True)
	bpy.data.meshes.remove(mesh, do_unlink=True)

	return snap_ob