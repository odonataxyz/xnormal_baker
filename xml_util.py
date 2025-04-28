from xml.etree.ElementTree import Element, SubElement

def set_xml(element:Element, name:str, data):
    if isinstance(data, bool) :
        element.set(name, str(data).lower())
    elif data.__class__.__name__ == 'bpy_prop_array' :
        element.set(name,';'.join([str(d) for d in data]))
    elif isinstance(data, str) :
        element.set(name, data)
    else :
        element.set(name, str(data))


def set_xml_color(element:Element, name:str, data:tuple[float, float, float]):
    color_element = SubElement(element, name)
    color_element.set('R', str(int(data[0] * 255)))
    color_element.set('G', str(int(data[1] * 255)))
    color_element.set('B', str(int(data[2] * 255)))