import bpy


def is_clone(name: str) -> bool:
    """Determine whether the given name is a clone/suffixed one (Something.001)"""
    return (
            len(name) > 4 and
            name[-4] == "." and
            name[-3:].isnumeric()
    )


def object_basename(name: str) -> str:
    """Remove the '.001' (etc.) suffix from a name, if it exists"""
    return name[:-4] if is_clone(name) else name


def name_copy(prefix, name):
    """Format a "copied" name with a prefix."""
    return f"{prefix}.{name}"


def partition_collection_instances(all_objects) -> tuple[set[bpy.types.Object], set[bpy.types.Object]]:
    """Split a group of objects into two sets based on whether they don't or do have instance_collections"""
    split = (set(), set())
    for ob in all_objects:
        split[int(bool(ob.instance_collection))].add(ob)
    return split


def get_existing(desired_name: str, data_collection: bpy.types.bpy_prop_collection) -> bpy.types.ID:
    """If there is an existing nodegroup with the given name in the document, return it."""
    for item in data_collection:
        if object_basename(item.name) == desired_name:
            return item
    return None
