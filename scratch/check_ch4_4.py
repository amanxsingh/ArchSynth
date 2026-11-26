
import zipfile
from lxml import etree
docx = r'd:\Web Dev\archy\Aman_Singh_ArchSynth_Third_Semester_Report_Revised_Final.docx'
z = zipfile.ZipFile(docx)
doc = etree.fromstring(z.read('word/document.xml'))
body = doc.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')
for i in range(370, 377):
    txt = ''.join(body[i].itertext()).strip()
    print(f'{i}: {txt}')
