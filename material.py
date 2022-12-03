from typing import Iterable, Callable
from re import escape, match

import bpy

from . import object
from . import common

if "_LOADED" in locals():
    import importlib

    for mod in (object, common):  # list all imports here
        importlib.reload(mod)
_LOADED = True

deep_get_objects = object.deep_get_objects
name_copy = common.name_copy
get_existing = common.get_existing


def deep_get_materials(root_objects: Iterable[bpy.types.Object]) -> set[bpy.types.Material]:
    """Get all materials in the current collection and all instanced collections."""
    objects = deep_get_objects(root_objects, lambda o: o.data)
    materials = set()
    for obj in objects:
        materials |= set(obj.data.materials)
        materials |= {s.material for s in obj.material_slots}
    return materials


def deep_copy_materials(objects: Iterable[bpy.types.Object], prefix: str, prefer_existing: bool = False) -> set[bpy.types.Material]:
    """Make copies of materials on all objects and instanced collections.
    Does not unlink object data materials-- be sure to copy objects and data before running this.
    Returns the set of materials that were actually copied. Omits ones that were assigned because of prefer_existing."""

    all_objects = deep_get_objects(objects, lambda obj: obj.data)

    # Collect only copied materials so further operations don't touch re-used materials
    copied_materials = set()
    # Data-blocks that have already been processed, to prevent double hits on linked duplicates
    seen_datas = set()
    # Lookup for old->new changes that have already been made and can be reused
    copies_lookup = {}

    for obj in all_objects:
        # Get materials from objects' data
        if obj.data not in seen_datas:
            seen_datas.add(obj.data)

            for idx, mat in enumerate(obj.data.materials):
                if mat in copies_lookup.values():
                    continue
                if mat in copies_lookup:
                    obj.data.materials[idx] = copies_lookup[mat]
                    continue

                new_name = name_copy(prefix, mat.name)
                existing = None

                if prefer_existing:
                    existing = get_existing(new_name, bpy.data.materials)

                if existing:
                    new_material = existing
                else:
                    new_material = mat.copy()
                    new_material.name = new_name
                    copied_materials.add(new_material)

                copies_lookup[mat] = new_material
                obj.data.materials[idx] = new_material

        # Get materials from objects' material slots
        for slot in obj.material_slots:
            # Check this, because the data and the slots can point to the same place, depending on the material linking.
            if slot.material in copies_lookup.values():
                continue

            if slot.material in copies_lookup:
                slot.material = copies_lookup[slot.material]
                continue

            new_name = name_copy(prefix, slot.material.name)

            existing = None
            if prefer_existing:
                existing = get_existing(new_name)

            if existing:
                new_material = existing
            else:
                new_material = slot.material.copy()
                new_material.name = new_name
                copied_materials.add(new_material)

            copies_lookup[slot.material] = new_material
            slot.material = new_material

    return copied_materials
