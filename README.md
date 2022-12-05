# Blender Deep Copy Functions

https://github.com/SuperFLEB/blender_deepcopy_lib

*This is made to fill specific needs-- namely to support converting imports into namespaced sets of objects
in the scene-- so it may be opinionated and quirky in some regards. It's also currently a work in
progress, so things are liable to change drastically.*

A Blender Python library that allows (somewhat, see caveats) deep-copying of Objects, Collections, Materials,
and Node Groups, recursing into Collection Instances, Materials, and Node Groups.

Data is copied to be unique within the requested set of objects, but is shared within the set. The result is a
namespaced set of unique Collections, Materials, Node Groups, Objects, and object data. Note that objects are not
*duplicated*-- there will still be only one in the scene-- but are replaced with their copies.

## Known quirks/issues:
* No support for Geometry Nodes, because having to rewrite and track instancing is liable to be a massive pain.
* Collections are not copied into the scene, they are merely copied in the file.
* (Probably) does not handle physics/simulation. Will probably never support physics or simulation.
* Parents that are not included in the request will not be copied. The copies will be parented to the outside objects.
* Copying a parent object but not the child object will break the parent-child link. A set of failed parent-child links is returned from the `reconstruct_parentage` function.
* Original data that is not used elsewhere will be orphaned. Users should run a recursive Clean Up on the file after
  using this.
* If something from outside the copy job has a parent that gets copied, the parent link will be broken. Furthermore,
  the parent will be orphaned, possibly causing the position to reset after orphan-cleanup. This problem is outside the
  scope of the library, and it will probably not be fixed.

There is also a `prefer_existing` option for material-related copying. This will reuse existing materials or node groups
that match the (prefixed) name. So, if you are making a copy of "Material1" with a prefix "copy_of" and
"copy_of.Material1" already exists in the file, "copy_of.Material1" will be used if `prefer_existing` is set. This
allows for copying more batches of objects into the same Material "namespace" that already exists.

For other issues that are intended to be fixed, see the GitHub Issues page:
https://github.com/SuperFLEB/blender_deepcopy_lib/issues

## To use

To see a demonstration addon, check out:
https://github.com/SuperFLEB/blender_deep_copy_demo

### Methods:

Exposed methods are:

Method|Purpose
---|---
deep_copy_objects(objects, prefix) | Deep-copy objects and collections/collection instances
deep_copy_materials(objects, prefix, prefer_existing) | Deep-copy materials
deep_copy_material_nodegroups_from_objects(objects, prefix, prefer_existing) | Deep-copy material Nodegroups, given a list of Objects
deep_copy_material_nodegroups(deep_copy_material_nodegroups(materials, prefix, prefer_existing) | Deep-copy material Nodegroups, given a list of Materials

To perform a complete deep copy, including Objects, Object data, Materials, and Material Node Groups, do:
```python
from .lib import blender_deepcopy_lib

# An iterable of objects, such as the selected_objects collection...
objects_to_copy = bpy.context.selected_objects
# A prefix to prepend to any new copies
prefix = "copy_of"
# Whether to use existing materials and nodegroups if they already exist in the file
use_existing = True

# Perform the copies.
obj_copies = blender_deepcopy_lib.deep_copy_objects(objects_to_copy, prefix)
material_copies = blender_deepcopy_lib.deep_copy_materials(obj_copies, prefix, prefer_existing)
blender_deepcopy_lib.deep_copy_material_nodegroups(material_copies, prefix, prefer_existing)
```

## Testing

Tests don't exist yet, but there will probably be some.

To run unit tests, run (from the Blender install directory):

```shell
blender --factory-startup --background --python path/to/module/run_tests.py
```
