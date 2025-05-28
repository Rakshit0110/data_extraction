import math
import json

# Calculate Euclidean distance
def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# Calculate direction from point A to B
def calculate_direction(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0:
        if dy > 0:
            return "Down"
        elif dy < 0:
            return "Up"
        else:
            return "No movement"
    angle = math.degrees(math.atan2(dy, dx))
    if -45 <= angle < 45:
        return "Right"
    elif 45 <= angle < 135:
        return "Down"
    elif -135 <= angle < -45:
        return "Up"
    else:
        return "Left"

# Determine vertical approach
def determine_approach(y_coordinate):
    return "Top" if y_coordinate < 2000 else "Down"

# Inject regex based on field name
def add_regex_field(base_name):
    base = base_name.upper()
    if "TVA" in base:
        return "^.{11}"
    elif "BIC" in base or "SWIFT" in base:
        return "^.{8}"
    return None

# Main JSON processor
def process_json(json_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    results = {}

    # Handle key-value fields
    for key in data:
        if key.endswith("KEY"):
            base_name = key.replace(" KEY", "").replace("KEY", "").strip()
            val_key = key.replace("KEY", "VAL").strip()

            if val_key in data:
                k = data[key][0]
                v = data[val_key][0]

                results[base_name] = {
                    "key": k.get("key"),
                    "Distance": round(calculate_distance(k["x"], k["y"], v["x"], v["y"]), 2),
                    "Direction": calculate_direction(k["x"], k["y"], v["x"], v["y"]),
                    "Approach": determine_approach(k["y"]),
                    "Size": "single line"
                }

                # Add regex if required
                regex = add_regex_field(base_name)
                if regex:
                    results[base_name]["regex"] = regex

    # Handle standalone fields like addresses and names
    for label in data:
        upper_label = label.upper()
        if any(x in upper_label for x in ["ADDRESS", "NAME"]):
            y = data[label][0]["y"]
            label_name = label.strip()

            results[label_name] = {
                "Approach": determine_approach(y),
                "Size": "multi line" if "ADDRESS" in upper_label else "single line"
            }

    # Save results
    with open("output_results.json", "w") as f:
        json.dump(results, f, indent=4)

    print("Results have been written to output_results.json")

# Entrypoint
def main():
    json_file_path = "convert.json"  # Replace with actual path if needed
    try:
        process_json(json_file_path)
    except FileNotFoundError:
        print("File not found.")
    except json.JSONDecodeError:
        print("Invalid JSON file.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
