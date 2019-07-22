import sys
import struct
import json
import os
from lmt import Lmt

def aob_hexstr(type):
    return struct.pack('%dB' % len(type), *type).hex()
    
def hexstr_aob(hex):
    aob = bytes.fromhex(hex)
    return list(struct.unpack('%dB' % len(aob), aob))

def pycstruct_to_jsondict(cstruct):
    ret_dict = {}
    for field in cstruct.fields:
        ret_dict[field]  = cstruct.__getattribute__(field)
        try: json.dumps(ret_dict[field])
        except: ret_dict[field] = pycstruct_to_jsondict(ret_dict[field])
    return ret_dict

def events_to_json(event_list):
    events_dict = { "unkn": event_list.unkn } 
    events = []
    for event in event_list.events:
        event_dict = {"type":aob_hexstr(event.type)}
        parameters = []
        for parameter in event.parameters:
            parameters += [{
                "type":aob_hexstr(parameter.type),
                "buffer":[aob_hexstr(b.values) for b in parameter.buffer]
            }]
        event_dict["parameters"] = parameters
        events += [event_dict]
    events_dict["events"] = events
    return events_dict

def json_to_events(events_dict):
    event_list = Lmt.Events(unkn = events_dict["unkn"], events_offset = 0, event_count = 0)
    event_list.events = []
    for event_dict in events_dict["events"]:
        event = Lmt.Events.EventParameter(type=hexstr_aob(event_dict["type"]), offset = 0, count = 0)
        event.parameters =  []
        for parameter_dict in event_dict["parameters"]:
            parameter = Lmt.Events.EventParameter(type=hexstr_aob(parameter_dict["type"]), offset = 0, count = 0)
            parameter.buffer = [Lmt.Events.Data(values=hexstr_aob(b)) for b in parameter_dict["buffer"]]
            event.parameters += [parameter]
        event_list.events += [event]
    return event_list

def block_to_json(anim_block, id):
    block_dict = pycstruct_to_jsondict(anim_block)
    block_dict.pop("bone_paths_offset")
    block_dict.pop("bone_path_count")
    block_dict.pop("events_offset")

    bone_paths = []
    for path in anim_block.bone_paths:
        path_dict = pycstruct_to_jsondict(path)
        path_dict.pop("buffer_offset")
        path_dict.pop("buffer_size")
        path_dict.pop("bounds_offset")
        if path.bounds:
            path_dict["bounds"] = pycstruct_to_jsondict(path.bounds)
        if path.buffer:
            path_dict["buffer"] = aob_hexstr(path.buffer)
        bone_paths += [path_dict]
    block_dict["bone_paths"] = bone_paths
    block_dict["events"] = events_to_json(anim_block.events)
    final_tuple = (id, block_dict)
    return json.dumps(final_tuple, indent=True)

def json_to_block(json_str):
    (id, block_dict) = json.loads(json_str)
    events_dict = block_dict.pop("events")
    bone_path_dicts = block_dict.pop("bone_paths")
    block = Lmt.AnimationBlock(bone_paths_offset = 0, bone_path_count = 0, events_offset = 0, **block_dict)

    block.bone_paths = []
    for bone_path_dict in bone_path_dicts:
        bounds = None
        buffer = b''
        if "bounds" in bone_path_dict: bounds = Lmt.BonePath.Bounds(**bone_path_dict.pop("bounds"))
        if "buffer" in bone_path_dict: buffer = bytes.fromhex(bone_path_dict.pop("buffer"))
        bone_path = Lmt.BonePath(buffer_size = 0, buffer_offset = 0, bounds_offset = 0, **bone_path_dict)
        bone_path.bounds = bounds
        bone_path.buffer = buffer
        block.bone_paths += [bone_path]
    
    block.events = json_to_events(events_dict)
    return (block, id)
    
def export_animation(path, lmt, i):
    output_path = "%s.%03d.json" % (path, i)
    print(f"exporting {output_path}")
    animation = lmt.get_animation(i)
    if not animation:
        return
    output_file = open(output_path, 'w')
    output_file.write(block_to_json(animation, i))

def export_animations(path):
    lmt_file = open(path, 'rb')
    lmt = Lmt.LMT(lmt_file)
    for i in range(lmt.entry_count):
        export_animation(path, lmt, i)

def override_animation(lmt_path, json_path):
    lmt_file = open(lmt_path, 'rb')
    lmt = Lmt.LMT(lmt_file)

    input_file = open(json_path, 'r')
    animation, id = json_to_block(input_file.read())
    animation.unkn[11] = 1
    lmt.override_animation(id, animation)

    lmt_file = open(lmt_path, 'wb')
    lmt_file.write(lmt.serialize())


if __name__ == "__main__":
    if len(sys.argv) == 2:
        export_animations(sys.argv[1])
    elif len(sys.argv) == 3 and sys.argv[2].isdigit():
        lmt = open(sys.argv[1], 'rb')
        lmt = Lmt.LMT(lmt)
        export_animation(sys.argv[1], lmt, int(sys.argv[2]))
    elif len(sys.argv) >= 3:
        lmts = [p for p in sys.argv[1:] if os.path.splitext(p)[1] == '.lmt']
        jsons = [p for p in sys.argv[1:] if os.path.splitext(p)[1] == '.json']
        for lmt in lmts:
            for jsn in jsons:
                override_animation(lmt, jsn)
        
