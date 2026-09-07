import os.path
import subprocess
import platform
import sys
from datetime import datetime

from string import Template

from importlib import resources

from . import rsisutil


def generate_latex(comps, opts: rsisutil.RapidOptions):
    latex_command = "tectonic"
    logospath = os.path.normpath(
        os.path.join(resources.files("rapidsis"), "logos")
    )
    templ_file = resources.files("rapidsis")

    if opts.file_type == "plain" or len(comps.comp_list) < 2:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        templ_file = os.path.join(
            templ_file,
            "templates",
            "single_comp_report.tmpl",
        )
    else:
        timestamp = comps.comp_list[0].trace.stats.starttime.ctime()
        templ_file = os.path.join(
            templ_file, "templates", "report.tmpl"
        )

    if platform.system() == "Windows":
        opts.record_name = opts.record_name.replace("\\", "/")
        opts.record_dir = opts.record_dir.replace("\\", "/")
        logospath = logospath.replace("\\", "/")

    texTemplateVariables = {
        "RecordName": opts.record_name,
        "Timestamp": timestamp,
        "OutputDir": opts.record_dir,
        "LogosDir": logospath,
        "Duration": comps.duration_trimmed,
        "FilterType": comps.filter_type,
    }
    if len(comps.comp_list) > 1:
        texTemplateVariables.update(
            {
                "PGARotD50": comps.pga_rotd50,
                "PGARotD100": comps.pga_rotd100,
                "PGVRotD50": comps.pgv_rotd50,
                "PGVRotD100": comps.pgv_rotd100,
                "PGDRotD50": comps.pga_rotd50,
                "PGDRotD100": comps.pga_rotd100,
            }
        )
    for i in range(6):
        texTemplateVariables.update({f"Comp{i}": ""})

    for i, comp in enumerate(comps.comp_list):
        texTemplateVariables.update(
            {
                f"Comp{i}": f"{comp.name} & {round(comp.pga, 3)} & {round(comp.pgv, 3)} & {round(comp.pgd, 3)} & {round(comp.sa_dot2s, 2)} & {round(comp.sa_1s, 2)} \\\\ \\hline"
            }
        )
    with open(templ_file, "r") as f:
        src = Template(f.read())
        result = src.substitute(texTemplateVariables)
        latex_fname = opts.record_name + ".tex"
        pdf_fname = opts.record_name + ".pdf"
        latex_fpath = os.path.join(opts.latex_final_dir, latex_fname)
        pdf_fpath = os.path.join(opts.latex_final_dir, pdf_fname)
        written_template = open(latex_fpath, "w")
        written_template.write(result)
        written_template.close()

        latexpdf_proc = subprocess.run(
            [
                latex_command,
                "-X",
                "compile",
                latex_fpath,
                "--outdir",
                opts.latex_final_dir,
            ],
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        for line in latexpdf_proc.stdout.split("\n"):
            sys.stderr.write(f"PDFCOMP: {line}\n")

        sys.stdout.write("Done generating LaTeX report.")
        if opts.open_pdf:
            if platform.system() == "Darwin":
                subprocess.call(("open", pdf_fpath))
            elif platform.system() == "Windows":
                os.startfile(pdf_fpath)
            else:
                subprocess.call(("xdg-open", pdf_fpath))
