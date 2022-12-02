import bpy


def name_copy(prefix, name):
    """Format a "copied" name with a prefix."""
    return f"{prefix}.{name}"


def partition_collection_instances(all_objects) -> tuple[set[bpy.types.Object], set[bpy.types.Object]]:
    """Split a group of objects into two sets based on whether they don't or do have instance_collections"""
    split = (set(), set())
    for ob in all_objects:
        split[int(bool(ob.instance_collection))].add(ob)
    return split
