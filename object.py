import bpy
from dataclasses import dataclass, field
from typing import Iterable, Callable
from bpy.types import ID, Object, Collection
from .common import name_copy
from .common import partition_collection_instances


@dataclass
class ReparentResults:
    success: dict[Object, list[Object]] = field(default_factory=dict)
    failure: dict[Object, list[Object]] = field(default_factory=dict)

    def succeed(self, obj: Object, target: Object):
        """
        Add a successful reparenting
        :param obj: Object being reparented
        :param target: New parent
        """
        self.success.setdefault(obj, []).append(target)

    def fail(self, obj: Object, target: Object):
        """
        Add an unsuccessful reparenting
        :param obj: Object being reparented
        :param target: Parent object
        """
        self.failure.setdefault(obj, []).append(target)


def copy_swap_object(obj: Object, colls: Iterable[Collection], prefix: str,
                     copies_lookup: dict[ID, ID] = None) -> Object:
    """
    Replace the specified object with a copy.

    :param obj: The object to copy
    :param colls: The collections the object belongs to
    :param prefix: The prefix to prepend to the object/data name
    :param copies_lookup: A common lookup dict where object/data references will be added. Object will be mutated.
    :return: The created object copy
    """
    copies_lookup = copies_lookup if copies_lookup is not None else {}

    obj_copy = obj.copy()
    obj_copy.name = name_copy(prefix, obj.name)

    for coll in colls:
        coll.objects.unlink(obj)
        coll.objects.link(obj_copy)

    if not obj.data:
        # Non-data object (empty, etc.) -- just return the copy of the object
        return obj_copy

    if obj.data in copies_lookup:
        obj_copy.data = copies_lookup[obj.data]
    else:
        obj_copy.data = obj_copy.data.copy()
        obj_copy.data.name = name_copy(prefix, obj.data.name)
        copies_lookup[obj.data] = obj_copy.data

    return obj_copy


def copy_swap_instance_collection(obj: Object, prefix: str, copies_lookup: object = None) -> None:
    """
    Swap an object's instance_collection with a copy.
    Does not swap the object itself (i.e., you should pass a copied object).

    :param obj: The object to copy
    :param prefix: The prefix to prepend to the object/data name
    :param copies_lookup: A common lookup dict where object/data references will be added. Object will be mutated.
    """
    copies_lookup = copies_lookup if copies_lookup is not None else {}

    if obj.instance_collection in copies_lookup:
        obj.instance_collection = copies_lookup[obj.instance_collection]
    else:
        ic_copy = obj.instance_collection.copy()
        ic_copy.name = name_copy(prefix, obj.instance_collection.name)
        copies_lookup[obj.instance_collection] = ic_copy
        obj.instance_collection = ic_copy

    return obj


def deep_get_objects(objects: Iterable[Object], filter_on: Callable = None, ttl: int = 1000) -> set[Object]:
    """
    Get all objects in the current collection and all instanced collections.

    :param objects: Objects to scan
    :param filter_on: Filter function to include/exclude found objects
    :param ttl: TTL to prevent infinite loops
    :return: Set of found objects
    """
    if ttl <= 0:
        return set()

    plain_objects, ci_objects = partition_collection_instances(objects)

    objects = ({ob for ob in plain_objects if filter_on(ob)} if filter_on else plain_objects)
    for subc_obj in ci_objects:
        objects |= deep_get_objects(subc_obj.instance_collection.objects, filter_on, ttl - 1)

    return objects


def deep_copy_collection_contents(coll: Collection, prefix: str = "copy_of", copies_lookup: dict[ID, ID] = None,
                                  ttl=1000) -> dict[Object, Object]:
    """
    Deep-copy a collection's contents. Preserves linked duplicates within the hierarchy.
    Does NOT copy the collection itself, so be sure to do that first if you need to.

    :param coll: Collection to scan
    :param prefix: Prefix for copied objects/data
    :param copies_lookup: A common lookup dict where object/data references will be added. Object will be mutated.
    :param ttl: TTL to prevent infinite loops
    :return:
    """
    copies_lookup = copies_lookup if copies_lookup is not None else {}
    object_copies_log = {}

    if ttl <= 0:
        return {}

    objects, coll_insts = partition_collection_instances(coll.objects)

    # Copy simple objects and object data
    for ob in objects:
        object_copies_log[ob] = copy_swap_object(ob, [coll], prefix, copies_lookup)

    # Copy collections
    collections_to_deep_copy = set()
    for ci_ob in coll_insts:
        ob_copy = copy_swap_object(ci_ob, [coll], prefix, copies_lookup)
        copy_swap_instance_collection(ob_copy, prefix, copies_lookup)

        if ob_copy.instance_collection not in copies_lookup:
            collections_to_deep_copy.add(ob_copy.instance_collection)

    # Copy everything in the (copies_lookup of any) collection instances
    for inst_coll in collections_to_deep_copy:
        object_copies_log.update(deep_copy_collection_contents(inst_coll, prefix, copies_lookup, ttl - 1))

    return object_copies_log


def reconstruct_parentage(log: dict[Object, Object]) -> ReparentResults:
    """
    Reconstruct parent-child relationships to copies.
    :param log: Source->Destination copy log
    """

    results = ReparentResults()

    # Reparent direct parents
    for orig, copied in {orig: copied for (orig, copied) in log.items() if copied.parent}.items():
        if orig.parent not in log:
            results.fail(copied, copied.parent)
            continue
        # The matrix_local may get re-set when the reparent happens, so explicitly preserve and restore it
        matrix_local = copied.matrix_local.copy()
        copied.parent = log[orig.parent]
        copied.matrix_local = matrix_local
        results.succeed(copied, copied.parent)

    # TODO: Reparent vertex parents

    return results


def deep_copy_objects(objects: Iterable[Object], prefix: str) -> set[Object]:
    """
    Replaces objects or collections encountered with copies. Does not copy Materials or Geonodes.

    :param objects: Objects to scan
    :param prefix: Prefix for copied objects/data
    :return: Set of copies of replaced objects
   """

    # Lookup for old->new object/data relations of all sorts. May be mutated in called functions.
    copies_lookup: dict[ID, ID] = {}

    # Log of old->new changes made, used to reconstruct parent relationships.
    object_copies_log: dict[Object, Object] = {}

    for obj in list(objects):
        # Swap the object with a copy having the same data
        obj_copy = copy_swap_object(obj, list(obj.users_collection), prefix, copies_lookup)
        object_copies_log[obj] = obj_copy

        # If the object isn't a collection instance, we're done.
        if not obj_copy.instance_collection:
            continue

        # If the instanced collection has already been copied, just apply the copy.
        if obj_copy.instance_collection in copies_lookup:
            obj_copy.instance_collection = copies_lookup[obj_copy.instance_collection]
            continue

        # If the instanced collection hasn't been seen, duplicate/apply the collection...
        copy_swap_instance_collection(obj_copy, prefix, copies_lookup)
        # ...and deep-copy its contents
        copies_lookup.update(deep_copy_collection_contents(obj_copy.instance_collection, prefix, copies_lookup))

    reparent_results = reconstruct_parentage(object_copies_log)

    if reparent_results.failure:
        print("Failed to re-parent some objects to copies (probably because the parents were not included in the copy:")
        for src, fails in reparent_results.failure.items():
            for dest in fails:
                print(f"   - {src} ---> {dest}")

    return set(object_copies_log.values())
