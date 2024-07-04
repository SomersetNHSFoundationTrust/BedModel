import pytest
from ...patient import BasicPatientGenerator


@pytest.fixture
def sample_patient_generator():
    source_prob = {"Emergency Department": 0.8, "Non-ED Admission": 0.14, "Waiting List": 0.06}

    category_prob = {"Emergency Department": {'Elective':0, 'Surgical Emergency':0.2, 'Medical Emergency':0.8},
                     "Non-ED Admission": {'Elective':0, 'Surgical Emergency':0.4, 'Medical Emergency':0.6}
                     }

    los_distributions = {
        'Emergency Department': {'Elective': (1, 0.5), 'Surgical Emergency': (2, 0.7), 'Medical Emergency': (3, 1)},
        'Non-ED Admission': {'Elective': (1.5, 0.6), 'Surgical Emergency': (2.5, 0.8), 'Medical Emergency': (3.5, 1.2)},
        'Elective': {'Elective': (2, 0.7)}
    }
    return BasicPatientGenerator(source_prob, category_prob, los_distributions)


def test_patient_generator_output(sample_patient_generator):
    patients_data = sample_patient_generator.patient_generator(5, warm=True)
    assert len(patients_data) == 5
    for patient in patients_data:
        assert isinstance(patient, list)
        assert len(patient) == 5
        assert isinstance(patient[0], int)  # patient_id
        assert isinstance(patient[1], str)  # source
        assert isinstance(patient[2], str)  # category
        assert isinstance(patient[3], int)  # los
        assert isinstance(patient[4], int)  # continuing_los


def test_patient_generator_output_with_source(sample_patient_generator):
    patients_data = sample_patient_generator.patient_generator(5, warm=False, source_='Emergency Department')
    assert len(patients_data) == 5
    for patient in patients_data:
        assert isinstance(patient, list)
        assert len(patient) == 5
        assert isinstance(patient[0], int)  # patient_id
        assert isinstance(patient[1], str)  # source
        assert patient[1] == 'Emergency Department'
        assert isinstance(patient[2], str)  # category
        assert isinstance(patient[3], int)  # los
        assert isinstance(patient[4], int)  # continuing_los


def test_patient_generator_raises_exception(sample_patient_generator):
    with pytest.raises(Exception):
        sample_patient_generator.patient_generator(5, warm=False)
