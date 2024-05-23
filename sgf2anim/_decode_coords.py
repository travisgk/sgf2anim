# returns a list of tuples, with each tuple
# containing two board points.
def decode_lines(parameters):
    lines = []
    for parameter in parameters:
        start_coords = parameter[:2]
        end_coords = parameter[3:]
        points = decode_letter_coords([start_coords, end_coords])
        if len(points) == 2:
            lines.append(tuple(points))
    return lines


# returns a list of board points
# and an corresponding list of strings.
def decode_labels(parameters):
    points = []
    strings = []
    for parameter in parameters:
        results = decode_letter_coords([parameter[:2]])
        if len(results) == 0:
            continue
        points.append(results[0])
        strings.append(parameter[3:])
    return points, strings


# returns a list of board points.
def decode_letter_coords(parameters):
    points = []
    for parameter in parameters:
        if len(parameter) != 2:
            continue
        x = _letter_to_number(parameter[0])
        y = _letter_to_number(parameter[1])
        if x is not None and y is not None:
            points.append((x, y))
    return points


# returns an integer if <letter> is valid,
# otherwise None will be returned.
def _letter_to_number(letter):
    if "a" <= letter <= "z":
        return ord(letter) - ord("a")
    if "A" <= letter <= "Z":
        return 26 + ord(letter) - ord("A")
    return None
