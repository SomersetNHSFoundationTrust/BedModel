import numpy as np

from .tools import Unique

class PatientGenerator:
    def __init__(self, source_probability, category_probability, los_distributions):

        self.source_probability = source_probability
        self.category_probability = category_probability
        self.los_distributions = los_distributions

        self.unique = Unique()

    def patient_generator(self, n, warm=False, source_=None):
        """
        Create stochastic patients based on probability and distributions
        :param source_: the type of patient to generate
        :param warm: whether to generate from warmup
        :param n: Number of patients to generate
        :return: patients to patient_master
        """
        patients_data = []
        if warm:

            for i in range(0, n):

                patient_id, source, category, los, continuing_los = self.unique.next_counter(), None, None, None, 0

                # TODO: I wonder if it's better to multiply this out, then randomly select the resultant tuple with probabilities...
                # - Could use an nx graph here, with the los generator being a node attribute on the terminal nodes?

                source = np.random.choice(['Emergency Department', 'Non-ED Admission', 'Elective'],
                                          1,
                                          p=[self.source_probability.get('Emergency Department'),
                                             self.source_probability.get('Non-ED Admissions'),
                                             self.source_probability.get('Waiting List')]).item(0)

                # Get the corresponding probability that the Patient will be Elective, Surgical Emergency or Medical Emergency

                if source == 'Emergency Department':
                    category = np.random.choice(['Elective', 'Surgical Emergency', 'Medical Emergency'],
                                                1,
                                                p=[self.category_probability.get(source)['Elective'],
                                                   self.category_probability.get(source)['Surgical Emergency'],
                                                   self.category_probability.get(source)['Medical Emergency']]).item(0)

                    # Pick from a los distribution using the mean and sigma !! Assuming that LOS is log normal just while building, need to check this

                    if category == 'Elective':
                        los = int(np.random.lognormal(self.los_distributions.get(source)['Elective'][0],
                                                      self.los_distributions.get(source)['Elective'][1],
                                                      1).item(0))

                    elif category == 'Surgical Emergency':
                        los = int(np.random.lognormal(self.los_distributions.get(source)['Surgical Emergency'][0],
                                                      self.los_distributions.get(source)['Surgical Emergency'][1],
                                                      1).item(0))

                    elif category == 'Medical Emergency':
                        los = int(np.random.lognormal(self.los_distributions.get(source)['Medical Emergency'][0],
                                                      self.los_distributions.get(source)['Medical Emergency'][1],
                                                      1).item(0))

                elif source == 'Non-ED Admission':
                    category = np.random.choice(['Elective', 'Surgical Emergency', 'Medical Emergency'],
                                                1,
                                                p=[self.category_probability.get(source)['Elective'],
                                                   self.category_probability.get(source)['Surgical Emergency'],
                                                   self.category_probability.get(source)['Medical Emergency']]).item(0)

                    if category == 'Elective':
                        los = int(np.random.lognormal(self.los_distributions.get(source)['Elective'][0],
                                                      self.los_distributions.get(source)['Elective'][1],
                                                      1).item(0))

                    elif category == 'Surgical Emergency':
                        los = int(np.random.lognormal(self.los_distributions.get(source)['Surgical Emergency'][0],
                                                      self.los_distributions.get(source)['Surgical Emergency'][1],
                                                      1).item(0))

                    elif category == 'Medical Emergency':
                        los = int(np.random.lognormal(self.los_distributions.get(source)['Medical Emergency'][0],
                                                      self.los_distributions.get(source)['Medical Emergency'][1],
                                                      1).item(0))

                elif source == 'Elective':
                    # Waiting List patients will always be admitted as an Elective
                    category = 'Elective'
                    los = int(np.random.lognormal(self.los_distributions.get(source)['Elective'][0],
                                                  self.los_distributions.get(source)['Elective'][1],
                                                  1).item(0))

                # TODO: Suggestion, if patient_data was a dict (or dataclass?), we could reference parameters without relying on positioning
                patient_data = [patient_id, source, category, los, continuing_los]

                patients_data.append(patient_data)

        else:
            # TODO: This can be combined with the above section (pulling the source_ stuff out)
            if source_:

                for i in range(0, n):

                    patient_id, source, category, los, continuing_los = self.unique.next_counter(), None, None, None, 0

                    if source_=='Emergency Department':

                        source = 'Emergency Department'

                        category = np.random.choice(['Elective', 'Surgical Emergency', 'Medical Emergency'],
                                                    1,
                                                    p=[self.category_probability.get(source)['Elective'], # Don't think this needs to be in,
                                                       self.category_probability.get(source)['Surgical Emergency'],
                                                       self.category_probability.get(source)['Medical Emergency']]).item(0)

                        if category == 'Elective':
                            los = int(np.random.lognormal(self.los_distributions.get(source)['Elective'][0],
                                                          self.los_distributions.get(source)['Elective'][1],
                                                          1).item(0))

                        elif category == 'Surgical Emergency':
                            los = int(np.random.lognormal(self.los_distributions.get(source)['Surgical Emergency'][0],
                                                          self.los_distributions.get(source)['Surgical Emergency'][1],
                                                          1).item(0))

                        elif category == 'Medical Emergency':
                            los = int(np.random.lognormal(self.los_distributions.get(source)['Medical Emergency'][0],
                                                          self.los_distributions.get(source)['Medical Emergency'][1],
                                                          1).item(0))

                    elif source_=='Non-ED Admissions':

                        source = 'Non-ED Admissions'

                        category = np.random.choice(['Elective', 'Surgical Emergency', 'Medical Emergency'],
                                                    1,
                                                    p=[self.category_probability.get(source)['Elective'],
                                                       self.category_probability.get(source)['Surgical Emergency'],
                                                       self.category_probability.get(source)['Medical Emergency']]).item(0)

                        if category == 'Elective':
                            los = int(np.random.lognormal(self.los_distributions.get(source)['Elective'][0],
                                                          self.los_distributions.get(source)['Elective'][1],
                                                          1).item(0))

                        elif category == 'Surgical Emergency':
                            los = int(np.random.lognormal(self.los_distributions.get(source)['Surgical Emergency'][0],
                                                          self.los_distributions.get(source)['Surgical Emergency'][1],
                                                          1).item(0))

                        elif category == 'Medical Emergency':
                            los = int(np.random.lognormal(self.los_distributions.get(source)['Medical Emergency'][0],
                                                          self.los_distributions.get(source)['Medical Emergency'][1],
                                                          1).item(0))

                    elif source_=='Waiting List':

                        source = 'Waiting List'

                        category = np.random.choice(['Elective', 'Surgical Emergency', 'Medical Emergency'],
                                                    1,
                                                    p=[self.category_probability.get(source)['Elective'],
                                                       self.category_probability.get(source)['Surgical Emergency'],
                                                       self.category_probability.get(source)['Medical Emergency']]).item(0)

                        if category == 'Elective':
                            los = int(np.random.lognormal(self.los_distributions.get(source)['Elective'][0],
                                                          self.los_distributions.get(source)['Elective'][1],
                                                          1).item(0))

                        elif category == 'Surgical Emergency':
                            los = int(np.random.lognormal(self.los_distributions.get(source)['Surgical Emergency'][0],
                                                          self.los_distributions.get(source)['Surgical Emergency'][1],
                                                          1).item(0))

                        elif category == 'Medical Emergency':
                            los = int(np.random.lognormal(self.los_distributions.get(source)['Medical Emergency'][0],
                                                          self.los_distributions.get(source)['Medical Emergency'][1],
                                                          1).item(0))

                    patient_data = [patient_id, source, category, los, continuing_los]

                    patients_data.append(patient_data)

            else:
                raise Exception('A source has not been specified for the patient to be generated')

        return patients_data