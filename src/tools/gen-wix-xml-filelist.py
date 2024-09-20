import os
import sys
import uuid

source_dir = sys.argv[1]
template_file = sys.argv[2]
target_file = sys.argv[3]

existing_components = {
    'gam.exe': '''      <Component Id="gam_exe" Guid="d046ea24-c9f8-40ca-84db-70b0119933ff">
        <File Name="gam.exe" KeyPath="yes" />
        <Environment Id="PATH" Name="PATH" Value="[INSTALLFOLDER]" Permanent="yes" Part="last" Action="set" System="yes" />
      </Component>
''',
    'LICENSE': '''      <Component Id="license" Guid="c76864c5-d005-44d5-bb7c-a27e5923792d">
        <File Name="LICENSE" KeyPath="yes" />
      </Component>
''',
    'gam-setup.bat': '''      <Component Id="gam_setup_bat" Guid="5e6bbacb-d86f-4d80-a10b-89b81ee63fcb">
        <File Name="gam-setup.bat" KeyPath="yes" />
      </Component>
''',
    'GamCommands.txt': '''      <Component Id="GamCommands_txt" Guid="a2dca862-b222-469e-a637-95ea2a1c53e7">
        <File Name="GamCommands.txt" KeyPath="yes" />
      </Component>
''',
    'GamUpdate.txt': '''      <Component Id="GamUpdate_txt" Guid="1b7cdd48-0fff-4943-a219-102fcd14c755">
        <File Name="GamUpdate.txt" KeyPath="yes" />
      </Component>
''',
    'cacerts.pem': '''      <Component Id="cacerts_pem" Guid="61fe2b2d-1646-4bed-b844-193965e97727">
        <File Name="cacerts.pem" KeyPath="yes" />
      </Component>
''',
}

component_xml = ''
all_files = []
for root, dirs, files in os.walk(source_dir):
    for filename in files:
        relpath = os.path.relpath(root, source_dir)
        if relpath == '.':
            all_files.append(filename)
        else:
            all_files.append(os.path.join(relpath, filename))
all_files.sort()
for filename in all_files:
    component_xml += existing_components.get(filename,
                                             f'      <Component>\n        <File Name="{filename}" KeyPath="yes"/>\n      </Component>\n')

with open(template_file, 'r') as f:
    template = f.read()

full_xml = template.replace('REPLACE_ME_WITH_FILE_COMPONENTS', component_xml)

with open(target_file, 'w') as f:
    f.write(full_xml)

