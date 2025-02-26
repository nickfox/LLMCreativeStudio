print("Testing @c mapping:")
let mention = "c"
switch mention.lowercased() {
case "a", "claude":
    print("Maps to claude")
case "c": 
    print("Maps to claude")
case "chatgpt":
    print("Maps to chatgpt")
default:
    print("Unknown mapping")
}
