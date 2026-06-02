import numpy as np

epsilon = 1.0

oman_subjects = ["Math", "Phys", "Chem", "Bio", "Arabic", "Islamic", "Social", "Eng"]

oman_corr = np.array([
    [ 1.00, 0.75, 0.73, 0.60, 0.50, 0.47, 0.44, -0.10],
    [ 0.75, 1.00, 0.70, 0.65, 0.49, 0.49, 0.51,  0.04],
    [ 0.73, 0.70, 1.00, 0.69, 0.55, 0.56, 0.52, -0.08],
    [ 0.60, 0.65, 0.69, 1.00, 0.60, 0.62, 0.67,  0.01],
    [ 0.50, 0.49, 0.55,  0.60, 1.00, 0.70, 0.59,  0.05],
    [ 0.47, 0.49, 0.56,  0.62, 0.70, 1.00, 0.65, -0.08],
    [ 0.44, 0.51, 0.52,  0.67, 0.59, 0.65, 1.00,  0.05],
    [-0.10, 0.04,-0.08,  0.01, 0.05,-0.08, 0.05,  1.00],
])

subject_map = {
    "AMATH": "Math", "BIOST": "Math", "BUS AN": "Math", "CFRM": "Math",
    "CSE": "Math", "CSE D": "Math", "CSE M": "Math", "CSE P": "Math",
    "CSSS": "Math", "DATA": "Math", "I S": "Math", "IMT": "Math",
    "IND E": "Math", "INFO": "Math", "INSC": "Math", "MATH": "Math",
    "MSIS": "Math", "Q SCI": "Math", "QERM": "Math", "QMETH": "Math",
    "STAT": "Math", "TECHIN": "Math",

    "A A": "Phys", "A E": "Phys", "ASTR": "Phys", "ATMOS": "Phys",
    "CEE": "Phys", "E E": "Phys", "ENGR": "Phys", "ESS": "Phys",
    "M E": "Phys", "OCEAN": "Phys", "PHYS": "Phys", "QUAT": "Phys",

    "BATY E": "Chem", "CHEM": "Chem", "CHEM E": "Chem", "MEDCH": "Chem",
    "MEDECK": "Chem", "MEDRCK": "Chem", "MOLENG": "Chem", "MSE": "Chem",
    "NME": "Chem", "PCEUT": "Chem", "PHARBE": "Chem", "PHARM": "Chem",
    "PHARMP": "Chem", "PHCOL": "Chem", "PHRMCY": "Chem", "PHRMPR": "Chem",
    "PHRMRA": "Chem", "PHRMSC": "Chem", "SBSE": "Chem",

    "ANEST": "Bio", "ASTBIO": "Bio", "B BIO": "Bio", "B STR": "Bio",
    "BIME": "Bio", "BIO A": "Bio", "BIOC": "Bio", "BIOEN": "Bio",
    "BIOL": "Bio", "BMSD": "Bio", "C MED": "Bio", "CONJ": "Bio",
    "D HYG": "Bio", "DENT": "Bio", "DENTCL": "Bio", "DENTCP": "Bio",
    "DENTEL": "Bio", "DENTFN": "Bio", "DENTGP": "Bio", "DENTPC": "Bio",
    "DENTSL": "Bio", "DERM": "Bio", "DPHS": "Bio", "ENDO": "Bio",
    "ENV H": "Bio", "EPI": "Bio", "ESRM": "Bio", "FAMED": "Bio",
    "FHL": "Bio", "FISH": "Bio", "G H": "Bio", "GCNSL": "Bio",
    "GENOME": "Bio", "HMS": "Bio", "HUBIO": "Bio", "IMMUN": "Bio",
    "IPM": "Bio", "LAB M": "Bio", "MARBIO": "Bio", "MCB": "Bio",
    "MED": "Bio", "MED EM": "Bio", "MEDEX": "Bio", "MEDSCI": "Bio",
    "MICROM": "Bio", "MSTP": "Bio", "N SCI": "Bio", "NBIO": "Bio",
    "NCLIN": "Bio", "NEUBIO": "Bio", "NEUR S": "Bio", "NEURL": "Bio",
    "NEURO": "Bio", "NEUSCI": "Bio", "NMETH": "Bio", "NSG": "Bio",
    "NURS": "Bio", "NUTR": "Bio", "OB GYN": "Bio", "OHS": "Bio",
    "OPHTH": "Bio", "ORALB": "Bio", "ORALM": "Bio", "ORTHO": "Bio",
    "ORTHP": "Bio", "OTOHN": "Bio", "P BIO": "Bio", "PA EX": "Bio",
    "PABIO": "Bio", "PATH": "Bio", "PBSCI": "Bio", "PEDO": "Bio",
    "PEDS": "Bio", "PERIO": "Bio", "PHG": "Bio", "PROS": "Bio",
    "PSYCAP": "Bio", "PSYCLN": "Bio", "R ONC": "Bio", "RADGY": "Bio",
    "REHAB": "Bio", "RES D": "Bio", "RHB PO": "Bio", "SEFS": "Bio",
    "SURG": "Bio", "UCONJ": "Bio", "UROL": "Bio",

    "ARAB": "Arabic",

    "A S": "Social", "AAS": "Social", "ACCTG": "Social", "ADMIN": "Social",
    "AES": "Social", "AFRAM": "Social", "AIS": "Social", "ANTH": "Social",
    "ARCHY": "Social", "ARCTIC": "Social", "B A": "Social",
    "B ECON": "Social", "B E": "Social", "B H": "Social", "BA RM": "Social",
    "C ENV": "Social", "CEP": "Social", "CESG": "Social", "CESI": "Social",
    "CET": "Social", "CEWA": "Social", "CHID": "Social", "CHSTU": "Social",
    "CM": "Social", "CSDE": "Social", "DIS ST": "Social", "ECE": "Social",
    "ECFS": "Social", "ECON": "Social", "EDC&I": "Social", "EDLPS": "Social",
    "EDPSY": "Social", "EDSPE": "Social", "EDTEP": "Social", "EDUC": "Social",
    "ENTRE": "Social", "ENVIR": "Social", "ESMS": "Social",
    "ETHICS": "Social", "FIN": "Social", "GEN ST": "Social", "GEOG": "Social",
    "GRDSCH": "Social", "GWSS": "Social", "HCSS": "Social", "HEOR": "Social",
    "HIHIM": "Social", "HONORS": "Social", "HPS": "Social",
    "HSERV": "Social", "HSMGMT": "Social", "HSTAA": "Social",
    "HSTAFM": "Social", "HSTAM": "Social", "HSTAS": "Social",
    "HSTCMP": "Social", "HSTEU": "Social", "HSTLAC": "Social",
    "HSTRY": "Social", "I BUS": "Social", "IECMH": "Social",
    "INDIV": "Social", "INTSCI": "Social", "IPHD": "Social", "ISS": "Social",
    "JSIS": "Social", "JSIS A": "Social",
    "JSIS B": "Social", "JSIS C": "Social", "JSIS D": "Social",
    "JSIS E": "Social", "LABOR": "Social", "LAW": "Social",
    "LAW A": "Social", "LAW B": "Social", "LAW C": "Social",
    "LAW E": "Social", "LAW H": "Social", "LAW P": "Social",
    "LAW T": "Social", "LEAD": "Social", "LIS": "Social", "LSJ": "Social",
    "M SCI": "Social", "MGMT": "Social", "MKTG": "Social",
    "N MES": "Social", "O S": "Social", "OPMGT": "Social", "PHI": "Social",
    "PHIL": "Social", "POL S": "Social", "PPM": "Social", "PSYCH": "Social",
    "PUBPOL": "Social", "R E": "Social", "SCM": "Social",
    "SMEA": "Social", "SOC": "Social", "SOC W": "Social", "SOC WF": "Social",
    "SOC WL": "Social", "SPH": "Social", "STSS": "Social", "URBAN": "Social",
    "URBDP": "Social",

    "ARAMIC": "Islamic", "BIBHEB": "Islamic", "COPTIC": "Islamic",
    "GEEZ": "Islamic", "JEW ST": "Islamic", "MELC": "Islamic",
    "MODHEB": "Islamic", "RELIG": "Islamic", "SNKRT": "Islamic",
    "UGARIT": "Islamic",

    "AMHAR": "Eng", "ARCH": "Eng", "ART": "Eng",
    "ART H": "Eng", "ASIAN": "Eng", "ASL": "Eng", "B CMU": "Eng",
    "BCMS": "Eng", "BENG": "Eng", "BULGR": "Eng",
    "C LIT": "Eng", "CHGTAI": "Eng", "CHIN": "Eng", "CL AR": "Eng",
    "CL LI": "Eng", "CLAS": "Eng", "CMS": "Eng", "COM": "Eng",
    "COMMLD": "Eng", "CZECH": "Eng", "DANCE": "Eng",
    "DANISH": "Eng", "DESIGN": "Eng", "DRAMA": "Eng", "DXARTS": "Eng",
    "EGYPT": "Eng", "ENGL": "Eng", "ESTO": "Eng", "FINN": "Eng",
    "FRENCH": "Eng", "GEORG": "Eng", "GERMAN": "Eng",
    "GLITS": "Eng", "GREEK": "Eng", "HCDE": "Eng", "HCID": "Eng",
    "HINDI": "Eng", "HUM": "Eng", "INDN": "Eng", "INDO": "Eng",
    "ITA": "Eng", "ITAL": "Eng", "JAPAN": "Eng", "KAZAKH": "Eng",
    "KHMER": "Eng", "KOREAN": "Eng", "KYRGYZ": "Eng", "L ARCH": "Eng",
    "LADINO": "Eng", "LATIN": "Eng", "LATV": "Eng", "LING": "Eng",
    "LITH": "Eng", "LITS": "Eng", "MUHST": "Eng",
    "MUSAP": "Eng", "MUSED": "Eng", "MUSEN": "Eng", "MUSEUM": "Eng",
    "MUSIC": "Eng", "MUSICP": "Eng", "MUSTEC": "Eng", "NORW": "Eng",
    "POLSH": "Eng", "PORT": "Eng", "PRSAN": "Eng", "ROMN": "Eng",
    "RUSS": "Eng", "S ASIA": "Eng", "SCAND": "Eng", "SEASIA": "Eng",
    "SLAVIC": "Eng", "SLVN": "Eng", "SPAN": "Eng",
    "SPHSC": "Eng", "SPLING": "Eng", "SWA": "Eng", "SWED": "Eng",
    "TAGLG": "Eng", "THAI": "Eng", "TKISH": "Eng", "TURKIC": "Eng",
    "TXTDS": "Eng", "UKR": "Eng", "URDU": "Eng",
    "UYGUR": "Eng", "UZBEK": "Eng", "VIET": "Eng",
}


def corr(subject_a, subject_b):
    return oman_corr[oman_subjects.index(subject_map[subject_a]), oman_subjects.index(subject_map[subject_b])]

def subject_z_scores(transcript, courses):
    by_subject = {}
    for entry in transcript:
        course = courses[entry["course_id"]]
        subject = course["department"].upper()
        by_subject.setdefault(subject, []).append(
            (entry["grade"] - course["mean"]) / np.sqrt(course["variance"])
        )
    return {subject: {"mean_z": np.mean(zs), "n_courses": len(zs)} for subject, zs in by_subject.items()}


def predict_course(target_course_id, student_subjects, courses):
    target = courses[target_course_id]
    taken_subjects = list(student_subjects.keys())

    r_vector = np.array([corr(target["department"].upper(), s) for s in taken_subjects])
    n = len(taken_subjects)
    R_matrix = np.zeros((n, n))
    for i in range(len(taken_subjects)):
        for j in range(len(taken_subjects)):
            R_matrix[i, j] = corr(taken_subjects[i], taken_subjects[j])
        R_matrix[i, i] += epsilon

    beta = np.linalg.solve(R_matrix, r_vector)
    predicted_z = beta @ np.array([student_subjects[s]["mean_z"] for s in taken_subjects])
    R2 = r_vector @ beta

    return {
        "mean": target["mean"] + np.sqrt(target['variance']) * predicted_z,
        "variance": target["variance"] * (1.0 - R2),
        "predicted_z": predicted_z,
        "R2": R2,
    }
