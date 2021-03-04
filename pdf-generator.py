#!/usr/bin/python

# -n name: file name
# -i: add index
# -f: add front page

import sys
import yaml
import os.path
from fpdf import FPDF, HTMLMixin
import re
import datetime

usage = """\
Usage: python3 pdf-generator.py [OPTION]... <FILE>
Generate a PDF report from FILE.

Options:
    -n <NAME>   Generated PDF file name will be <NAME>.pdf
    -i          Generated PDF will have content index
    -f          Generated PDF will have front page
"""

if "--help" in sys.argv:
    print(usage)
    quit(0)

dst_file = ""
src_file = ""
add_frontpage = False
add_index = False

argv = sys.argv[1:]

while argv:
    arg = argv.pop(0)
    if re.match(r"^-[nif]{1,3}$", arg):
        if "i" in arg: add_index = True
        if "f" in arg: add_frontpage = True
        if "n" in arg:
            if not argv or argv[0].startswith("-"):
                print("Missing argument for option -n")
                quit(1)
            dst_file = argv.pop(0)
    elif argv:
        print(f"Invalid argument: {arg}")
        quit(1)
    else: src_file = arg

if src_file == "":
    print("Missing argument <FILE>")
    quit(1)

if not os.path.isfile(src_file):
    print(f"File <{src_file}> does not exist")
    quit(1)

data = yaml.load(open(src_file), Loader=yaml.FullLoader)

if data is None:
    print(f"File <{src_file}> is not YAML format")
    quit(1)

if "metadata" not in data: 
    print(f"Missing data in <{src_file}>: No metadata")
    quit(1)
if "sections" not in data: 
    print(f"Missing data in <{src_file}>: No sections")
    quit(1)

class PDF(FPDF):

    def __init__(self, metadata):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.metadata = metadata
        self.l_margin = self.r_margin = 30
        self.t_margin = self.b_margin = 25
        self.epw = self.w - self.l_margin - self.r_margin
        self.eph = self.h - self.t_margin - self.b_margin
        self.file_name = (dst_file if dst_file != "" else data["metadata"]["title"]) + ".pdf"
        self.date = datetime.datetime.now().strftime(self.metadata["date-format"] if "date-format" in metadata else "%d-%m-%Y")
    
    def header(self):
        self.set_y(self.t_margin/2)
        self.set_font('Arial', 'I', 10)
        self.set_text_color(100, 100, 100)
        self.cell(self.get_string_width(self.metadata["title"]), 0, self.metadata["title"], 0, 0, 'L')
        self.set_x(self.w - self.r_margin - self.get_string_width(self.date))
        self.cell(self.get_string_width(self.date), 0, self.date, 0, 0, 'R')
        self.set_y(self.t_margin)

    def footer(self):
        self.set_y(self.h - (self.b_margin/2))
        self.set_font('Arial', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(20, 0, str(self.page_no()), 0, 0, 'L')

    def save(self):
        self.output(self.file_name, 'F')

    def add_header(self, text, level=1):
        self.set_font('Arial', 'B', 18 - (2 * level))
        self.set_text_color(47, 84, 150)
        self.multi_cell(self.epw, 10, text, 0, 'L')

    def add_paragraph(self, text, alignment = 'L'):
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(self.epw, 5, text, 0, alignment)

    def add_front_page(self):
        self.add_page()
        self.set_fill_color(255, 175, 0)
        self.rect(33, 27, 6, 195, 'F')
        self.set_xy(54.7, 76.8)
        self.set_font('Arial', '', 30)
        self.multi_cell(125, 15, self.metadata["title"], 0, 'L')

def fill_section(pdf: PDF, section, level):
    if level == 1: pdf.add_page()
    if "header" in section:
        pdf.add_header(section["header"], level)
        section["page"] = pdf.page_no()
    if "text" in section and section["text"]:
        for text in section["text"]: pdf.add_paragraph(text)
        pdf.ln()
    if "sections" in section: fill_sections(pdf, section["sections"], level + 1)

def fill_sections(pdf: PDF, sections, level):
    for section in sections: fill_section(pdf, section, level)

pdf = PDF(data["metadata"])

if add_frontpage: pdf.add_front_page()
fill_sections(pdf, data["sections"], 1)

pdf.save()