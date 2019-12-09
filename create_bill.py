import string
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template("cam_surplus_template.html")

input_file = '/home/sangram/code/git/bill_sending/data/sample_cam.csv'
inf = open(input_file, 'r')

for line in inf:
    line = line.rstrip('\n')
    parts = string.split(line, '|')
    building = parts[0]
    flat = parts[1]
    flat_number = building[0] + '-' + flat
    file_name = 'cam_' + building[0] + '_' + flat + '.pdf'
    owner_name = string.capwords(parts[2])
    print file_name, flat_number, owner_name, parts[3:]

    template_vars = {
        'flat_number_title': flat_number,
        'flat_number': flat_number,
        'owner_name': owner_name,
        'carpet_area': parts[3],
        'possession_date': parts[4],
        'cam_start_date': parts[5],
        'cam_charges': parts[6],
        'fcam_allocation': parts[7],
        'housekeeping': parts[8],
        'security': parts[9],
        'mep_admin': parts[10],
        'electricity': parts[11],
        'water': parts[12],
        'mgmt_overhead': parts[13],
        'r_m_amc': parts[14],
        'bcam_provision': parts[15],
        'cam_expenses': parts[16],
        'cam_surplus': parts[17]
    }

    html_out = template.render(template_vars)
    HTML(string=html_out).write_pdf('pdf_out/' + file_name)

inf.close()
