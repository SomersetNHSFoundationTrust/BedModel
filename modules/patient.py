import numpy as np
from typing import Protocol

from .tools import Unique


class PatientGenerator(Protocol):
    def patient_generator(self) -> None:
        pass


class BasicPatientGenerator:
    def __init__(self, source_probability, category_probability, los_distributions):

        self.source_probability = source_probability
        self.category_probability = category_probability
        self.los_distributions = los_distributions

        self.unique = Unique()
        self.probabilities = self.__calculate_probabilities()

    def __calculate_probabilities(self):

        probabilities = {}
        for source, source_probability in self.source_probability.items():
            for category, category_probability in self.category_probability.get(source, {None: 1}).items():
                probabilities[(source, category)] = source_probability * category_probability

        assert np.isclose(sum(probabilities.values()), 1), "Probabilities do not sum to 1"

        return probabilities

    def patient_generator(self, n, warm=False, source_=None):
        """
        Create stochastic patients based on probability and distributions
        :param source_: the type of patient to generate
        :param warm: whether to generate from warmup
        :param n: Number of patients to generate
        :return: patients to patient_master
        """
        keys = list(self.probabilities.keys())
        probs = list(self.probabilities.values())

        if not warm:
            if not source_:
                raise Exception('A source has not been specified for the patient to be generated')
            keys, probs = zip(*self.category_probability[source_].items())
            keys = [(source_, category) for category in keys]

        choices = np.random.choice([*range(len(keys))], p=probs, size=n)

        patients_info = []
        for choice in choices:
            source, category = keys[choice]

            # TODO: this is a bit of a hack that we should have a think about...
            if source == "Waiting List":
                source = "Elective"
                category = "Elective"

            los = int(np.random.lognormal(*self.los_distributions[source][category]))

            patients_info.append([self.unique.next_counter(), source, category, los, 0])

        return patients_info
