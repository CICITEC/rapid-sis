import matplotlib

matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.pylab as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
import sys

from . import comp_processing as cproc
from . import rsisutil
from . import mapgen

colors = [
    "tab:blue",
    "tab:red",
    "tab:green",
    "tab:brown",
    "tab:pink",
]
colors_h = [
    "tab:cyan",
    "tab:purple",
    "tab:orange",
    "tab:gray",
    "tab:olive",
]
colors_all = [
    "tab:blue",
    "tab:red",
    "tab:green",
    "tab:brown",
    "tab:pink",
    "tab:cyan",
    "tab:purple",
    "tab:orange",
    "tab:gray",
    "tab:olive",
]


# Euclidean rule
def hodogram_x(
        e_comp_data: np.ndarray | np.ma.MaskedArray,
        n_comp_data: np.ndarray | np.ma.MaskedArray,
        fig,
        gspec,
        comp_bundle: cproc.CompBundle,
        ptype="Acc",
        unit="$cm/s^2$",
        pcolor=0,
):
    """Hodogram generation for an x type of data, like acceleration, velocity and displacement"""
    e_acc = e_comp_data
    n_acc = n_comp_data
    rotd100_acc = np.sqrt(e_acc * e_acc + n_acc * n_acc)
    rotd100_max_idx = np.argmax(rotd100_acc)
    rotd100_max = rotd100_acc[rotd100_max_idx]
    sys.stderr.write(f"IDX: {rotd100_max_idx}, value: {rotd100_max}")
    rotd100_angle_max = np.arctan2(
        n_acc[rotd100_max_idx], e_acc[rotd100_max_idx]
    )
    rotd100_angle_deg_max = np.degrees(rotd100_angle_max)

    ax = fig.add_subplot(gspec)

    plt.plot(
        e_acc,
        n_acc,
        color=colors_h[pcolor],
        linewidth=1.5,
    )
    text = f"Max: {round(rotd100_max, 3)}\n Angle:{
    round(rotd100_angle_deg_max, 2)}"

    plt.plot(
        e_acc[rotd100_max_idx],
        n_acc[rotd100_max_idx],
        "o",
        color="tab:gray",
        ms=5,
    )

    plt.text(
        e_acc[rotd100_max_idx],
        n_acc[rotd100_max_idx],
        text,
        fontsize=18,
    )

    plt.xlabel(f"{ptype} E-W ({unit})", fontsize=20)
    plt.ylabel(f"{ptype} N-S ({unit})", fontsize=20)
    plt.grid()
    plt.legend()
    plt.tight_layout()


def generate_acceleration_spectra_all(
        fig, gspec, rotd, comps: cproc.CompBundle
):
    """
    This function generates the acceleration spectra
    """

    # SECTION: Plotting
    ax = fig.add_subplot(gspec)
    for i, comp in enumerate(comps.comp_list):
        plt.semilogx(
            comp.periods,
            comp.acc_spectra,
            linewidth=2,
            color=colors_all[i],
            label=comp.name,
        )

    if len(comps.comp_list) > 1 and rotd:
        plt.semilogx(
            comps.comp_list[0].periods,
            comps.acc_rotd100,
            linewidth=2,
            color="k",
            ls="--",
            label="RotD100",
        )
        plt.semilogx(
            comps.comp_list[0].periods,
            comps.acc_rotd50,
            linewidth=2,
            color="tab:grey",
            ls="-.",
            # linewidth=2.5,
            label="RotD50",
        )
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)

    plt.grid()
    plt.ylabel("SA ($cm/s^2$)", fontsize=20)
    plt.xlabel("T (s)", fontsize=20)
    plt.tight_layout()
    plt.legend(fontsize=16)


def generate_velocity_spectra_all(fig, gspec, comps: cproc.CompBundle):
    """
    This function generates the velocity spectra plot
    """

    # SECTION: Plotting
    ax = fig.add_subplot(gspec)
    for i, comp in enumerate(comps.comp_list):
        plt.semilogx(
            comp.periods,
            comp.vel_spectra,
            linewidth=2,
            # So the colors are always different
            color=colors_all[i + 3],
            label=comp.name,
        )
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)

    plt.grid()
    plt.ylabel("SV ($cm/s$)", fontsize=20)
    plt.xlabel("T (s)", fontsize=20)
    plt.tight_layout()
    plt.legend(fontsize=16)


def generate_displacement_spectra_all(
        fig, gspec, comps: cproc.CompBundle
):
    """
    This function generates the displacement spectra
    """

    # SECTION: Plotting
    ax = fig.add_subplot(gspec)
    for i, comp in enumerate(comps.comp_list):
        plt.semilogx(
            comp.periods,
            comp.disp_spectra,
            linewidth=2,
            color=colors_all[i + 6],
            label=comp.name,
        )
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)

    plt.grid()
    plt.ylabel("SD (cm)", fontsize=20)
    plt.xlabel("T (s)", fontsize=20)
    plt.tight_layout()
    plt.legend(fontsize=16)


def generate_acceleration_plot(fig, gspec, comp: cproc.CompData):
    """
    This function generates the time histories for acceleration.
    """
    ax = fig.add_subplot(gspec)
    plt.plot(
        comp.trace.times("relative"), comp.acc_data, color=colors_h[0]
    )
    plt.grid()
    # plt.legend(loc=1)
    plt.title(f"{comp.trace.stats.channel}")

    text = f"PGA: {round(comp.pga_signed, 3)}"

    plt.ylabel(f"Acc. ($cm/s^2$)", fontsize=16)
    plt.plot(comp.pga_t, comp.pga_signed, "o", color="tab:gray", ms=5)
    plt.text(
        comp.pga_t + 0.1,
        comp.pga_signed,
        text,
        fontsize=14,
        wrap=True,
    )

def generate_velocity_plot(fig, gspec, comp: cproc.CompData):
    """
    This function generates the time histories for velocity.
    """

    ax = fig.add_subplot(gspec)
    plt.plot(
        comp.trace.times("relative"), comp.vel_data, color=colors_h[1]
    )
    plt.grid()
    plt.title(f"{comp.trace.stats.channel}")

    text = f"PGV: {round(comp.pgv_signed, 3)}"

    plt.ylabel(f"Vel. ($cm/s$)", fontsize=16)
    plt.plot(comp.pgv_t, comp.pgv_signed, "o", color="tab:gray", ms=5)
    plt.text(
        comp.pgv_t + 0.1,
        comp.pgv_signed,
        text,
        fontsize=14,
        wrap=True,
        )

def generate_displacement_plot(fig, gspec, comp: cproc.CompData):
    """
    This function generates the time histories for displacement.
    """

    ax = fig.add_subplot(gspec)
    plt.plot(
        comp.trace.times("relative"),
        comp.disp_data,
        color=colors_h[2],
    )
    plt.grid()
    plt.title(f"{comp.trace.stats.channel}")
    plt.tight_layout()

    text = f"PGD: {round(comp.pgd_signed, 3)}"

    plt.ylabel(f"Disp (cm)", fontsize=16)
    plt.plot(comp.pgd_t, comp.pgd_signed, "o", color="tab:gray", ms=5)
    plt.text(
        comp.pgd_t + 0.1,
        comp.pgd_signed,
        text,
        fontsize=14,
        wrap=True,
        )


def generate_displacement_plot_w_fig(fig, gspec, comp_list, path, time_str):
    for idx, comp in enumerate(comp_list):
        generate_displacement_plot(fig, gspec[idx, :], comp)
    plt.xlabel(time_str, fontsize=14)
    plt.tight_layout()
    plt.savefig(path)
    plt.clf()


def generate_velocity_plot_w_fig(fig, gspec, comp_list, path, time_str):
    for idx, comp in enumerate(comp_list):
        generate_velocity_plot(fig, gspec[idx, :], comp)
    plt.xlabel(time_str, fontsize=14)
    plt.tight_layout()
    plt.savefig(path)
    plt.clf()


def generate_acceleration_plot_w_fig(fig, gspec, comp_list, path, time_str):
    for idx, comp in enumerate(comp_list):
        generate_acceleration_plot(fig, gspec[idx, :], comp)
    plt.xlabel(time_str, fontsize=14)
    plt.tight_layout()
    plt.savefig(path)
    plt.clf()


def generate_figures(
        comp_bundle: cproc.CompBundle, opts: rsisutil.RapidOptions
):
    # How many rows we need
    rows = len(comp_bundle.comp_list)
    cols = 2
    # Width for histograms is always 18
    width = 18
    # Height, we want 3 for each histogram
    height = rows * 3
    fig_size_histograms = (width, height)
    fig = plt.figure(figsize=fig_size_histograms)
    gridspec_histograms = gridspec.GridSpec(rows, cols)

    generate_acceleration_plot_w_fig(
        fig,
        gridspec_histograms,
        comp_bundle.comp_list,
        f"{opts.record_dir}/acceleration_{opts.record_name}",
        f"Time (s) relative to {comp_bundle.start_time_with_offset}",
    )

    generate_velocity_plot_w_fig(
        fig,
        gridspec_histograms,
        comp_bundle.comp_list,
        f"{opts.record_dir}/velocity_{opts.record_name}",
        f"Time (s) relative to {comp_bundle.start_time_with_offset}",
    )

    generate_displacement_plot_w_fig(
        fig,
        gridspec_histograms,
        comp_bundle.comp_list,
        f"{opts.record_dir}/displacement_{opts.record_name}",
        f"Time (s) relative to {comp_bundle.start_time_with_offset}",
    )

    # Squared plots
    fig_sizes_sq = (12, 12 * 3)
    fig_sq = plt.figure(figsize=fig_sizes_sq)
    gs_sq = gridspec.GridSpec(3, 1, hspace=0.2)
    # Perfectly capable of dealing with n amount of components
    generate_acceleration_spectra_all(
        fig_sq, gs_sq[0, :], opts.rotd, comp_bundle
    )
    generate_velocity_spectra_all(fig_sq, gs_sq[1, :], comp_bundle)
    generate_displacement_spectra_all(fig_sq, gs_sq[2, :], comp_bundle)
    plt.savefig(
        f"{opts.record_dir}/spectras_{opts.record_name}",
        bbox_inches="tight",
    )
    plt.clf()

    # Rows is directly obtained from the number of components
    if rows > 1:
        # Acceleration
        hodogram_x(
            comp_bundle.comp_list[0].acc_data,
            comp_bundle.comp_list[1].acc_data,
            fig_sq,
            gs_sq[0, :],
            comp_bundle,
            ptype="Acc",
            unit="$cm/s^2$",
            pcolor=0,
        )

        # Velocity
        hodogram_x(
            comp_bundle.comp_list[0].vel_data,
            comp_bundle.comp_list[1].vel_data,
            fig_sq,
            gs_sq[1, :],
            comp_bundle,
            ptype="Vel",
            unit="$cm/s$",
            pcolor=1,
        )
        # Displacement
        hodogram_x(
            comp_bundle.comp_list[0].disp_data,
            comp_bundle.comp_list[1].disp_data,
            fig_sq,
            gs_sq[2, :],
            comp_bundle,
            ptype="Disp",
            unit="cm",
            pcolor=2,
        )
    plt.savefig(
        f"{opts.record_dir}/hodograms_{opts.record_name}",
        bbox_inches="tight",
    )

    # Map
    fig_map_size = (14, 14)
    fig_map = plt.figure(figsize=fig_map_size)
    gs_map = gridspec.GridSpec(2, 2)
    mapgen.gen_map(
        fig_map,
        gs_map[:, :],
        comp_bundle,
        f"{opts.record_dir}/map_{opts.record_name}",
    )
    plt.clf()
