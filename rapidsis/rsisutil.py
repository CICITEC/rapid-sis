import os
import sys
import json
from . import comp_processing as cproc
from datetime import datetime
from pathlib import Path


# Aggregate of options
class RapidOptions:
    def __init__(self, timezone_offset="None"):
        self.sensor_sensitivity: float = 2
        self.threshold: float = 0.1
        self.threshold_padding: float = 5.0
        self.freq_min: float = 0.1
        self.freq_max: float = 25.0
        self.event_latitude: float = 0.0
        self.event_longitude: float = 0.0
        self.station_latitude: float = 0.0
        self.station_longitude: float = 0.0
        self.filter_type: str = "bandpass"
        self.spectra_method: str = "nigam-jennings"
        self.rotd: bool = False
        self.delta: float = 0.000
        self.timezone: int = -5
        self.plain_line_start: int = 2
        self.plain_col_num: str = "single"
        self.filename: str = ""
        self.file_type: str = ""
        self.record_name: str = ""
        self.output_dir: str = ""
        self.latex_final_dir: str = ""
        self.dump_dir: str = ""
        self.record_dir: str = ""
        self.open_pdf: bool = False
        self.skip_conversion: bool = False

        if timezone_offset == "None":
            tz = datetime.now().astimezone()
            timezone_offset = int(tz.utcoffset().total_seconds() / 3600)
            self.timezone = timezone_offset
        else:
            self.clamp_timezone(int(timezone_offset))

    def clamp_timezone(self, tz_utc: int):
        """Ensure that the timezone is within acceptable range."""
        _clamp_tz = lambda _tz: (
            -11 if _tz < -11 else (11 if _tz > 11 else _tz)
        )
        self.timezone = _clamp_tz(tz_utc)

    def validate_directory_and_create(self, dir, name):
        """Validate that the indicated folder exists"""
        if not os.path.isdir(dir):
            sys.stderr.write(
                f"Creating {name} directory at {dir} ...\n"
            )
            os.makedirs(dir)

    def pathname_generation(self, all_comps, latex_dir="latex"):
        """Build the full paths that will be used to output files."""
        if self.output_dir == "":
            self.output_dir = os.path.normpath(
                os.path.join(Path.home(), "rapidsis", "Records")
            )
        else:
            self.output_dir = os.path.normpath(
                os.path.join(self.output_dir, "Records")
            )

        if self.file_type == "mseed":
            self.record_dir = os.path.normpath(
                os.path.join(
                    self.output_dir,
                    all_comps.year,
                    all_comps.month,
                    self.record_name,
                )
            )
        elif self.file_type == "plain":
            self.record_dir = os.path.normpath(
                os.path.join(
                    self.output_dir,
                    all_comps.year,
                    all_comps.month,
                    self.record_name,
                )
            )
        else:
            sys.stderr.write(
                "Unable to create record directory, unkown file type..."
            )
            quit(1)

        self.validate_directory_and_create(self.output_dir, "Output")
        self.validate_directory_and_create(self.record_dir, "Records")

        self.latex_final_dir = os.path.normpath(
            os.path.join(self.record_dir, latex_dir)
        )
        self.validate_directory_and_create(
            self.latex_final_dir, "Latex"
        )

    def filter_name_normalization(self, filter_name: str):
        """The CLI and GUI have different ways of selecting a filter
        thus, we require this normalization of sorts"""
        filter_name = filter_name.lower()
        match filter_name:
            case "bp" | "butterworth-bandpass":
                self.filter_type = "bandpass"
            case "bs" | "butterworth-bandstop":
                self.filter_type = "bandstop"
            case "lp" | "butterworth-lowpass":
                self.filter_type = "lowpass"
            case "hp" | "butterworth-highpass":
                self.filter_type = "highpass"
            case "lpc2" | "lowpass-cheby-2":
                self.filter_type = "lowpass_cheby_2"
            case "None":
                self.filter_type = "bandpass"
                sys.stderr.write(
                    "No filter selected. Defaulting to Butterworth bandpass.\n"
                )
            case _:
                self.filter_type = "bandpass"
                sys.stderr.write(
                    "Unkown filter option. Defaulting to Butterworth bandpass.\n"
                )
        sys.stderr.write(f"{self.filter_type} filter selected.\n")

    def spectra_name_validation(self, spectra_method_name: str):
        """This function allows us to ensure the names are equal across gui
        and cli"""
        self.spectra_method = spectra_method_name.lower()
        # Override until a new method comes along.
        self.spectra_method = "nigam-jennings"
        match self.spectra_method:
            case "nigam-jennings":
                sys.stderr.write(
                    "Nigam-Jennings for spectral response generation.\n"
                )
            case _:
                self.spectra_method = "nigam-jennings"
                sys.stderr.write(
                    "Spectra method is incorrect, defaulting to Nigam-Jennings.\n"
                )

    def delta_validation(self, delta):
        """Returns false if the validation fails,
        this allows us to ensure the user puts the delta in plain text
        """
        self.delta = float(delta)
        if self.delta == 0 and self.file_type == "plain":
            sys.stderr.write(
                "Please set the delta if using plain text files."
            )
            return False
        return True

    def __repr__(self):
        return (
            f"Sensor sensitivity: {self.sensor_sensitivity}\n"
            f"Threshold: {self.threshold}\n"
            f"Threshold padding: {self.threshold_padding}\n"
            f"Frequency minimum: {self.freq_min}\n"
            f"Frequency maximum: {self.freq_max}\n"
            f"Event latitude: {self.event_latitude}\n"
            f"Event longitude: {self.event_longitude}\n"
            f"Station latitude: {self.station_latitude}\n"
            f"Station longitude: {self.station_longitude}\n"
            f"Filter type: {self.filter_type}\n"
            f"Spectra method: {self.spectra_method}\n"
            f"Calculate RotD: {self.rotd}\n"
            f"Delta: {self.delta}\n"
            f"Timezone: {self.timezone}\n"
            f"First line of data: {self.plain_line_start}\n"
            f"Number of columns: {self.plain_col_num}\n"
            f"Filename: {self.filename}\n"
            f"File type: {self.file_type}\n"
            f"Record name: {self.record_name}\n"
            f"Output directory: {self.output_dir}\n"
            f"Latex directory: {self.latex_final_dir}\n"
            f"Dump directory: {self.dump_dir}\n"
            f"Record directory: {self.record_dir}\n"
            f"Open PDF: {self.open_pdf}\n"
        )


class DumpBundle:
    def __init__(self, timezone_offset="None"):
        self.Z_comp = None
        self.E_comp = None
        self.N_comp = None
        self.Station = ""
        self.Timestamp = ""


def json_comp_data(comp: cproc.CompData):
    """Creates a dictionary for a component."""
    json_data = {
        "sensitivity": float(comp.sensitivity),
        "damp": float(comp.damp),
        "dt": float(comp.dt),
        "dt_hz": int(comp.dt_hz),
        "spectral_acceleration_at_dot2_seconds": float(comp.sa_dot2s),
        "spectral_acceleration_at_1_second": float(comp.sa_1s),
        "pga": float(comp.pga),
        "pga_signed": float(comp.pga_signed),
        "pga_time": float(comp.pga_t),
        "pgv": float(comp.pgv),
        "pgv_signed": float(comp.pgv_signed),
        "pgv_time": float(comp.pgv_t),
        "pgd": float(comp.pgd),
        "pgd_signed": float(comp.pgd_signed),
        "pgd_time": float(comp.pgd_t),
    }
    return json_data


def json_dump_generation(json_bundle, comps: cproc.CompBundle, opts):
    """Generates the dictionary that will be used to create the json file."""
    json_bundle.Timestamp = comps.comp_list[
        0
    ].original_trace.stats.starttime.ctime()
    json_bundle.Graph_start_time = comps.comp_list[
        0
    ].trace.stats.starttime.ctime()
    json_bundle.Graph_end_time = comps.end_time_with_offset.ctime()
    json_bundle.Duration = comps.duration
    json_dict = {
        f"Start time (UTC {opts.timezone})": json_bundle.Timestamp,
        f"Duration (s)": json_bundle.Duration,
        f"Plots start time (UTC {opts.timezone})": json_bundle.Graph_start_time,
        f"Plots end time (UTC {opts.timezone})": json_bundle.Graph_end_time,
        "Spectra method": comps.spectra_method,
        "Filter type": comps.filter_type,
        "pga_rotd50": comps.pga_rotd50,
        "pga_rotd100": comps.pga_rotd100,
        # "pgv_rotd50": comps.pgv_rotd50,
        # "pgv_rotd100": comps.pgv_rotd100,
        # "pgd_rotd50": comps.pgd_rotd50,
        # "pgd_rotd100": comps.pgd_rotd100,
    }
    for x in comps.comp_list:
        json_bundle_x_comp = json_comp_data(x)
        json_dict.update({f"{x.name}": json_bundle_x_comp})

    return json_dict


def json_write_dump(AllComps: cproc.CompBundle, opts):
    json_bundle = DumpBundle()
    json_data = json_dump_generation(json_bundle, AllComps, opts)
    json_path = os.path.normpath(
        os.path.join(opts.record_dir, opts.record_name + "_data.json")
    )
    sys.stderr.write(f"Dumping to path: {json_path}")
    with open(json_path, "w") as file:
        json.dump(json_data, file, indent=2)
