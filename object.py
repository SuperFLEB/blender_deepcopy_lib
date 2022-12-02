from typing import Iterable, Callable
import bpy

from .common import name_copy
from .common import partition_collection_instances


def copy_swap_object(ob, colls, prefix, copies_lookup=None):
    copies_lookup = copies_lookup if copies_lookup is not None else {}

    ob_copy = ob.copy()
    ob_copy.name = name_copy(prefix, ob.name)

    for coll in colls:
        coll.objects.unlink(ob)
        coll.objects.link(ob_copy)

    if not ob.data:
        # Non-data object (empty, etc.) -- just return the copy of the object
        return ob_copy

    if ob.data in copies_lookup:
        ob_copy.data = copies_lookup[ob.data]
    else:
        ob_copy.data = ob_copy.data.copy()
        ob_copy.data.name = name_copy(prefix, ob.data.name)
        copies_lookup[ob.data] = ob_copy.data

    return ob_copy


def copy_swap_collection(obj, prefix, copies_lookup=None):
    """Swap an object's instance_collection with a copy.
       Does not swap the object itself (i.e., you should pass a copied object)."""
    copies_lookup = copies_lookup if copies_lookup is not None else {}
    print("SCC check object=", obj)

    if obj.instance_collection in copies_lookup:
        print("SCC found ic=", obj.instance_collection.name)
        obj.instance_collection = copies_lookup[obj.instance_collection]
    else:
        ic_copy = obj.instance_collection.copy()
        ic_copy.name = name_copy(prefix, obj.instance_collection.name)
        print("SCC new ic=", ic_copy.name)
        copies_lookup[obj.instance_collection] = ic_copy
        obj.instance_collection = ic_copy

    print("KS", [c.name for c in copies_lookup.keys() if type(c) is bpy.types.Collection])

    return obj


def deep_get_objects(objects: Iterable[bpy.types.Object], filter_on: Callable = None, ttl: int = 1000) -> set[bpy.types.Object]:
    """Get all objects in the current collection and all instanced collections."""
    if ttl <= 0:
        return set()

    plain_objects, ci_objects = partition_collection_instances(objects)

    objects = ({ob for ob in plain_objects if filter_on(ob)} if filter_on else plain_objects)
    for subc_obj in ci_objects:
        objects |= deep_get_objects(subc_obj.instance_collection.objects, filter_on, ttl - 1)

    return objects


def deep_copy_collection_contents(coll: bpy.types.Collection, prefix="copy_of", copies_lookup: dict[bpy.types.ID, bpy.types.ID] = None, ttl=1000):
    """Deep-copy a collection's contents. Preserves linked duplicates within the hierarchy.
       Does NOT copy the collection itself, so be sure to do that first if you need to."""
    copies_lookup = copies_lookup if copies_lookup is not None else {}
    if ttl <= 0:
        return

    objects, coll_insts = partition_collection_instances(coll.objects)

    # Copy simple objects and object data
    for ob in objects:
        copy_swap_object(ob, [coll], prefix, copies_lookup)

    # Copy collections
    collections_to_deep_copy = set()
    for ci_ob in coll_insts:
        ob_copy = copy_swap_object(ci_ob, [coll], prefix, copies_lookup)
        copied = ob_copy.instance_collection in copies_lookup
        copy_swap_collection(ob_copy, prefix, copies_lookup)
        if not copied:
            collections_to_deep_copy.add(ob_copy.instance_collection)

    # Copy everything in the (copies_lookup of any) collection instances
    for inst_coll in collections_to_deep_copy:
        deep_copy_collection_contents(inst_coll, prefix, copies_lookup, ttl - 1)


def deep_copy_objects(objects: Iterable[bpy.types.Object], prefix: str) -> set[bpy.types.Object]:
    """Copy the object and any hierarchy of collection instances under it.
       Copies any objects or collections encountered. Does not copy Materials or Geonodes."""

    copies_lookup = {}
    copied_objs = set()

    for obj in list(objects):
        # Swap the object with a copy having the same data
        obj_copy = copy_swap_object(obj, list(obj.users_collection), prefix, copies_lookup)
        copied_objs.add(obj_copy)

        # If the object isn't a collection instance, we're done.
        if not obj_copy.instance_collection:
            continue

        # If the instanced collection has already been copied, just apply the copy.
        if obj_copy.instance_collection in copies_lookup:
            obj_copy.instance_collection = copies_lookup[obj_copy.instance_collection]
            continue

        # If the instanced collection hasn't been seen, duplicate/apply the collection...
        copy_swap_collection(obj_copy, prefix, copies_lookup)
        # ...and deep-copy its contents
        deep_copy_collection_contents(obj_copy.instance_collection, prefix, copies_lookup)
    return copied_objs
