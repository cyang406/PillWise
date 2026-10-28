"""synthea.py contract (stub now, real Synthea data later)."""

import pytest

from pillwise import synthea


def test_list_patients_shape_and_limit():
    patients = synthea.list_patients()
    assert patients and all(isinstance(pid, str) and (age is None or isinstance(age, int)) for pid, age in patients)
    assert len(synthea.list_patients(limit=1)) == 1


def test_patient_meds_are_synthea_meds():
    pid, _ = synthea.list_patients()[0]
    meds = synthea.patient_meds(pid)
    assert meds and all(m.source == "synthea" and m.ingredients for m in meds)
    assert all(i == i.lower() for m in meds for i in m.ingredients)


def test_unknown_patient_raises():
    with pytest.raises(KeyError):
        synthea.patient_meds("nobody")
