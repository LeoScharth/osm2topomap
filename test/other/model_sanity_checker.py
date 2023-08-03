import os,re, json

models_path = 'model3_xml_files'

outpath = 'test/sanity_check.json'
outpath_filtered = 'test/sanity_check_filtered.json'


def find_between_strings(text, start_string, end_string):
    pattern = re.compile(f"{re.escape(start_string)}(.*?){re.escape(end_string)}")
    match = pattern.search(text)
    if match:
        return match.group(1)
    

def dump_dict_to_json(data, file_path):
    with open(file_path, 'w+', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

occurrences = {}

base_to_find =  'component_description'


for filename in os.listdir(models_path):
    filepath = os.path.join(models_path,filename)

    occurrences[filename] = {}

    with open(filepath) as reader:
        for line in reader:
            if base_to_find in line:
                interest_string = find_between_strings(line,'value="','" name="')

                if interest_string:
                    if not interest_string in occurrences[filename]:
                        occurrences[filename][interest_string] = 1
                    else:
                        occurrences[filename][interest_string] += 1

filtered = {}
# keeping only bigger than 1:
for key in occurrences:
    filtered[key] = {}
    for keyword in occurrences[key]:
        if occurrences[key][keyword] > 1:
            filtered[key][keyword] = occurrences[key][keyword]

dump_dict_to_json(occurrences,outpath)
dump_dict_to_json(filtered,outpath_filtered)

                    
