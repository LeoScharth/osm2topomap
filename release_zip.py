import os, shutil
# from zipfile import ZipFile 
# thx: https://thispointer.com/python-how-to-create-a-zip-archive-from-multiple-files-or-directory/ 

from pathlib import Path

"""

    RELEASE SYSTEM FOR THE PLUGIN

    you just need to include in the list "exclude_patternslist" the patterns that should not be included in the release 

    it will export the zip file to a folder named "sidewalkreator_release" to the homefolder

"""



exclude_patternslist = ['.git','.github','__pycache__','notes','i18n','release','*.pyc','temporary','plugin_upload.py','trash','paper_publication','extra_tests','model3_xml_files','sample_data']


# print(filelist)

this_file_path = os.path.realpath(__file__)
plugin_path = os.path.dirname(this_file_path)



# destfolderpath = str(Path.home()/'sidewalkreator_release'/'osm_sidewalkreator'/'osm_sidewalkreator')

release_folderpath = 'release'

outpath = os.path.join(release_folderpath,'osm2topomap.zip')


temp_files_path = 'release/temp_files'
destfolderpath = 'release/temp_files/osm2topomap'

if os.path.exists(release_folderpath):
    shutil.rmtree(release_folderpath)


#thx: https://stackoverflow.com/a/42488524/4436950
shutil.copytree(plugin_path,destfolderpath,ignore=shutil.ignore_patterns(*exclude_patternslist))

if os.path.exists(outpath):
    os.remove(outpath)



shutil.make_archive(outpath.replace('.zip',''),'zip',temp_files_path)


if os.path.exists(temp_files_path):
    shutil.rmtree(temp_files_path)

print(outpath)
print(release_folderpath)
print(destfolderpath)


