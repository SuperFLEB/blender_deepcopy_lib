import bpy
from typing import Iterable
from . import material
from . import common

if "_LOADED" in locals():
    import importlib

    for mod in (material, common):  # list all imports here
        importlib.reload(mod)
_LOADED = True

deep_get_materials = material.deep_get_materials
name_copy = common.name_copy
get_existing = common.get_existing

def deep_copy_nodegroups(tree: bpy.types.NodeTree, prefix: str, prefer_existing: bool = False, copies_lookup=None, ttl=1000):
    """Deep-copy nodegroups from a root tree."""
    copies_lookup = copies_lookup if copies_lookup is not None else {}
    copied_trees = set()
    if not tree.nodes:
        return
    group_nodes_enumerated = [(tup[0], tup[1].node_tree) for tup in enumerate(tree.nodes) if tup[1].type == "GROUP"]
    for idx, group_tree in group_nodes_enumerated:
        if group_tree in copies_lookup:
            tree.nodes[idx].node_tree = copies_lookup[group_tree]
            continue

        new_name = name_copy(prefix, group_tree.name)
        existing = None

        if prefer_existing:
            existing = get_existing(new_name, bpy.data.node_groups)

        if existing:
            new_gt = existing
        else:
            new_gt = group_tree.copy()
            new_gt.name = new_name
            copied_trees.add(new_gt)

        copies_lookup[group_tree] = new_gt
        tree.nodes[idx].node_tree = new_gt
        copied_trees |= deep_copy_nodegroups(new_gt, prefix, prefer_existing, copies_lookup, ttl - 1)

    return copied_trees


def deep_copy_material_nodegroups_from_objects(objects: Iterable[bpy.types.Object], prefix: str, prefer_existing: bool = False):
    """Deep-copy all nodegroups on all materials in the given objects.
       Mutates the given materials, and does not copy them, so copy them first."""
    deep_copy_material_nodegroups(deep_get_materials(objects), prefix)


def deep_copy_material_nodegroups(materials: Iterable[bpy.types.Material], prefix: str, prefer_existing: bool = False):
    """Deep-copy all nodegroups on all materials given. Mutates the given materials, so copy them first."""
    copies_lookup = {}
    for mat in materials:
        deep_copy_nodegroups(mat.node_tree, prefix, prefer_existing, copies_lookup)
