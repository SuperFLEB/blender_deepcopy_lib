from typing import Iterable, Callable

import bpy

from material import deep_get_materials
from .common import name_copy


def deep_copy_nodegroups(tree: bpy.types.NodeTree, prefix: str, copies_lookup=None, ttl=1000):
    """Deep-copy nodegroups from a root tree."""
    copies_lookup = copies_lookup if copies_lookup is not None else {}
    if not tree.nodes:
        return
    group_nodes_enumerated = [(tup[0], tup[1].node_tree) for tup in enumerate(tree.nodes) if tup[1].type == "GROUP"]
    for idx, group_tree in group_nodes_enumerated:
        if group_tree in copies_lookup:
            tree.nodes[idx].node_tree = copies_lookup[group_tree]
            continue
        gt_copy = group_tree.copy()
        gt_copy.name = name_copy(prefix, group_tree.name)
        copies_lookup[group_tree] = gt_copy
        tree.nodes[idx].node_tree = gt_copy
        deep_copy_nodegroups(gt_copy, prefix, copies_lookup, ttl - 1)


def deep_copy_material_nodegroups(objects: Iterable[bpy.types.Object], prefix: str):
    """
    Deep-copy all material nodegroups on all materials on the given objects.
    - Does NOT copy objects. Do that first.
    - Does NOT copy materials. Do that first.
    """
    copies_lookup = {}
    materials = deep_get_materials(objects)

    for mat in materials:
        deep_copy_nodegroups(mat.node_tree, prefix, copies_lookup)
