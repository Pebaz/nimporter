import typetraits, json, tables, nimpy

proc return_bool(): bool {.exportpy.} =
    return true


proc return_int(): int {.exportpy.} =
    return 1

    
proc return_float(): float {.exportpy.} =
    return 3.14
            
            
proc return_str(): string {.exportpy.} =
    return "Hello World!"


proc return_list(): seq[int] {.exportpy.} =
    return @[1, 2, 3]


proc return_dict(): Table[string, int] {.exportpy.} =
    return {
        "Pebaz" : 25,
        "Protodip" : 28,
        "Yelbu": 23
    }.toTable




proc receive_bool(val: bool): bool {.exportpy.} =
    return val.type.name == "bool" and val == true


proc receive_int(val: int): bool {.exportpy.} =
    return val.type.name == "int" and val == 1


proc receive_float(val: float): bool {.exportpy.} =
    return val.type.name == "float" and val == 3.14
            
            
proc receive_str(val: string): bool {.exportpy.} =
    return val.type.name == "string" and val == "Hello World!"


proc receive_list(val: seq[int]): bool {.exportpy.} =
    return val.type.name == "seq[int]" and val == @[1, 2, 3]


proc receive_dict(val: JsonNode): bool {.exportpy.} =
    var res = val["Name"].getStr() == "Pebaz"
    res = res and val["Age"].getInt() == 25
    res = res and val["Alive"].getBool() == false
    res = res and val["Height"].getFloat() > 5
    res = res and val["Height"].getFloat() < 7
    return val.type.name == "JsonNode" and res
