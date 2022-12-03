from . import object
from . import material
from . import node

if "_LOADED" in locals():
    import importlib

    for mod in (object, material, node,):  # list all imports here
        importlib.reload(mod)
_LOADED = True

deep_copy_objects = object.deep_copy_objects
deep_copy_materials = material.deep_copy_materials
deep_copy_material_nodegroups_from_objects = node.deep_copy_material_nodegroups_from_objects
deep_copy_material_nodegroups = node.deep_copy_material_nodegroups





