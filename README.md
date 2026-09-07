# RAPID-SIS
Automatic report generation out of miniSEED files.

## Dependencies
- `Conda`
### Windows
- We also recommend having `Anaconda navigator` so it is easier to launch the program.

## Installation
### Linux and MacOS
Clone the repo and run the following commands inside the conda environment you want to put this in:
```sh
conda build recipe
conda install --use-local rapidsis -y
```
### Windows
Run the installer available at: []().

## Using
### Terminal
The command is `rapidsis` you MUST specify `--no_gui` to not start the GUI, and you must specify `--filename` 
and point to the miniSEED you which to process, everything else is optional.

You run the program like this: `rapidsis --filename dummy_event.seed`.
The program creates a folder in your home directory called `rapidsis` 
and inside it, there is a folder called `Records`, 
which will create a folder for each event.

In this case the event folder generated will be `dummy event` with the path `~/rapidsis/Records/dummy_event`.

#### Options
- `--no_gui`: Don't initialize the gui
- `--filename`: The path to the file we will process.
- `--lat`: The latitude of the event.
- `--lon`: The longitude of the event.
- `--s_lat`: The latitude of the station. Only necessary if it is not a known station.
- `--s_lon`: The longitude of the longitude. Only necessary if it is not a known station.
- `--sens`: Sensor sensitivity, the default value for a TITAN SMA acelerograph is 2.
- `--threshold`: The minimum value of acceleration we want to reach before starting the treatment of our signal. Default value is 0.1 cm/s^2.
- `--filter`: The type of filter used. Butterworth options are: bp (bandpass), bs (bandstop), lp (lowpass), hp (highpass). Cheby 2 options: lpc2 (lowpass_cheby_2). Defaults to bandpass. In the case of a lp or hp filter, the minimum frequency will be ignored, and the maximum frequency will be used as the corner frequency.
- `--freq_min`: The minimum frequency to use for the filter. Default value is 0.1 Hz.
- `--freq_max`: The maximum frequency to use for the filter. Default value is 25 Hz 
- `--output_dir`: Directory where the images and other related files will be output to. Defaults to `~/rapidsis`
- `--latex_dir`: Directory where the latex files will live. This will be created inside of the output directory.

##### Spectral method
- `duhamel` for Duhamels double integral
- `fast` for Nigam and Jennings numerical method

### GUI
The gui can be launched by running `rapidsis` with no flags or by launching through `Anaconda Navigator`.
![RAPID-SIS GUI](./imgs/gui.png)

#### Options
##### Left
- `Open a File`: Select the miniSEED file we will process.
- `Choose a Directory`: Directory where the images and other related files will be output to. Defaults to `~/rapidsis`
- `Choose a pdflatex binary`: Path to the `pdflatex` executable that will be used. Don't select anything if the binary is available in `PATH`.

##### Right
- `Latitude of event`: The latitude of the event.
- `Longitude of event`: The longitude of the event.
- `Latitude of station`: The latitude of the station. Only necessary if it is not a known station.
- `Longitude of station`: The longitude of the longitude. Only necessary if it is not a known station.
- `Sensor sensitivity`: Sensor sensitivity, the default value for a TITAN SMA acelerograph is 2.
- `Acceleration threshold`: The minimum value of acceleration we want to reach before starting the treatment of our signal. Default value is 0.1 cm/s^2.
- `Select filter type`: The filter that will be used for processing.
- `Minimum frequency for filter`: The minimum frequency to use for the filter. Default value is 0.1 Hz.
- `Maximum frequency for filter`: The maximum frequency to use for the filter. Default value is 25 Hz 
