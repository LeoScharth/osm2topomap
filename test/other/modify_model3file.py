

orig_model_path = 'model3_xml_files/model_1_grupos_transformadores_p.model3'
new_model_path = 'model3_xml_files/model_1_test.model3'

to_replace = 'component_description'


with open(orig_model_path) as reader:
    with open(new_model_path,'w+') as writer:
        for i,line in enumerate(reader):
            if to_replace in line:
                line = line.replace(to_replace,f"item_{i}")

            writer.write(line)
