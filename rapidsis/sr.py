import numpy as np


# spectral response
def rs_func_nigam_jennings(data, delta, T, damp_factor):
    # preliminary computations
    w = 2 * np.pi / T
    acc_spectra = np.zeros(len(T))
    vel_spectra = np.zeros(len(T))
    disp_spectra = np.zeros(len(T))
    for i in np.arange(len(T)):
        DW = damp_factor * w[i]
        D2 = damp_factor**2
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

        # responses u, up and upp (absolute acceleration)
        npts = len(data)
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

        disp_spectra[i] = np.max(np.abs(u))
        vel_spectra[i] = np.max(np.abs(up))
        acc_spectra[i] = np.max(np.abs(upp))

    return disp_spectra, vel_spectra, acc_spectra