import random
from modules.tools import *


class Patient:
    def __init__(self, gender, age_mean, age_sigma):
        """

        :param admission_source: Elective, Emergency Medical, Emergency Surgical
        """
        self.uid = Unique()
        self.admission_route = None
        self.age_mean = age_mean
        self.age_sigma = age_sigma
        self.gender = gender
        self.tfc = None
        self.procedure = None
        self.los = None
        self.infectious = None
        self.risk_critical_care = None

    def fetch_gender(self):
        if random.random() < float(self.gender):
            return 'm'
        else:
            return 'f'

    def fetch_age(self):
        pass

    def fetch_los(self):
        pass

    def fetch_tfc(self):
        pass

    def fetch_procedure(self):
        pass

    def fetch_critical_care_risk(self):
        pass

    def fetch_infection(self):
        """
        likelihood of being admitted whilst infectious from e.g. Norovirus, COVID
        :return:
        """
        pass

    def generate(self, admission_route):

        uid = self.uid.next_counter()

        self.admission_route = admission_route
        patients_gender = self.fetch_gender()
        self.fetch_age()
        self.fetch_tfc()
        self.fetch_los()
        self.fetch_procedure()
        self.fetch_critical_care_risk()
        self.fetch_infection()

        patient = [uid, patients_gender]#, self.admission_route, self.fetch_age, self.fetch_tfc, self.fetch_los,
                   #self.fetch_procedure, self.fetch_infection, self.risk_critical_care]

        return patient
