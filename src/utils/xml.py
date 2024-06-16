import os
import json
import xmltodict


def xml_to_json(input_path, force_if_exists=False):
    
    if not input_path.endswith(".xml"):
        raise TypeError("Input file must be an XML.")

    path_js = input_path.replace(".xml", ".json")

    if force_if_exists or not os.path.exists(path_js):
        with open(input_path) as xml_file:
            data_dict = xmltodict.parse(xml_file.read())

        with open(path_js, "w") as json_file:
            json.dump(data_dict, json_file)
            
    return path_js
