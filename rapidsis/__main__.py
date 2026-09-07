import sys
import os
import argparse
from pathlib import Path

from . import gui as mgui
from . import comp_processing as cproc
from . import fig_gen as fg
from . import latex_gen as lg
from . import rsisutil

from obspy.core import UTCDateTime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no_gui",
        action="store_false",
        help="Don't initialize the gui",
    )
    parser.add_argument(
        "--ftype",
        default="mseed",
        help="The file type we wish to process. Options are 'plain' and 'seed'.",
    )
    parser.add_argument(
        "--line_start",
        default=2,
        help="Which line to save the component data from.",
    )
    parser.add_argument(
        "--column_n",
        default="Single",
        help="How many columns in the text file. Options are 'single' or 'Double'.",
    )
    parser.add_argument(
        "--delta",
        default=0.000,
        help="Delta in seconds. Used for plain text processing. "
             "If no value is provided, it will be extracted from the miniSEED.",
    )
    parser.add_argument(
        "--filename", help="The path to the file we will process."
    )
    parser.add_argument(
        "--timezone",
        default="None",
        help="The timezone of the event. Defaults to the users timezone.",
    )
    parser.add_argument(
        "--lat", default=0, help="The latitude of the event."
    )
    parser.add_argument(
        "--lon", default=0, help="The longitude of the event."
    )
    parser.add_argument(
        "--s_lat",
        default=0,
        help="The latitude of the station. Only necessary if it is not a known station.",
    )
    parser.add_argument(
        "--s_lon",
        default=0,
        help="The longitude of the longitude. Only necessary if it is not a known station.",
    )
    parser.add_argument(
        "--sens",
        default=2,
        help="Sensor sensitivity, the default value for a TITAN SMA acelerograph is 2.",
    )
    parser.add_argument(
        "--threshold",
        default=0.1,
        help="The minimum value of acceleration we want to reach before starting the treatment of our signal. Default value is 0.1 cm/s^2.",
    )
    parser.add_argument(
        "--tpad",
        default=5,
        help="The seconds added to the threshold of the signal. Default value is 5 seconds.",
    )
    parser.add_argument(
        "--filter",
        default="None",
        help="The type of filter used. Butterworth options are: bp (bandpass), bs (bandstop), lp (lowpass), hp (highpass). Cheby 2 options: lpc2 (lowpass_cheby_2). Defaults to bandpass. In the case of a lp or hp filter, the minimum frequency will be ignored, and the maximum frequency will be used as the corner frequency.",
    )
    parser.add_argument(
        "--corners",
        default=4,
        help="The default corner amount for the filter. Default value is 4.",
    )
    parser.add_argument(
        "--freq_min",
        default=0.1,
        help="The minimum frequency to use for the filter. Default value is 0.1 Hz.",
    )
    parser.add_argument(
        "--freq_max",
        default=25.0,
        help="The maximum frequency to use for the filter. Default value is 25 Hz. If the type is lowpass, highpass or lowpass_cheby_2, --freq_min will be ignored.",
    )
    parser.add_argument(
        "--spectra_method",
        default="nigam-jennings",
        help="Response spectra method to use. Options: nigam-jennings.",
    )
    parser.add_argument(
        "--rotd",
        action="store_true",
        help="Calculate RotD50 and RotD100.",
    )
    parser.add_argument(
        "--output_dir",
        default=os.path.normpath(os.path.join(Path.home(), "rapidsis")),
        help="Directory where the images and other related files will be output to. Defaults to ~/rapidsis",
    )
    parser.add_argument(
        "--latex_dir",
        default="latex",
        help="Directory where the latex files will live. This will be created inside of the output directory.",
    )
    parser.add_argument("--open_pdf", action="store_true",
                        help="Open the pdf file after processing.")
    parser.add_argument("--skip_conversion", action="store_true",
                        help="Skip conversion to cm/s^2 of the input data. Useful if you know the values are already in cm/s^2.")

    args = parser.parse_args()

    # Start gui if no argument
    if args.no_gui is not False:
        mgui.rapid_sis_gui()
        exit(0)

    if args.filename is None:
        sys.stderr.write("Can't have empty filename...")
        sys.stderr.write("Please run --help")
        quit()

    # Init all options
    opts = rsisutil.RapidOptions(args.timezone)
    opts.filename = args.filename
    opts.record_name = Path(opts.filename).stem
    opts.file_type = args.ftype
    opts.plain_line_start = args.line_start
    opts.plain_col_num = args.column_n.lower()

    opts.output_dir = args.output_dir

    opts.event_latitude = float(args.lat)
    opts.event_longitude = float(args.lon)

    opts.station_latitude = float(args.s_lat)
    opts.station_longitude = float(args.s_lon)

    opts.filter_name_normalization(args.filter)
    opts.spectra_name_validation(args.spectra_method)
    opts.rotd = args.rotd

    opts.threshold = float(args.threshold)
    opts.threshold_padding = float(args.tpad)

    opts.sensor_sensitivity = float(args.sens)

    opts.freq_min = float(args.freq_min)
    opts.freq_max = float(args.freq_max)
    opts.open_pdf = args.open_pdf

    if not opts.delta_validation(args.delta):
        return

    print(opts)

    # NOTE: Processing is here
    comps_bundle = cproc.seed_to_comp_bundle(opts)
    opts.pathname_generation(comps_bundle, args.latex_dir)

    cproc.generate_text_dump(opts, comps_bundle)

    sys.stderr.write("Generating event description...\n")
    rsisutil.json_write_dump(comps_bundle, opts)
    sys.stderr.write("Generating figures...\n")
    fg.generate_figures(comp_bundle=comps_bundle, opts=opts)

    sys.stderr.write("Generating LaTeX...\n")
    lg.generate_latex(comps_bundle, opts)


if __name__ == "__main__":
    main()
