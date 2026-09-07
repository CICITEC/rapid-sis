import numpy as np
import sys
import os
from obspy import read, read_inventory
from obspy import core as obspy_core
from obspy import UTCDateTime
from pathlib import Path
import calendar
import pandas as pd

import multiprocessing as mp

from . import sr


def generate_text_dump(opts, all_comps):
    """Dump filtered and unfiltered traces to text files in the Record directory"""
    for comp in all_comps.comp_list:
        _simply_dump2(
            opts.record_dir,
            opts.record_name,
            comp,
            filter=False,
        )
        _simply_dump2(
            opts.record_dir,
            opts.record_name,
            comp,
            filter=True,
        )


def _simply_dump2(record_dir, record_name, comp_x, filter):
    """Simply dumps the trace (array?) line by line
    """
    if not os.path.exists(record_dir):
        sys.stderr.write(
            "Attempted to dump trace data and record directory does not exist...Why?"
        )
        quit()
    dump_name = os.path.normpath(
        os.path.join(
            record_dir,
            record_name + "_" + comp_x.trace.stats.channel,
        )
    )
    if filter:
        dump_name = os.path.normpath(
            os.path.join(dump_name + "_filtered")
        )
        np.savetxt(dump_name + ".txt", comp_x.trace.data, fmt="%.15f")
    else:
        np.savetxt(
            dump_name + ".txt", comp_x.baseline_trace.data, fmt="%.15f"
        )


class CompData:
    def __init__(self, tr, name, sensor_sensitivity, delta=None):
        # Component name
        self.name: str = name
        # Damping factor: defaults to 0.05
        self.damp: float = 0.05
        # Delta
        self.dt: float = 0.0
        # Sampling rate
        self.dt_hz: int = 0
        # Live trace used throughout the code
        self.trace: obspy_core.Trace = tr.copy()
        # Unmodified trace (raw data)
        self.original_trace: obspy_core.Trace = tr
        # Trace converted from raw values to acceleration
        self.converted_trace: obspy_core.Trace = None
        # Baseline correction with detrending trace
        self.baseline_trace: obspy_core.Trace = None
        # Unfiltered trace
        self.unfiltered_trace: obspy_core.Trace = None
        # Filtered trace
        self.filtered_trace: obspy_core.Trace = None
        # Sensor sensitivity
        self.sensitivity: int = sensor_sensitivity
        # Acceleration data, this is trace.data
        self.acc_data: np.ndarray = 0
        # Velocity data, this is trace.data integrated once
        self.vel_data: np.ndarray = 0
        # Displacement data, this is trace.data integrated twice
        self.disp_data: np.ndarray = 0
        # Period values used for spectras
        self.periods: np.ndarray = None
        # Freq values used for spectras
        self.freqs: np.ndarray = None
        # Acceleration spectra data
        self.acc_spectra: np.ndarray = None
        # spectral acceleration @ .2s
        self.sa_dot2s: float = 0.
        # spectral acceleration @ 1s
        self.sa_1s: float = 0.
        # Velocity spectra data
        self.vel_spectra = None
        # Displacement spectra data
        self.disp_spectra = None
        # Peak ground acceleration
        self.pga: float = 0
        # Peak ground velocity
        self.pgv: float = 0
        # peak ground displacement
        self.pgd: float = 0
        # signed peak ground acceleration
        self.pga_signed: float = 0.
        # Peak ground velocity
        self.pgv_signed: float = 0.
        # peak ground displacement
        self.pgd_signed: float = 0.
        # Peak ground acceleration index in the corrected signal
        self.pga_idx = 0
        # Peak ground velocity index in the corrected signal
        self.pgv_idx = 0
        # peak ground displacement index in the corrected signal
        self.pgd_idx = 0
        # Peak ground acceleration time in seconds
        self.pga_t: float = 0.
        # Peak ground velocity time in seconds
        self.pgv_t: float = 0.
        # peak ground displacement time in seconds
        self.pgd_t: float = 0.
        # UTC complete date time (adjusted for timezone)
        self.date_time = None

        if delta is None:
            self.dt = round(tr.stats.delta, 3)
            self.dt_hz = tr.stats.sampling_rate
        else:
            self.dt = round(delta, 3)
            self.dt_hz = int(1.0 / self.dt)

    def find_SA_values_index(self, comp_bundle):
        """Function to find the spectral acceleration values at .2s and 1s."""
        if comp_bundle.sa_dot2s_idx == 0:
            self.sa_dot2s = find_SA_value_at_period(
                comp_bundle, 0.2, self
            )
        else:
            sys.stderr.write(
                f"Found SA value at 2s for comp {self.trace.stats.channel[-1]} cached\n"
            )
            self.sa_dot2s = self.acc_spectra[comp_bundle.sa_dot2s_idx]
        # NOTE: calculate at 1s
        if comp_bundle.sa_1s_idx == 0:
            self.sa_1s = find_SA_value_at_period(comp_bundle, 1, self)
        else:
            sys.stderr.write(
                f"Found SA value at 1s for comp {self.trace.stats.channel[-1]} cached\n"
            )
            self.sa_1s = self.acc_spectra[comp_bundle.sa_1s_idx]



# We need this to sort the components in the list, since when they
# return from their thread, one might finish earlier than others
def _sort_comps(c: CompData):
    return c.trace.stats.channel


class CompBundle:
    def __init__(
            self,
            path,
            sensor_sensitivity=2,
            lat=0.0,
            lon=0.0,
            station_lat=0.0,
            station_lon=0.0,
            filter="bandpass",
            spectra_method="nigam-jennings",
    ):
        # Components
        self.comp_list: list[CompData] = []
        # Event latitude and longitude
        self.latitude = lat
        self.longitude = lon
        # Station latitude and longitude
        self.station_latitude = station_lat
        self.station_longitude = station_lon
        # Name of the filter used
        self.filter_type: str = filter
        # Spectra method
        self.spectra_method: str = spectra_method
        # Date information
        self.year = ""
        self.month = ""

        # Trimming and threshold
        # These are the offset values in second
        # These will be added to the start time of the event so we can trim
        # n amount of seconds before the threshold
        self.offset_head = None
        self.offset_tail = None
        self.offset_size = None
        # These are the start and end times of the event,
        # with the offset added to the original time
        # Needed for trimming
        self.start_time_with_offset: UTCDateTime = None
        self.end_time_with_offset: UTCDateTime = None
        # These are the indexes of where the threshold values are found
        self.start_time_idx: int = 0
        self.end_time_idx: int = 0
        # Padding in seconds
        self.head_padding: int = 0
        self.tail_padding: int = 0
        # Duration of the untrimmed event in seconds
        self.duration = 0.0
        # Duration of the processed signal
        self.duration_trimmed = 0.0

        # Spectral values
        # This is where in the array of data points the
        # spectral acceleration value at .2 seconds and 1 seconds
        # are located, respectively.
        # (Used for caching)
        self.sa_dot2s_idx = 0
        self.sa_1s_idx = 0

        # RotD
        self.pga_rotd50: float = 0.0
        self.pga_rotd100: float = 0.0
        self.pgv_rotd50: float = 0.0
        self.pgv_rotd100: float = 0.0
        self.pgd_rotd50: float = 0.0
        self.pgd_rotd100: float = 0.0

        # RotD data points
        self.acc_rotd100 = None
        self.acc_rotd50 = None
        self.vel_rotd100 = None
        self.vel_rotd50 = None
        self.disp_rotd100 = None
        self.disp_rotd50 = None


def find_SA_value_at_period(comps: CompBundle, t, comp_x: CompData):
    """Function to find the spectral acceleration values at a specific period."""
    # Make an array where we subtract the amount of time
    abs_arr = np.abs(comp_x.periods - t)
    # The index of the 0 since it's an all positive array thanks to abs
    # is where we will find our spectra value
    idx = abs_arr.argmin()
    if t == 0.2:
        comps.sa_dot2s_idx = idx
    elif t == 1:
        comps.sa_1s_idx = idx
    sys.stderr.write(
        f"Index is {idx} for {comp_x.periods[idx]} with value {comp_x.acc_spectra[idx]}")

    return comp_x.acc_spectra[idx]

def comp_corrections(
        opts,
        comp_bundle: CompBundle,
        comp_x: CompData,
        threshold=0.1,
):
    # Use factor to convert to acceleration
    if not opts.skip_conversion:
        # baseline correction
        if comp_x.trace.stats._format == "MSEED":
            sys.stderr.write("Performing baseline correction\n")
            # quit()
            comp_x.trace.data = comp_x.trace.data * (
                    1 / (comp_x.sensitivity / 0.00098066)
            )
        else:
            sys.stderr.write("Skipping baseline correction...\n")
            sys.stderr.write(f"Format is {comp_x.trace.stats._format}\n")
    # after converting acceleration values, they are not quite
    # at the baseline yet, detrending fixes this
    comp_x.converted_trace = comp_x.trace.copy()
    comp_x.trace.detrend("linear")
    comp_x.trace.detrend("demean")
    comp_x.baseline_trace = comp_x.trace.copy()

    # lol
    comp_x.unfiltered_trace = comp_x.trace.copy()

    match opts.filter_type:
        case "bandpass" | "bandstop":
            comp_x.trace.filter(
                opts.filter_type,
                freqmin=opts.freq_min,
                freqmax=opts.freq_max,
                corners=4,
            )
        case "lowpass" | "highpass" | "lowpass_cheby_2":
            comp_x.trace.filter(
                opts.filter_type, freq=opts.freq_max, corners=4
            )
        case _:
            # Use default filter
            comp_x.trace.filter(
                opts.filter_type,
                freqmin=opts.freq_min,
                freqmax=opts.freq_max,
                corners=4,
            )

    comp_x.filtered_trace = comp_x.trace.copy()

    trace_data_len = len(comp_x.trace.data)
    absolute_trace_data = np.abs(
        comp_x.trace.data
    )
    # loop until we find the first value that is bigger than the threshhold
    try:
        thresh_head_idx = next(
            i for i, v in enumerate(absolute_trace_data) if v > threshold
        )
    # if we couldn't find it we keep everything on the left side
    except StopIteration:
        thresh_head_idx = 0
    thresh_head_time = round(thresh_head_idx * comp_x.dt, 0)

    sys.stderr.write(
        f"Value {absolute_trace_data[thresh_head_idx]} ({comp_x.trace.data[thresh_head_idx]}) approximates the {threshold} threshold value.\n"
    )
    sys.stderr.write(
        f"The relative time is {thresh_head_time} with index {thresh_head_idx}\n")

    # This is to add an extra n amount of seconds (padding)
    # to the value found that fits the threshold
    if thresh_head_time > opts.threshold_padding:
        offset_head_t = thresh_head_time - opts.threshold_padding
        comp_bundle.head_padding = opts.threshold_padding
    else:
        offset_head_t = 0
        comp_bundle.head_padding = 0

    duration_t = comp_x.trace.stats.npts * comp_x.trace.stats.delta
    comp_bundle.duration = duration_t
    sys.stderr.write(f"Duration: {comp_bundle.duration}\n")

    # Doing the same for the tail now
    thresh_tail_idx = 0
    for i in reversed(range(0, len(absolute_trace_data))):
        if absolute_trace_data[i] > threshold:
            thresh_tail_idx = i
            sys.stderr.write(f"Tail idx: {thresh_tail_idx}\n")
            break

    thresh_tail_time = round(thresh_tail_idx * comp_x.dt, 0)

    sys.stderr.write(
        f"Value {absolute_trace_data[thresh_tail_idx]} ({comp_x.trace.data[thresh_tail_idx]}) approximates the {threshold} threshold value.\n"
    )
    sys.stderr.write(
        f"The relative time is {thresh_tail_time} with index {thresh_tail_idx}\n")

    # This is to add an extra 5 second window to the threshold value found
    # this ensures there's actually enough time for the padding to fit in
    if (duration_t - thresh_tail_time) > opts.threshold_padding:
        offset_tail_t = thresh_tail_time + opts.threshold_padding
        comp_bundle.tail_padding = opts.threshold_padding
    else:
        offset_tail_t = duration_t
        comp_bundle.tail_padding = 0

    # Offset head/tail are the points/timestamps new starting
    # and end point respectively.
    if (
            comp_bundle.offset_head is None
            and comp_bundle.offset_tail is None
    ):
        comp_bundle.offset_head = offset_head_t
        comp_bundle.offset_tail = offset_tail_t

    # Add indexes to comp_bundle
    comp_bundle.start_time_idx = thresh_head_idx
    comp_bundle.end_time_idx = thresh_tail_idx


    offset_size_t = offset_tail_t - offset_head_t
    if offset_head_t < comp_bundle.offset_head:
        comp_bundle.offset_head = offset_head_t

    if offset_tail_t > comp_bundle.offset_tail:
        comp_bundle.offset_tail = offset_tail_t

    comp_bundle.offset_size = (
            comp_bundle.offset_tail - comp_bundle.offset_head
    )

    sys.stderr.write(f"Offset head: {offset_head_t}\n")
    sys.stderr.write(f"Offset tail: {offset_tail_t}\n")
    sys.stderr.write(f"Offset_size_t: {offset_size_t}\n")
    sys.stderr.write(
        f"Offset size: {comp_bundle.offset_size}\n"
    )


def trim_traces(comp_bundle: CompBundle, comp_x):
    comp_bundle.start_time_with_offset = (
            comp_x.trace.stats.starttime + comp_bundle.offset_head
    )
    comp_bundle.end_time_with_offset = (
            comp_x.trace.stats.starttime + comp_bundle.offset_tail
    )

    comp_x.trace = comp_x.trace.slice(
        comp_bundle.start_time_with_offset, comp_bundle.end_time_with_offset
    )


def sp_time_histories_and_spectral(
        comp_x: CompData,
        spectra_method="nigam-jennings",
):
    """Second half of the signal processing,
    Here we perform integration to obtain velocity and displacement from
    the acceleration values and generate the spectral responses"""

    # This is the ObsPy way of creating copies of traces
    comp_tr = comp_x.trace.copy()

    # PGA
    comp_x.pga_signed = max(
        comp_tr.data.min(), comp_tr.data.max(), key=abs
    )
    comp_x.pga = abs(comp_x.pga_signed)
    comp_x.pga_idx = np.abs(comp_tr.data).argmax()
    # Convert the index to seconds
    comp_x.pga_t = comp_x.pga_idx * comp_x.dt
    comp_x.acc_data = comp_x.trace.data

    # Velocity
    comp_tr.integrate()
    comp_x.pgv_signed = max(
        comp_tr.data.min(), comp_tr.data.max(), key=abs
    )
    comp_x.pgv = abs(comp_x.pgv_signed)
    comp_x.pgv_idx = np.abs(comp_tr.data).argmax()
    comp_x.pgv_t = comp_x.pgv_idx * comp_x.dt
    comp_x.vel_data = comp_tr.data

    # Displacement
    comp_tr.integrate()
    comp_x.pgd_signed = max(
        comp_tr.data.min(), comp_tr.data.max(), key=abs
    )
    comp_x.pgd = abs(comp_x.pgd_signed)
    comp_x.pgd_idx = np.abs(comp_tr.data).argmax()
    comp_x.pgd_t = comp_x.pgd_idx * comp_x.dt
    comp_x.disp_data = comp_tr.data

    # Periods for the spectras (4s)
    comp_x.periods = np.arange(0.01, 4, 0.01)
    comp_x.freqs = 1 /comp_x.periods

    comp_x.acc_spectra = np.zeros(len(comp_x.periods))
    comp_x.vel_spectra = np.zeros(len(comp_x.periods))
    comp_x.disp_spectra = np.zeros(len(comp_x.periods))

    match spectra_method:
        case "nigam-jennings":
            (
                comp_x.disp_spectra,
                comp_x.vel_spectra,
                comp_x.acc_spectra,
            ) = sr.rs_func_nigam_jennings(
                comp_x.trace.data,
                comp_x.dt,
                comp_x.periods,
                comp_x.damp,
            )
    return comp_x


def rotd(
        x: np.ndarray | np.ma.MaskedArray,
        y: np.ndarray | np.ma.MaskedArray,
        max_angle=180,
):
    """RotD50 and RotD100 for 0-180"""
    if x.shape != y.shape:
        sys.stderr.write(
            "Unable to calculated RotD, x and y have different shapes"
        )
    # Creates an array of angles from 0 to max_angle (180 at most)
    # all evenly spaced
    angles = np.linspace(0.0, np.pi, num=max_angle, endpoint=False)
    peaks = np.empty_like(angles)
    periods = np.arange(0.01, 4, 0.01)

    T = periods
    damp_factor = 0.05
    delta = 0.005

    w = 2 * np.pi / T
    rotd100 = np.empty_like(T)
    rotd50 = np.empty_like(T)
    for i in np.arange(len(T)):
        DW = damp_factor * w[i]
        D2 = damp_factor ** 2
        A0 = np.exp(-DW * delta)
        A1 = w[i] * np.sqrt(1 - D2)
        AD1 = A1 * delta
        A2 = np.sin(AD1)
        A3 = np.cos(AD1)
        W2 = w[i] ** 2
        A4 = (2 * D2 - 1) / W2
        A5 = damp_factor / w[i]
        A6 = 2 * A5 / W2
        A7 = 1 / W2
        A8 = (A1 * A3 - DW * A2) * A0
        A9 = -(A1 * A2 + DW * A3) * A0
        A10 = A8 / A1
        A11 = A0 / A1
        A12 = A11 * A2
        A13 = A0 * A3
        A14 = A10 * A4
        A15 = A12 * A4
        A16 = A6 * A13
        A17 = A9 * A6

        # computing A and B
        a11 = A0 * (DW * A2 / A1 + A3)
        a12 = A12
        a21 = A10 * DW + A9
        a22 = A10

        b11 = (-A15 - A16 + A6) / delta - A12 * A5 - A7 * A13
        b12 = (A15 + A16 - A6) / delta + A7
        b21 = (-A14 - A17 - A7) / delta - A10 * A5 - A9 * A7
        b22 = (A14 + A17 + A7) / delta
        ########################################################

        # responses u, up and upp (absolute acceleration)
        data = x
        npts = len(x)
        u = np.zeros(npts)
        up = np.zeros(npts)
        upp = np.zeros(npts)
        for j in range(1, npts):
            u[j] = (
                    a11 * u[j - 1]
                    + a12 * up[j - 1]
                    + b11 * data[j - 1]
                    + b12 * data[j]
            )
            up[j] = (
                    a21 * u[j - 1]
                    + a22 * up[j - 1]
                    + b21 * data[j - 1]
                    + b22 * data[j]
            )
            upp[j] = -2 * damp_factor * w[i] * up[j] - w[i] ** 2 * u[j]

        data2 = y
        npts = len(y)
        uy = np.zeros(npts)
        upy = np.zeros(npts)
        uppy = np.zeros(npts)
        for j in range(1, npts):
            uy[j] = (
                    a11 * uy[j - 1]
                    + a12 * upy[j - 1]
                    + b11 * data2[j - 1]
                    + b12 * data2[j]
            )
            upy[j] = (
                    a21 * uy[j - 1]
                    + a22 * upy[j - 1]
                    + b21 * data2[j - 1]
                    + b22 * data2[j]
            )
            uppy[j] = (
                    -2 * damp_factor * w[i] * upy[j] - w[i] ** 2 * uy[j]
            )

        for j, a in enumerate(angles):
            rot = upp * np.cos(a) + uppy * np.sin(a)
            peaks[j] = np.max(np.abs(rot))

        rotd50[i] = np.percentile(peaks, 50)
        rotd100[i] = np.percentile(peaks, 100)

    return np.percentile(peaks, 50), np.max(peaks), rotd100, rotd50


def seed_to_comp_bundle(opts):
    """This function starts by reading the miniSEED file,
    it uses opts (look at RapidOptions on the rsisutil.py file) to know
    how to process the event"""

    # The timestamps we use are of type UTCDateTime,
    # so whatever timestamp we get
    # we need to adjust for our current timezone,
    # so we obtain the user timezone (a number between -11 and 11)
    # convert that to the amount of seconds we add to the
    # UTC timestamp
    tz = 3600 * opts.timezone

    comps = CompBundle(
        opts.filename,
        sensor_sensitivity=opts.sensor_sensitivity,
        lat=opts.event_latitude,
        lon=opts.event_longitude,
        station_lat=opts.station_latitude,
        station_lon=opts.station_longitude,
        filter=opts.filter_type,
        spectra_method=opts.spectra_method,
    )

    if opts.file_type == "mseed":
        # This is here because we want to have independent objects that
        # we can modify in each thread, then join to generate graphs
        st = read(opts.filename)

        # The reason we use this list and individual comps is because
        # we want to keep the locking stuff to a minimum
        # if we had the comp_x_temp variables inside the comps
        # the code would have to lock wayyyy more than it has to right now
        # so we try to stay using individual components separated from one big large object
        # as long as we can
        _comp_list = []
        # unwrap each trace and read
        for x in st:
            # Add trace of each component
            comp_x_temp = CompData(
                x.copy(), x.stats.channel, opts.sensor_sensitivity
            )
            _comp_list.append(comp_x_temp)
            sys.stderr.write(f"{comp_x_temp.name} found \n")
            sys.stderr.write(f"{comp_x_temp.trace.stats}\n")

            sys.stderr.write(f"{opts.sensor_sensitivity}\n")

        for comp in _comp_list:
            comp_corrections(
                opts=opts,
                comp_bundle=comps,
                comp_x=comp,
                threshold=opts.threshold,
            )

        for comp in _comp_list:
            trim_traces(comps, comp)

        # This section starts multithreading
        # Star map needs parameters to be in this form
        comp_args_time_hist_func = []
        for comp in _comp_list:
            comp_args_time_hist_func.append(
                (
                    comp,
                    opts.spectra_method,
                )
            )
        with mp.Pool(processes=3) as pool:
            star_comp_res = pool.starmap(sp_time_histories_and_spectral, comp_args_time_hist_func)

        for proc_comp in star_comp_res:
            comps.comp_list.append(proc_comp)

        # sort alphabetically
        comps.comp_list.sort(key=_sort_comps)

        # calculate rotd
        if len(comps.comp_list) > 1 and opts.rotd:
            sys.stderr.write("Calculating RotD50 and RotD100\n")
            # FIXME: Add to compo_processing
            (
                comps.pga_rotd50,
                comps.pga_rotd100,
                comps.acc_rotd100,
                comps.acc_rotd50,
            ) = rotd(
                comps.comp_list[0].acc_data,
                comps.comp_list[1].acc_data,
                180,
            )

        # We do this so the labels under the figures are using
        # the users timezone, and not UTC
        comps.start_time_with_offset = comps.start_time_with_offset + tz
        comps.end_time_with_offset = comps.end_time_with_offset + tz
        for comp in comps.comp_list:
            comp.find_SA_values_index(comps)
            comp.trace.stats.starttime = comps.start_time_with_offset
            comp.date_time = comps.start_time_with_offset

        comps.year = str(comps.comp_list[0].date_time.year)
        month_n = comps.comp_list[0].date_time.month
        comps.month = calendar.month_name[month_n]
        comps.filename = opts.filename
        comps.record = Path(opts.filename).stem

    elif opts.file_type == "plain":
        sys.stderr.write(f"{opts.filter_type} filter selected.\n")
        if opts.plain_line_start < 1:
            opts.plain_line_start = 1
        row_idx_corr = np.abs(opts.plain_line_start) - 1

        if opts.plain_col_num == "single":
            signal_df = pd.read_table(
                opts.filename,
                skiprows=row_idx_corr,
                header=None,
                sep="\s+",
                index_col=False,
                names=["value"],
            )
        elif opts.plain_col_num == "double":
            signal_df = pd.read_table(
                opts.filename,
                skiprows=row_idx_corr,
                header=None,
                sep="\s+",
                index_col=False,
                names=["time", "value"],
            )
            if signal_df["value"].isna().any():
                sys.stderr.write("Warning: NaN values in value column.")
        else:
            sys.stderr.write("Invalid column count.\n")
            exit(1)

        sys.stderr.write(f"Dataframe of signal:\n {signal_df}\n")
        signal_data = signal_df["value"].to_numpy()

        # calculate the delta, this is assuming
        # that the first column is time
        calc_delta = abs(signal_df.iloc[0, 0] - signal_df.iloc[1, 0])
        sys.stderr.write(f"Calculated delta is: {calc_delta}\n")
        if (opts.delta != calc_delta):
            sys.stderr.write(f"Delta chosen by the user ({opts.delta}) differs from calculated delta ({calc_delta})\n")
            opts.delta = calc_delta

        tr = obspy_core.Trace()
        tr.data = signal_data
        tr.stats.delta = opts.delta
        tr.stats.sampling_rate = 1 / opts.delta
        tr.stats.starttime = UTCDateTime()
        sys.stderr.write(f"{tr.stats}\n")
        single_comp = CompData(tr, "Single", opts.sensor_sensitivity)
        single_comp.trace.stats._format = "Plain"

        # We do not want to modify the event data itself,
        # this is just basically saying, WHEN we processed the event,
        # not when the event ocurred
        _date = UTCDateTime()
        comps.year = str(_date.year)
        month_n = _date.month
        comps.month = calendar.month_name[month_n]

        comp_corrections(
            opts=opts,
            comp_bundle=comps,
            comp_x=single_comp,
            threshold=opts.threshold,
        )

        trim_traces(comps, single_comp)

        single_comp = sp_time_histories_and_spectral(
            single_comp,
            opts.freq_min,
            opts.freq_max,
            opts.filter_type,
            opts.spectra_method,
        )
        comps.comp_list.append(single_comp)
        comps.start_time_with_offset = comps.start_time_with_offset + tz
        comps.end_time_with_offset = comps.end_time_with_offset + tz

    comps.duration_trimmed = float(
        comps.end_time_with_offset - comps.start_time_with_offset
    )
    return comps
