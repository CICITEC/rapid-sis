import tkinter as tk
import platform
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
import tkinter.scrolledtext as scrolledtext
from importlib import resources
import sys
import threading
import queue

from pathlib import Path

from . import comp_processing as cproc
from . import fig_gen as fg
from . import latex_gen as lg
from . import rsisutil


class stdio_wrapper(object):
    def __init__(self, widget, q, tag):
        self.widget = widget
        self.q = q
        self.tag = tag

    def write(self, msg):
        # Send the message to the queue
        self.widget.configure(state="normal")
        self.widget.insert(tk.END, msg, (self.tag))
        self.widget.see(tk.END)

    def flush(self):
        pass


class processing_gui(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("RAPID-SIS")
        self.resizable(False, False)
        self.grid_columnconfigure(1, minsize=200, weight=0)

        self.fname_tk_str = tk.StringVar()
        self.output_dir_tk_str = tk.StringVar()

        # Select file type
        self.file_type_name_ui = tk.Label(
            self, text="Select the file type."
        )
        self.file_type_name_ui.grid(
            row=0, column=1, columnspan=1, sticky="WE"
        )
        self.file_type_entry = tk.Entry(self)
        file_opt = [
            "MSEED",
            "Txt file",
        ]
        self.file_type_name_selection = ttk.Combobox(
            self, values=file_opt
        )
        self.file_type_name_selection.bind(
            "<<ComboboxSelected>>", self.update_ui_file_type
        )
        self.file_type_name_selection.current(0)
        self.file_type_name_selection.grid(
            row=1,
            column=1,
            columnspan=1,
        )

        # Line start
        self.line_start_name_ui = tk.Label(self, text="First line:")
        self.line_start_name_ui.grid(
            row=2, column=1, columnspan=1, sticky="WE"
        )
        self.line_start_entry_ui = tk.Entry(self)
        self.line_start_entry_ui.grid(
            row=3,
            column=1,
            columnspan=1,
        )
        self.line_start_entry_ui.grid_remove()
        self.line_start_name_ui.grid_remove()

        # Select file type
        self.column_selection_name_ui = tk.Label(
            self, text="Select how to parse the data:"
        )
        self.column_selection_name_ui.grid(
            row=4, column=1, columnspan=1, sticky="WE"
        )
        self.column_selection_entry = tk.Entry(self)
        parse_opt = [
            "Acceleration (cm/s^2) - One Column",
            "Time (s) & Acceleration (cm/s^2)- Two columns",
        ]
        self.column_selection_name_selection = ttk.Combobox(
            self, values=parse_opt
        )
        self.column_selection_name_selection.current(0)
        self.column_selection_name_selection.grid(
            row=5,
            column=1,
            columnspan=1,
        )
        self.column_selection_name_ui.grid_remove()
        self.column_selection_name_selection.grid_remove()

        # Delta
        self.delta_name_ui = tk.Label(self, text="Delta in seconds")
        self.delta_name_ui.grid(
            row=6, column=1, columnspan=1, sticky="WE"
        )
        self.delta_entry_ui = tk.Entry(self)
        self.delta_entry_ui.grid(
            row=7,
            column=1,
            columnspan=1,
        )
        self.delta_entry_ui.grid_remove()
        self.delta_name_ui.grid_remove()

        self.coord_ex_l1 = tk.Label(
            self, text="Latitude and Longitude in decimal degrees."
        )
        self.coord_ex_l1.grid(
            row=2, column=1, columnspan=1, sticky="WE"
        )
        self.coord_ex_l2 = tk.Label(
            self, text="Example: Lat 51.477928, Lon -0.001545"
        )
        self.coord_ex_l2.grid(
            row=3, column=1, columnspan=1, sticky="WE"
        )

        # Get event lat
        self.lat_name_ui = tk.Label(self, text="Lat of event")
        self.lat_name_ui.grid(
            row=4, column=1, columnspan=1, sticky="WE"
        )
        self.lat_entry_ui = tk.Entry(self)
        self.lat_entry_ui.grid(
            row=5,
            column=1,
            columnspan=1,
        )
        # Get event lon
        self.lon_name_ui = tk.Label(self, text="Lon of event")
        self.lon_name_ui.grid(
            row=6, column=1, columnspan=1, sticky="WE"
        )
        self.lon_entry_ui = tk.Entry(self)
        self.lon_entry_ui.grid(
            row=7,
            column=1,
            columnspan=1,
        )
        # Get station lat
        self.station_lat_name_ui = tk.Label(self, text="Lat of station")
        self.station_lat_name_ui.grid(
            row=8, column=1, columnspan=1, sticky="WE"
        )
        self.station_lat_entry_ui = tk.Entry(self)
        self.station_lat_entry_ui.grid(
            row=9,
            column=1,
            columnspan=1,
        )
        # Get station lon
        self.station_lon_name_ui = tk.Label(self, text="Lon of station")
        self.station_lon_name_ui.grid(
            row=10, column=1, columnspan=1, sticky="WE"
        )
        self.station_lon_entry_ui = tk.Entry(self)
        self.station_lon_entry_ui.grid(
            row=11,
            column=1,
            columnspan=1,
        )
        # Get sensor sensitivity
        self.sensitivity_name_ui = tk.Label(
            self, text="Sensor sensitivity (usually 2)"
        )
        self.sensitivity_name_ui.grid(
            row=12, column=1, columnspan=1, sticky="WE"
        )
        self.sensitivity_entry_ui = tk.Entry(self)
        self.sensitivity_entry_ui.grid(
            row=13,
            column=1,
            columnspan=1,
        )
        # Get threshold
        self.thresh_name_ui = tk.Label(
            self, text="Acceleration threshold (cm/s^2) (0.1 cm/s^2)"
        )
        self.thresh_name_ui.grid(
            row=14, column=1, columnspan=1, sticky="WE"
        )
        self.thresh_entry_ui = tk.Entry(self)
        self.thresh_entry_ui.grid(
            row=15,
            column=1,
            columnspan=1,
        )
        # Get threshold padding
        self.thresh_pad_name_ui = tk.Label(
            self, text="Threshold padding (s) (5s)"
        )
        self.thresh_pad_name_ui.grid(
            row=16, column=1, columnspan=1, sticky="WE"
        )
        self.thresh_pad_entry_ui = tk.Entry(self)
        self.thresh_pad_entry_ui.grid(
            row=17,
            column=1,
            columnspan=1,
        )
        # Select filter type
        self.filter_type_name_ui = tk.Label(
            self, text="Select the filter type."
        )
        self.filter_type_name_ui.grid(
            row=18, column=1, columnspan=1, sticky="WE"
        )
        self.freq_max_entry_ui = tk.Entry(self)
        filter_opt = [
            "Butterworth-bandpass",
            "Butterworth-bandstop",
            "Butterworth-lowpass",
            "Butterworth-highpass",
            "Lowpass-Cheby-2",
        ]
        self.filter_type_name_selection = ttk.Combobox(
            self, values=filter_opt
        )
        self.filter_type_name_selection.bind(
            "<<ComboboxSelected>>", self.update_ui_combobox_changes
        )
        self.filter_type_name_selection.current(0)
        self.filter_type_name_selection.grid(
            row=19,
            column=1,
            columnspan=1,
        )
        # Get freq min
        self.freq_min_name_ui = tk.Label(
            self, text="Minimum frequency for filter (0.1 Hz)"
        )
        self.freq_min_name_ui.grid(
            row=20, column=1, columnspan=1, sticky="WE"
        )
        self.freq_min_entry_ui = tk.Entry(self)
        self.freq_min_entry_ui.grid(
            row=21,
            column=1,
            columnspan=1,
        )
        # Get freq max
        self.freq_max_name_ui = tk.Label(
            self, text="Maximum frequency for filter (25 Hz)"
        )
        self.freq_max_name_ui.grid(
            row=22, column=1, columnspan=1, sticky="WE"
        )
        self.freq_max_entry_ui = tk.Entry(self)
        self.freq_max_entry_ui.grid(
            row=23,
            column=1,
            columnspan=1,
        )

        # Select filter type
        self.spectra_method_name = tk.Label(
            self, text="Select the spectral response algorithm."
        )
        self.spectra_method_name.grid(
            row=24, column=1, columnspan=1, sticky="WE"
        )
        self.spectra_method_ui = tk.Entry(self)
        spectra_algo_opts = [
            "Nigam-Jennings",
        ]
        self.spectra_method_selection = ttk.Combobox(
            self, values=spectra_algo_opts
        )
        self.spectra_method_selection.current(0)
        self.spectra_method_selection.grid(
            row=25,
            column=1,
            columnspan=1,
        )

        self.rotd_checkbox_val = tk.BooleanVar(self)
        self.rotd_checkbox_ui = tk.Checkbutton(
            self,
            text="Calculate RotD50 and RotD100",
            variable=self.rotd_checkbox_val,
        )
        self.rotd_checkbox_ui.grid(row=26, column=1, columnspan=1)

        # Select timezone
        self.timezone_name_ui = tk.Label(
            self, text="UTC timezone (-11 to 11)"
        )
        self.timezone_name_ui.grid(
            row=27, column=1, columnspan=1, sticky="WE"
        )
        self.timezone_entry_ui = tk.Entry(self)
        self.timezone_entry_ui.grid(
            row=28,
            column=1,
            columnspan=1,
        )

        self.process = tk.Button(
            self, text="Process!", command=self.get_vals
        )
        self.process.grid(row=31, column=1)

        ###### Leftside
        # Filename button
        self.open_button = ttk.Button(
            self, text="Open a File", command=self.select_file
        )
        self.filename_text_ui = tk.Label(
            self, width=50, text="Please choose a miniSEED file."
        )
        self.filename_text_ui.grid(
            row=0, column=0, columnspan=1, sticky="WE"
        )
        self.open_button.grid(
            row=1, column=0, columnspan=1, sticky="WE"
        )

        # Directory selection
        self.dir_button = ttk.Button(
            self, text="Choose a Directory", command=self.select_dir
        )
        self.dir_button.grid(row=3, column=0, columnspan=1, sticky="WE")
        self.dir_path_name_ui = tk.Label(
            self,
            width=2,
            text="Please choose where to save output data.",
        )
        self.dir_path_name_ui.grid(
            row=2, column=0, columnspan=1, sticky="WE"
        )

        # Textbox
        self.cmd_output_title_ui = tk.Label(self, text="Status log")
        self.cmd_output_title_ui.grid(row=4, column=0, sticky="WE")
        self.cmd_output_box = scrolledtext.ScrolledText(self, height=25)
        self.cmd_output_box.grid(
            row=6, column=0, rowspan=20, sticky="WE"
        )

        self.msg_q = queue.Queue()
        self.cmd_output_box.tag_config(
            "err", foreground="white", background="black"
        )
        sys.stdout = stdio_wrapper(
            self.cmd_output_box, self.msg_q, "stdout"
        )
        sys.stderr = stdio_wrapper(
            self.cmd_output_box, self.msg_q, "stderr"
        )
        s = ttk.Style()
        s.configure("TProgressbar", thickness=5)
        self.progvar = tk.IntVar()
        self.seed_progress_bar = ttk.Progressbar(
            self, style="TProgressbar", variable=self.progvar
        )
        self.seed_progress_bar.grid(row=5, column=0, sticky="WE")

    def seed_processing(
        self,
        opts,
    ):
        if opts.delta == 0 and opts.file_type == "plain":
            self.cmd_output_box.insert(
                tk.END, "\nError processing...\n", "err"
            )
            self.cmd_output_box.insert(
                tk.END, "\nPlease provide a delta value...\n", "err"
            )
            return

        self.seed_progress_bar.step(10)
        # Component processing
        try:
            comps_bundle = cproc.seed_to_comp_bundle(opts)
            self.progvar.set(10)
        except Exception as _:
            self.progvar.set(0)
            self.cmd_output_box.insert(
                tk.END, "\nError processing...\n", "err"
            )
        opts.pathname_generation(comps_bundle, "latex")
        cproc.generate_text_dump(opts, comps_bundle)
        self.update_idletasks()
        if opts.file_type == "mseed":
            try:
                # Figure generation
                self.progvar.set(60)
                fg.generate_figures(comp_bundle=comps_bundle, opts=opts)
            except Exception as _:
                self.progvar.set(0)
                self.cmd_output_box.insert(
                    tk.END, "\nError generating figures...\n", "err"
                )
            rsisutil.json_write_dump(comps_bundle, opts)

        self.cmd_output_box.insert(
            tk.END, "\nGenerating PDF from LaTeX...\n", "err"
        )
        self.update_idletasks()
        try:
            # Latex generation
            self.progvar.set(80)
            lg.generate_latex(comps_bundle, opts)
            self.cmd_output_box.insert(
                tk.END, "\nOpening PDF...\n", "err"
            )
            self.progvar.set(100)
        except Exception as _:
            self.progvar.set(0)
            self.cmd_output_box.insert(
                tk.END,
                "\nError generating LaTeX, check terminal...\n",
                "err",
            )

    def get_vals(self):
        self.progvar.set(0)
        gui_opts = rsisutil.RapidOptions()
        gui_opts.skip_conversion = False
        gui_opts.open_pdf = True
        thresh = self.thresh_entry_ui.get()
        if thresh == "":
            thresh = 0.1
        gui_opts.threshold = float(thresh)

        thresh_pad = self.thresh_pad_entry_ui.get()
        if thresh_pad == "":
            thresh_pad = 5
        gui_opts.threshold_padding = float(thresh_pad)

        freq_min = self.freq_min_entry_ui.get()
        if freq_min == "":
            freq_min = 0.1
        gui_opts.freq_min = float(freq_min)

        freq_max = self.freq_max_entry_ui.get()
        if freq_max == "":
            freq_max = 25.0
        gui_opts.freq_max = float(freq_max)

        spectra_method = self.spectra_method_selection.get()
        gui_opts.spectra_name_validation(spectra_method)

        rotd_b = self.rotd_checkbox_val.get()
        gui_opts.rotd = rotd_b

        lat = self.lat_entry_ui.get()
        if lat == "":
            lat = 0
        gui_opts.event_latitude = float(lat)

        lon = self.lon_entry_ui.get()
        if lon == "":
            lon = 0
        gui_opts.event_longitude = float(lon)

        station_lat = self.station_lat_entry_ui.get()
        if station_lat == "":
            station_lat = 0
        gui_opts.station_latitude = float(station_lat)

        station_lon = self.station_lon_entry_ui.get()
        if station_lon == "":
            station_lon = 0
        gui_opts.station_longitude = float(station_lon)

        sensitivity = self.sensitivity_entry_ui.get()
        if sensitivity == "":
            sensitivity = 2
        gui_opts.sensor_sensitivity = float(sensitivity)

        timezone = self.timezone_entry_ui.get()
        if timezone == "":
            timezone = -5
        gui_opts.clamp_timezone(int(timezone))

        gui_opts.filename = self.fname_tk_str.get()
        if gui_opts.filename == "":
            sys.stderr.write("No filename provided!\n")
            return
        gui_opts.record_name = Path(gui_opts.filename).stem
        gui_opts.output_dir = self.output_dir_tk_str.get()

        filter_name = self.filter_type_name_selection.get()
        gui_opts.filter_name_normalization(filter_name)

        file_type_tk = self.file_type_name_selection.get().lower()
        if file_type_tk == "txt file":
            file_type_tk = "plain"
        gui_opts.file_type = file_type_tk

        col_n_tk = self.column_selection_name_selection.get()
        match col_n_tk:
            case "Acceleration (cm/s^2) - One Column":
                col_n_tk = "single"
            case "Time (s) & Acceleration (cm/s^2)- Two columns":
                col_n_tk = "double"
        gui_opts.plain_col_num = col_n_tk

        delta_tk = self.delta_entry_ui.get()
        if delta_tk == "":
            delta_tk = 0.000
        if not gui_opts.delta_validation(float(delta_tk)):
            return
        line_start_tk = self.line_start_entry_ui.get()
        if line_start_tk == "":
            line_start_tk = 2
        gui_opts.plain_line_start = int(line_start_tk)
        self.cmd_output_box.insert(tk.END, "Processing...\n", "err")
        self.update_idletasks()

        try:
            threading.Thread(
                target=self.seed_processing,
                args=(gui_opts,),
                daemon=True,
            ).start()

        except Exception as _:
            self.cmd_output_box.insert(
                tk.END, "Error processing, check terminal...\n"
            )

        self.update_idletasks()

    def select_dir(self):
        dir_path = fd.askdirectory(initialdir="~")
        self.dir_path_name_ui.configure(text=dir_path)
        self.output_dir_tk_str.set(dir_path)

    def select_file(self):
        filetypes = (
            ("SEED/MiniSEED", "*.seed"),
            ("Plain text", "*.txt"),
            ("All files", "*.*"),
        )

        filename = fd.askopenfilename(
            title="Open a file",
            initialdir="~",
            filetypes=filetypes,
        )

        self.filename_text_ui.configure(text=filename)
        self.fname_tk_str.set(filename)

    def update_ui_file_type(self, ev):
        file_type_check_ui = self.file_type_name_selection.get()

        if file_type_check_ui == "Txt file":
            # Hide elements
            self.lat_name_ui.grid_remove()
            self.lat_entry_ui.grid_remove()
            self.lon_name_ui.grid_remove()
            self.lon_entry_ui.grid_remove()
            self.station_lat_name_ui.grid_remove()
            self.station_lat_entry_ui.grid_remove()
            self.station_lon_name_ui.grid_remove()
            self.station_lon_entry_ui.grid_remove()
            self.coord_ex_l1.grid_remove()
            self.coord_ex_l2.grid_remove()
            # Show elements
            self.line_start_name_ui.grid()
            self.line_start_entry_ui.grid()
            self.column_selection_name_ui.grid()
            self.column_selection_name_selection.grid()
            self.delta_name_ui.grid()
            self.delta_entry_ui.grid()
        else:
            self.lat_name_ui.grid()
            self.lat_entry_ui.grid()
            self.lon_name_ui.grid()
            self.lon_entry_ui.grid()
            self.station_lat_name_ui.grid()
            self.station_lat_entry_ui.grid()
            self.station_lon_name_ui.grid()
            self.station_lon_entry_ui.grid()
            self.coord_ex_l1.grid()
            self.coord_ex_l2.grid()
            # Hide elements
            self.line_start_name_ui.grid_remove()
            self.line_start_entry_ui.grid_remove()
            self.column_selection_name_ui.grid_remove()
            self.column_selection_name_selection.grid_remove()
            self.delta_name_ui.grid_remove()
            self.delta_entry_ui.grid_remove()

    def update_ui_combobox_changes(self, ev):
        filter_type_check_ui = self.filter_type_name_selection.get()
        filters_lowpass_l = [
            "Butterworth-lowpass",
            "Lowpass-Cheby-2",
        ]
        filters_highpass_l = [
            "Butterworth-highpass",
        ]
        self.freq_min_entry_ui.grid_remove()
        self.freq_min_name_ui.grid_remove()
        if filter_type_check_ui in filters_lowpass_l:
            # NOTE: Get freq max
            self.freq_max_name_ui.config(
                text="Cutoff frequency for filter (25 Hz)"
            )
        elif filter_type_check_ui in filters_highpass_l:
            self.freq_max_name_ui.config(
                text="Cutoff frequency for filter (0.1 Hz)"
            )
        else:
            self.freq_max_name_ui.config(
                text="Maximum frequency for filter (25 Hz)"
            )
            self.freq_min_entry_ui.grid()
            self.freq_min_name_ui.grid()


def rapid_sis_gui():
    self = processing_gui()
    self.mainloop()
