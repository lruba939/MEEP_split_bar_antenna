import os
import h5py
import numpy as np
import matplotlib.pyplot as plt


# =====================================================
# USER
# =====================================================

# PATH = "results/bowtie__lam-660__gap-6__L-87__T-30__R-5__ant-Au__sub-Au__14/cache/"
PATH2 = "results/bowtie__lam-660__gap-6__L-87__T-30__R-5__ant-Au__sub-Au__3/cache/"
PATH = "results/bowtie__lam-660__gap-6__L-87__T-30__R-5__ant-Au__sub-Au__15/cache/"

Nfreq = 500


# =====================================================
# HELPERS
# =====================================================

def load_flux_h5(fname):

    f = h5py.File(fname, "r")

    keys = list(f.keys())

    print("\nLoading:", fname)
    print("datasets:", keys)

    E = f[keys[0]][:]
    H = f[keys[1]][:]

    # float32 -> complex64
    E = E[0::2] + 1j * E[1::2]
    H = H[0::2] + 1j * H[1::2]

    E = E.reshape(-1, Nfreq)
    H = H.reshape(-1, Nfreq)

    return E, H


def flux_from_fields(E, H):

    return np.real(
        E * np.conj(H)
    ).sum(axis=0)


# =====================================================
# LOAD RAW SPECTRA
# =====================================================

empty_refl = np.load(
    os.path.join(PATH2,
                 "empty/TRL/refl.npz")
)

empty_tran = np.load(
    os.path.join(PATH2,
                 "empty/TRL/tran.npz")
)

ant_refl = np.load(
    os.path.join(PATH2,
                 "antenna/TRL/refl.npz")
)

ant_tran = np.load(
    os.path.join(PATH2,
                 "antenna/TRL/tran.npz")
)

freq = empty_refl["freqs"]
lam = 1/freq


# =====================================================
# LOAD DFT FIELDS
# =====================================================

E0r, H0r = load_flux_h5(
    os.path.join(
        PATH,
        "empty/refl_dft.h5"
    )
)

Ear, Har = load_flux_h5(
    os.path.join(
        PATH,
        "antenna/refl_dft.h5"
    )
)

# transmission
E0t, H0t = load_flux_h5(
    os.path.join(
        PATH,
        "empty/tran_dft.h5"
    )
)

Eat, Hat = load_flux_h5(
    os.path.join(
        PATH,
        "antenna/tran_dft.h5"
    )
)


# =====================================================
# OFFLINE LOAD_MINUS
# =====================================================

print("\nComputing offline load_minus...")

# reflection
Esc = Ear - E0r
Hsc = Har - H0r

refl_offline = flux_from_fields(
    Esc,
    Hsc,
)

# transmission
tran_offline = flux_from_fields(
    Eat,
    Hat,
)


# =====================================================
# COMPUTE TRA
# =====================================================

incident = empty_tran["flux"]

R_off = -refl_offline / incident
T_off = tran_offline / incident
A_off = 1 - R_off - T_off


# =====================================================
# REFERENCE MEEP
# =====================================================

R_meep = -ant_refl["flux"] / incident
T_meep = ant_tran["flux"] / incident
A_meep = 1 - R_meep - T_meep


# =====================================================
# ERRORS
# =====================================================

print()
print("max dR:",
      np.max(np.abs(R_off-R_meep)))

print("max dT:",
      np.max(np.abs(T_off-T_meep)))

print("max dA:",
      np.max(np.abs(A_off-A_meep)))


# =====================================================
# PLOT
# =====================================================

plt.figure(figsize=(8,5))

plt.plot(
    lam,
    R_meep,
    label="R meep",
    lw=3,
)

plt.plot(
    lam,
    R_off,
    "--",
    label="R offline",
)

plt.plot(
    lam,
    T_meep,
    label="T meep",
    lw=3,
)

plt.plot(
    lam,
    T_off,
    "--",
    label="T offline",
)

plt.plot(
    lam,
    A_meep,
    label="A meep",
    lw=3,
)

plt.plot(
    lam,
    A_off,
    "--",
    label="A offline",
)

plt.xlabel("wavelength [um]")
plt.ylabel("fraction")
plt.legend()
plt.grid()

plt.show()

# import os
# import numpy as np
# import matplotlib.pyplot as plt
# import pickle
# import numpy as np
# 
# 
# # ==========================================================
# # USER INPUT
# # ==========================================================
# print("\n\n")
# PATH = (
#     "results/bowtie__lam-660__gap-6__L-87__T-30__R-5__ant-Au__sub-Au__14/cache/"
# )
# 
# fname = "refl_dft.h5"
# 
# fpath = os.path.join(PATH, "empty", fname)
# 
# import h5py
# 
# f = h5py.File(fpath)
# 
# print(list(f.keys()))
# 
# for k in f.keys():
#     print(k)
# 
# print("\n")
# 
# for k in f.keys():
#     d = f[k]
#     print()
#     print(k)
#     print(type(d))
#     print("shape:", d.shape)
#     print("dtype:", d.dtype)
#     print("attrs:", list(d.attrs.keys()))
# 
# print("\n")
# 
# print(f["ex_dft"][:10])
# print(f["hy_dft"][:10])
# 
# print("\n")
# 
# ex = f["ex_dft"][:]
# 
# ex_complex = (
#     ex[0::2]
#     +
#     1j*ex[1::2]
# )
# 
# print(ex_complex.shape)
# 
# print("\n")
# 
# hy = f["hy_dft"][:]
# 
# hy_complex = (
#     hy[0::2]
#     +
#     1j*hy[1::2]
# )
# 
# print("\n")
# 
# Nfreq = 500
# 
# E = ex_complex.reshape(-1,Nfreq)
# H = hy_complex.reshape(-1,Nfreq)
# 
# flux = np.real(
#     E*np.conj(H)
# ).sum(axis=0)
# 
# print("\n")
# 
# # fname = "refl_flux_data.pkl"
# # with open(fpath, "rb") as f:
# #     fd = pickle.load(f)
# # 
# # print(type(fd))
# # print()
# # 
# # print("E:")
# # print(type(fd.E))
# # print(fd.E.dtype)
# # print(fd.E.shape)
# # print(fd.E.nbytes/1024**3, "GB")
# # print(fd.E[:5])
# # print()
# # 
# # print("H:")
# # print(type(fd.H))
# # print(fd.H.dtype)
# # print(fd.H.shape)
# # print(fd.H.nbytes/1024**3, "GB")
# # print(fd.H[:5])
# # print()
# # 
# # print("len(E):", len(fd.E))
# # print("len(H):", len(fd.H))
# # 
# # Nfreq = 500
# # 
# # E = fd.E.reshape(-1, Nfreq)
# # H = fd.H.reshape(-1, Nfreq)
# # 
# # print(E.shape)
# # print(H.shape)
# # 
# # print("nonzero E: ", np.count_nonzero(fd.E))
# # print("nonzero H: ", np.count_nonzero(fd.H))
# # 
# # print(np.max(np.abs(fd.E)))
# # print(np.max(np.abs(fd.H)))
# # 
# # flux = np.real(
# #     E * np.conj(H)
# # ).sum(axis=0)
# # 
# # print(flux.shape)
# 
# # ==========================================================
# # LOAD
# # ==========================================================
# 
# PATH2 = (
#     "results/bowtie__lam-660__gap-6__L-87__T-30__R-5__ant-Au__sub-Au__12/cache/"
# )
# 
# def load_TRL(path):
# 
#     refl = np.load(
#         os.path.join(path, "TRL", "refl.npz")
#     )
# 
#     tran = np.load(
#         os.path.join(path, "TRL", "tran.npz")
#     )
# 
#     return {
#         "refl": refl["flux"],
#         "tran": tran["flux"],
#         "freqs": refl["freqs"],
#     }
# 
# 
# print("Loading data...")
# 
# empty = load_TRL(
#     os.path.join(PATH2, "empty")
# )
# 
# print("flux - refl",
#     np.max(
#         np.abs(
#             flux-empty["refl"]
#         )
#     )
# )
# 
# print("WITH flux[::-1]",
#     np.max(
#         np.abs(
#             flux[::-1]
#             - empty["refl"]
#         )
#     )
# )
# 
# plt.plot(1/empty["freqs"], flux, "r-", label="calc")
# plt.plot(1/empty["freqs"], empty["refl"], "k:", label="meep")
# plt.legend(loc="best")
# plt.show()
# 
# # print("flux values:\n")
# # print(flux)
# 
# print("\n\n")
# # 
# # substrate = load_TRL(
# #     os.path.join(PATH, "substrate")
# # )
# # 
# # antenna = load_TRL(
# #     os.path.join(PATH, "antenna")
# # )
# # 
# # print("Done.")
# # 
# # # ==========================================================
# # # INCIDENT
# # # ==========================================================
# # 
# # incident = empty["tran"]
# # 
# # freq = empty["freqs"]
# # wavelength = 1 / freq
# # 
# # # ==========================================================
# # # SUBSTRATE
# # # ==========================================================
# # 
# # R_sub = -(
# #     substrate["refl"]
# #     - empty["refl"]
# # ) / incident
# # 
# # T_sub = (
# #     substrate["tran"]
# # ) / incident
# # 
# # A_sub = 1 - R_sub - T_sub
# # 
# # # ==========================================================
# # # ANTENNA
# # # ==========================================================
# # 
# # R_ant = -(
# #     antenna["refl"]
# #     - empty["refl"]
# # ) / incident
# # 
# # T_ant = (
# #     antenna["tran"]
# # ) / incident
# # 
# # A_ant = 1 - R_ant - T_ant
# # 
# # # ==========================================================
# # # ANTENNA - SUBSTRATE
# # # ==========================================================
# # 
# # R_ant_sub = -(
# #     antenna["refl"]
# #     - substrate["refl"]
# # ) / incident
# # 
# # T_ant_sub = (
# #     antenna["tran"]
# #     - substrate["tran"]
# # ) / incident
# # 
# # A_ant_sub = 1 - R_ant_sub - T_ant_sub
# # 
# # # ==========================================================
# # # CHECK
# # # ==========================================================
# # 
# # print()
# # print("SUBSTRATE:")
# # print(
# #     "max |R+T+A-1| =",
# #     np.max(
# #         np.abs(
# #             R_sub + T_sub + A_sub - 1
# #         )
# #     )
# # )
# # 
# # print()
# # print("ANTENNA:")
# # print(
# #     "max |R+T+A-1| =",
# #     np.max(
# #         np.abs(
# #             R_ant + T_ant + A_ant - 1
# #         )
# #     )
# # )
# # 
# # # ==========================================================
# # # PLOTS
# # # ==========================================================
# # 
# # plt.figure(figsize=(8,5))
# # plt.plot(
# #     wavelength,
# #     R_sub,
# #     label="R substrate"
# # )
# # plt.plot(
# #     wavelength,
# #     T_sub,
# #     label="T substrate"
# # )
# # plt.plot(
# #     wavelength,
# #     A_sub,
# #     label="A substrate"
# # )
# # plt.legend()
# # plt.xlabel("Wavelength [um]")
# # plt.ylabel("Fraction")
# # plt.title("Substrate")
# # plt.grid(True)
# # 
# # plt.figure(figsize=(8,5))
# # plt.plot(
# #     wavelength,
# #     R_ant,
# #     label="R antenna"
# # )
# # plt.plot(
# #     wavelength,
# #     T_ant,
# #     label="T antenna"
# # )
# # plt.plot(
# #     wavelength,
# #     A_ant,
# #     label="A antenna"
# # )
# # plt.legend()
# # plt.xlabel("Wavelength [um]")
# # plt.ylabel("Fraction")
# # plt.title("Antenna")
# # plt.grid(True)
# # 
# # plt.figure(figsize=(8,5))
# # plt.plot(
# #     wavelength,
# #     R_ant_sub,
# #     label="R antenna-substrate"
# # )
# # plt.plot(
# #     wavelength,
# #     T_ant_sub,
# #     label="T antenna-substrate"
# # )
# # plt.plot(
# #     wavelength,
# #     A_ant_sub,
# #     label="A antenna-substrate"
# # )
# # plt.legend()
# # plt.xlabel("Wavelength [um]")
# # plt.ylabel("Fraction")
# # plt.title("Antenna only")
# # plt.grid(True)
# # 
# # plt.show()
