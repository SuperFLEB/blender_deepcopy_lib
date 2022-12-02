from typing import Iterable, Callable

import bpy

from .object import deep_get_objects
from .common import name_copy


def deep_get_materials(root_objects: Iterable[bpy.types.Object]) -> set[bpy.types.Material]:
    """Get all materials in the current collection and all instanced collections."""
    objects = deep_get_objects(root_objects, lambda o: o.data)
    materials = set()
    for obj in objects:
        materials |= set(obj.data.materials)
        materials |= {s.material for s in obj.material_slots}
    return materials


def deep_copy_materials(objects: Iterable[bpy.types.Object], prefix: str):
    """Make copies of materials on all objects and instanced collections.
    Does not unlink object data materials-- be sure to copy objects and data before running this."""

    all_objects = deep_get_objects(objects, lambda obj: obj.data)

    seen_datas = set()
    copies_lookup = {}

    for obj in all_objects:
        if obj.data not in seen_datas:
            seen_datas.add(obj.data)
            for idx, mat in enumerate(obj.data.materials):
                if mat in copies_lookup.values():
                    continue
                if mat in copies_lookup:
                    obj.data.materials[idx] = copies_lookup[mat]
                    continue
                material_copy = mat.copy()
                material_copy.name = name_copy(prefix, mat.name)
                copies_lookup[mat] = material_copy
                obj.data.materials[idx] = material_copy

        for slot in obj.material_slots:
            if slot.material in copies_lookup.values():
                continue

            if slot.material in copies_lookup:
                slot.material = copies_lookup[slot.material]
                continue
            material_copy = slot.material.copy()
            material_copy.name = name_copy(prefix, slot.material.name)
            copies_lookup[slot.material] = material_copy
            slot.material = material_copy
