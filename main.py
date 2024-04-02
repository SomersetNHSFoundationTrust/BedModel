from datetime import timedelta
import pandas as pd
import numpy as np
from BedModel.modules import Unique
import plotly.graph_objects as go


class BedModel:
    """
    Generalised Inpatient Bed Model

    Example:

    warmup_n = 574

    source_prob = {"Emergency Department": 0.8, "Non-ED Admissions": 0.14, "Waiting List": 0.06}

    category_prob = {"Emergency Department": {'Elective':0, 'Surgical Emergency':0.2, 'Medical Emergency':0.8},
                 "Non-ED Admission": {'Elective':0, 'Surgical Emergency':0.4, 'Medical Emergency':0.6}
                 }

    los_distributions = {
        'Emergency Department': {'Elective': (1, 0.5), 'Surgical Emergency': (2, 0.7), 'Medical Emergency': (3, 1)},
        'Non-ED Admission': {'Elective': (1.5, 0.6), 'Surgical Emergency': (2.5, 0.8), 'Medical Emergency': (3.5, 1.2)},
        'Elective': {'Elective': (2, 0.7)}
    }

    hospital = BedModel(n_elective_beds=40,
                        n_surgical_emergency_beds=150,
                        n_medical_emergency_beds=450,
                        n_escalation_beds=20,
                        source_probability=source_prob,
                        category_probability=category_prob,
                        los_distributions=los_distributions)

    hospital.warm_up_model(warmup_number=warmup_n)

    """
    def __init__(self, n_elective_beds, n_surgical_emergency_beds, n_medical_emergency_beds, n_escalation_beds, source_probability, category_probability, los_distributions, time_matrix):
        """

        :param n_elective_beds:
        :param n_surgical_emergency_beds:
        :param n_medical_emergency_beds:
        :param n_escalation_beds:
        :param source_probability:
        :param category_probability:
        :param los_distributions:
        :param time_matrix:
        """
        # Total Beds
        self.n_elective_beds = n_elective_beds # ? can these four use a dictionary to reduce n parameters
        self.n_surgical_emergency_beds = n_surgical_emergency_beds
        self.n_medical_emergency_beds = n_medical_emergency_beds
        self.n_escalation_beds = n_escalation_beds

        # Global Variables
        self.los_distributions = los_distributions
        self.category_probability = category_probability
        self.source_probability = source_probability
        self.time_matrix = time_matrix
        self.time = []
        self.run_name = []

        # Beds occupied
        self.occupied_elective_beds = []
        self.occupied_surgical_emergency_beds = []
        self.occupied_medical_emergency_beds = []
        self.occupied_escalation_beds = []

        # All Patients
        self.patient_master = [] # A master holding place for the warm-up patients so that it can be replicated each run
        self.unique = None

        # Holding Places
        self.ed_queue = [] # If an emergency patient they wait here (trolley wait)
        self.non_ed_queue = [] # If an emergency patient they wait here
        self.Elective_queue = [] # If an Elective patient they wait here

        # Metrics
        self.Elective_cancellations = [] # If a patient from the Waiting List cannot be admitted they are cancelled
        self.record_available_beds = {'Elective': [], 'surgical emergency': [], 'medical emergency': [], 'escalation': []}
        self.record_n_occupied_beds = {'Elective': [], 'surgical emergency': [], 'medical emergency': [], 'escalation': []}
        self.record_n_outliers = {'Elective': [], 'surgical emergency': [], 'medical emergency': []}
        self.record_n_escalation = []
        self.record_n_admissions_by_hour = []
        self.record_n_discharges_by_hour = []
        self.record_mean_length_of_stay = [] # wondering if there is any use in recording this
        self.record_mean_ed_queue = []
        self.record_mean_non_ed_queue = []
        self.record_n_trolley_waits = []
        self.record_n_cancellations = []


    # Tools

    # These functions are used as tools throughout the model

    def patient_generator(self, n, warm=False, source_=None):
        """
        Create stochastic patients based on probability and distributions
        :param source_: the type of patient to generate
        :param warm: whether to generate from warmup
        :param n: Number of patients to generate
        :return: patients to patient_master
        """
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

                self.patient_master.append(patient_data)

        else:
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

                    # TODO: This will return on the first iteration, check that this is desired.
                    return patient_data

            else:
                raise Exception('A source has not been specified for the patient to be generated')



    # This function acts as a warm-up, setting the starting figures in the simulation, so it does not begin with an empty system

    def warm_up_model(self, warmup_number):
        """

        :param warmup_number: Number of patients to be generated at warm up
        :return:
        """

        self.unique = Unique()

        if warmup_number > self.n_surgical_emergency_beds + self.n_elective_beds + self.n_medical_emergency_beds + self.n_escalation_beds:
            raise ValueError("The number of patients at warm-up cannot exceed the beds available")

        else:
            self.patient_generator(n=warmup_number, warm=True)

        # Admit patients
        self.admit_patient(warm=True)


    # Core Functions

    # All these functions are used in the running of the simulation

    def discharge_patient(self):
        """
        This function should store the number of patients ready for discharge and then remove them from the system
        :return: number of discharges to self.record_n_discharges_by_hour
        """

        discharged = 0

        if len(self.occupied_medical_emergency_beds) > 0:

            discharged += len([sublist for sublist in self.occupied_medical_emergency_beds if sublist[3] == 0])
            self.occupied_medical_emergency_beds = [sublist for sublist in self.occupied_medical_emergency_beds if sublist[3] != 0]

        if len(self.occupied_surgical_emergency_beds) > 0:
            discharged += len([sublist for sublist in self.occupied_surgical_emergency_beds if sublist[3] == 0])
            self.occupied_surgical_emergency_beds = [sublist for sublist in self.occupied_surgical_emergency_beds if sublist[3] != 0]

        if len(self.occupied_elective_beds) > 0:
            discharged += len([sublist for sublist in self.occupied_elective_beds if sublist[3] == 0])
            self.occupied_elective_beds = [sublist for sublist in self.occupied_elective_beds if sublist[3] != 0]

        if len(self.occupied_escalation_beds) > 0:
            discharged += len([sublist for sublist in self.occupied_escalation_beds if sublist[3] == 0])
            self.occupied_escalation_beds = [sublist for sublist in self.occupied_escalation_beds if sublist[3] != 0]

        self.record_n_discharges_by_hour.append(discharged)


    def cancel_patient(self):
        """
        This function should add any patients left in the Elective queue but where there are no beds
        :return: updates self.Elective_cancellations and self.Elective_queue
        """

        self.Elective_cancellations.append(len(self.Elective_queue))
        # Clear all remaining Electives in the queue
        self.Elective_queue.clear()

    def update_los(self):
        """
        update the los parameters held in the occupied bed areas

        !! should also handle updating those in the holding areas
        :return:
        """
        reduce = lambda los : los - 1
        increase = lambda los : los + 1

        if len(self.occupied_medical_emergency_beds)>0:

            for patient in self.occupied_medical_emergency_beds:
                patient[3] = reduce(patient[3])
                patient[4] = increase(patient[4])

        if len(self.occupied_surgical_emergency_beds)>0:
            for patient in self.occupied_surgical_emergency_beds:
                patient[3] = reduce(patient[3])
                patient[4] = increase(patient[4])

        if len(self.occupied_elective_beds)>0:
            for patient in self.occupied_elective_beds:
                patient[3] = reduce(patient[3])
                patient[4] = increase(patient[4])

        if len(self.occupied_escalation_beds)>0:
            for patient in self.occupied_escalation_beds:
                patient[3] = reduce(patient[3])
                patient[4] = increase(patient[4])

        #Update those waiting in the holding areas
        #Do not update the LOS until they are admitted

        # TODO when patient is admitted they should have their LOS in idx[4] reset

        if len(self.ed_queue)>0:
            for patient in self.ed_queue:
                patient[4] = increase(patient[4])

        if len(self.non_ed_queue)>0:
            for patient in self.non_ed_queue:
                patient[4] = increase(patient[4])


    def admit_patient(self, warm):
        """
        This function should admit patients from the holding areas
        :return:
        """

        if warm:
            for patient in self.patient_master:
                # Prioritise the placement of emergency patients

                if (patient[2] == 'Medical Emergency'
                        and len(self.occupied_medical_emergency_beds) < self.n_medical_emergency_beds):
                    self.occupied_medical_emergency_beds.append(patient)

                # If this is not possible place the patients in surgical beds
                elif (patient[2] == 'Medical Emergency'
                      and len(self.occupied_medical_emergency_beds) >= self.n_medical_emergency_beds
                      and len(self.occupied_surgical_emergency_beds) < self.n_surgical_emergency_beds):
                    self.occupied_surgical_emergency_beds.append(patient)

                elif (patient[2] == 'Surgical Emergency'
                      and len(self.occupied_surgical_emergency_beds) < self.n_surgical_emergency_beds):
                    self.occupied_surgical_emergency_beds.append(patient)

                elif (patient[2] == 'Surgical Emergency'
                      and len(self.occupied_surgical_emergency_beds) >= self.n_surgical_emergency_beds
                      and len(self.occupied_medical_emergency_beds) < self.n_medical_emergency_beds):
                    self.occupied_medical_emergency_beds.append(patient)

                elif (patient[2] == 'Elective'
                      and len(self.occupied_elective_beds) < self.n_elective_beds):
                    self.occupied_elective_beds.append(patient)

                elif (patient[2] == 'Elective'
                      and len(self.occupied_elective_beds) >= self.n_elective_beds
                      and len(self.occupied_surgical_emergency_beds) < self.n_surgical_emergency_beds):
                    self.occupied_surgical_emergency_beds.append(patient)

                elif (patient[2] == 'Elective'
                      and len(self.occupied_elective_beds) >= self.n_elective_beds
                      and len(self.occupied_medical_emergency_beds) < self.n_medical_emergency_beds):
                    self.occupied_medical_emergency_beds.append(patient)

                # If patient cannot fit within the core bed base then use escalation beds
                else:
                    self.occupied_escalation_beds.append(patient)

        else:
            category_pathways = {
                "Medical Emergency": self.__handle_medical_emergency,
                "Surgical Emergency": self.__handle_surgical_emergency,
                "Elective": self.__handle_elective,
            }

            # TODO: if this logic is correct, it could be applied to the warmup section too
            for category, pathway in category_pathways.items():
                for queue in [self.ed_queue, self.non_ed_queue, self.Elective_queue]:
                    patients_in_beds = []
                    for patient_index, patient in enumerate(queue):
                        if patient[2] == category:
                            if pathway(patient):
                                patients_in_beds.append(patient_index)

                    # Remove the patients in beds from the queue
                    for patient_index in patients_in_beds[::-1]:
                        del queue[patient_index]


    def __handle_medical_emergency(self, patient):
        """
        This method assigns the provided patient to an available bed according to the severity of the medical emergency.
        It prioritizes assigning the patient to medical emergency beds, then surgical emergency beds, and finally escalation beds
        if all medical and surgical emergency beds are occupied.
        :param patient: a list containing information pertinent to the patient
        :return bool: whether the patient could get a bed
        """
        patient_in_bed = True
        if len(self.occupied_medical_emergency_beds) < self.n_medical_emergency_beds:
            self.occupied_medical_emergency_beds.append(patient)
        elif len(self.occupied_surgical_emergency_beds) < self.n_surgical_emergency_beds:
            self.occupied_surgical_emergency_beds.append(patient)
        elif len(self.occupied_escalation_beds) < self.n_escalation_beds:
            self.occupied_escalation_beds.append(patient)
        else:
            patient_in_bed = False

        return patient_in_bed


    def __handle_surgical_emergency(self, patient):
        """
        This method assigns the provided patient to an available bed according to the severity of the surgical emergency.
        It prioritizes assigning the patient to surgical emergency beds, then medical emergency beds, and finally escalation beds
        if all medical and surgical emergency beds are occupied.
        :param patient: a list containing information pertinent to the patient.
        :return bool: whether the patient could get a bed
        """
        patient_in_bed = True
        if len(self.occupied_surgical_emergency_beds) < self.n_surgical_emergency_beds:
            self.occupied_surgical_emergency_beds.append(patient)
        elif len(self.occupied_medical_emergency_beds) < self.n_medical_emergency_beds:
            self.occupied_medical_emergency_beds.append(patient)
        elif len(self.occupied_escalation_beds) < self.n_escalation_beds:
            self.occupied_escalation_beds.append(patient)
        else:
            patient_in_bed = False

        return patient_in_bed

    def __handle_elective(self, patient):
        """
        This method assigns the provided patient to an available bed, considering the priority of elective treatments.
        It first attempts to assign the patient to elective beds. If all elective beds are occupied, it checks if there
        are any available surgical emergency beds, followed by medical emergency beds, and finally escalation beds.
        :param patient: a list containing information pertinent to the patient.
        :return bool: whether the patient could get a bed
        """
        patient_in_bed = True
        if len(self.occupied_elective_beds) < self.n_elective_beds:
            self.occupied_elective_beds.append(patient)
        # TODO: Check this logic - would the elective not just be cancelled? Since this goes down an unsorted list we could be filling non-emergency patients in emergency slots
        elif len(self.occupied_surgical_emergency_beds) < self.n_surgical_emergency_beds:
            self.occupied_surgical_emergency_beds.append(patient)
        elif len(self.occupied_medical_emergency_beds) < self.n_medical_emergency_beds:
            self.occupied_medical_emergency_beds.append(patient)
        elif len(self.occupied_escalation_beds) < self.n_escalation_beds:
            self.occupied_escalation_beds.append(patient)
        else:
            patient_in_bed = False

        return patient_in_bed


    def arrivals(self, hour, weekday):
        """
        This function handles generating the new arrivals each hour and puts them in the holding area ready for the admit function
        :return:
        """

        number_being_admitted_emergency_department = self.time_matrix.get('Emergency Department')[weekday][hour]
        number_being_admitted_non_emergency_department = self.time_matrix.get('Non-ED Admission')[weekday][hour]
        number_being_admitted_n_elective = self.time_matrix.get('Elective')[weekday][hour]

        if number_being_admitted_emergency_department:

            new = self.patient_generator(n=number_being_admitted_emergency_department, source_='Emergency Department')

            self.ed_queue.append(new)

        if number_being_admitted_non_emergency_department:

            # TODO: is this source correct?
            new = self.patient_generator(n=number_being_admitted_emergency_department, source_='Elective')

            # TODO: Should this be non_ed_queue?
            self.ed_queue.append(new)

        if number_being_admitted_n_elective:

            new = self.patient_generator(n=number_being_admitted_emergency_department, source_='Elective')

            # TODO: Should this be Elective_queue?
            self.ed_queue.append(new)


    # End Results

    # These functions are used to record the end results of the model and graphically show them

    def collect_results(self):
        """
        This function should collect the results into a tabular format

        :return: a dataframe of results from the simulation
        """
        df = pd.DataFrame({
            'DateTime': self.time if self.time else None,
            'Run Name': self.run_name if self.run_name else None,

            'Available medical emergency': self.record_available_beds['medical emergency'],
            'Available surgical emergency': self.record_available_beds['surgical emergency'],
            'Available Elective': self.record_available_beds['Elective'],
            'Available escalation': self.record_available_beds['escalation'],

            'Occupied medical emergency': self.record_n_occupied_beds['medical emergency'] if self.record_n_occupied_beds['medical emergency'] else None,
            'Occupied surgical emergency': self.record_n_occupied_beds['surgical emergency'] if self.record_n_occupied_beds['surgical emergency'] else None,
            'Occupied Elective': self.record_n_occupied_beds['Elective'] if self.record_n_occupied_beds['Elective'] else None,
            'Occupied escalation': self.record_n_occupied_beds['escalation'] if self.record_n_occupied_beds['escalation'] else None,

            'Medical Outliers': self.record_n_outliers['medical emergency'] if self.record_n_outliers['medical emergency'] else None,
            'Surgical Outliers': self.record_n_outliers['surgical emergency'] if self.record_n_outliers['surgical emergency'] else None,
            'Elective Outliers': self.record_n_outliers['Elective'] if self.record_n_outliers['Elective'] else None,

            'Escalation Beds Used': self.record_n_escalation if self.record_n_escalation else None,
            'Patients Admitted per Hour': self.record_n_admissions_by_hour if self.record_n_admissions_by_hour else None,
            'Patients Discharged per Hour': self.record_n_discharges_by_hour if self.record_n_discharges_by_hour else None,
            'Mean time waiting in ED': self.record_mean_ed_queue if self.record_mean_ed_queue else None,
            'Mean time waiting in Non ED': self.record_mean_non_ed_queue if self.record_mean_non_ed_queue else None,
            'Number of Trolley Waits (ED & Non ED)': self.record_n_trolley_waits if self.record_n_trolley_waits else None,
            'Number of Elective Cancellations': self.record_n_cancellations if self.record_n_cancellations else None
        })

        df['Medical Bed % Occ'] = df['Occupied medical emergency'] / df['Available medical emergency']
        df['Surgical Bed % Occ'] = df['Occupied surgical emergency'] / df['Available surgical emergency']
        df['Elective Bed % Occ'] = df['Occupied Elective'] / df['Available Elective']
        df['Escalation Bed % Occ'] = df['Occupied escalation'] /df['Available escalation']

        return df


    def graph_results(self, graph='occupied'):
        """
        This function should graphically show the results of the simulation
        :return:
        """
        data = self.collect_results()

        run_names = data['Run Name'].unique()

        if graph == 'occupied':
            fig = go.Figure()

            for i in run_names:

                fig.add_trace(go.Scatter(x=data[data['Run Name']==i]['DateTime'],
                                         y=data[data['Run Name']==i]['Occupied medical emergency'],
                                         name='Occupied Medical Emergency Beds'))

                fig.add_trace(go.Scatter(x=data[data['Run Name']==i]['DateTime'],
                                         y=data[data['Run Name']==i]['Occupied surgical emergency'],
                                         name='Occupied Surgical Emergency Beds'))

                fig.add_trace(go.Scatter(x=data[data['Run Name']==i]['DateTime'],
                                         y=data[data['Run Name']==i]['Occupied Elective'],
                                         name='Occupied Elective Beds'))

                fig.add_trace(go.Scatter(x=data[data['Run Name']==i]['DateTime'],
                                         y=data[data['Run Name']==i]['Occupied escalation'],
                                         name='Occupied Escalation Beds'))

            fig.update_layout(margin=dict(t=10,l=10,r=10,b=10), template='seaborn')



            return fig

    # Main Function

    # This is the core function called to run the simulation (after set up and warm up)

    def simulate_inpatient_system(self, start_time, end_time, runs=100):
        """

        :param start_time: datetime for when the simulation should start
        :param end_time: datetime for when the simulation should end
        :param runs: the number of runs that should be executed to collect results, default: 100 runs
        :return:
        """

        for i in range(runs):

            # TODO remove this  when the patient generator has been split to the module
            self.unique = Unique()

            current_time = start_time

            while current_time <= end_time:

                self.time.append(current_time)
                self.run_name.append('Run_' + str(i))

                # Update all the LOSs ready for calculations
                self.update_los()

                # Discharge any patients that have reached the end of their LOS
                self.discharge_patient()

                # Calculate the new arrivals
                self.arrivals(hour=current_time.hour,
                              weekday=current_time.strftime('%A'))

                # Admit those patients
                self.admit_patient(warm=False)

                # Begin Recording

                record_occupied_beds(record_n_occupied_beds = self.record_n_occupied_beds,
                                     occupied_elective_beds=self.occupied_elective_beds,
                                     occupied_surgical_emergency_beds = self.occupied_surgical_emergency_beds,
                                     occupied_medical_emergency_beds = self.occupied_medical_emergency_beds,
                                     occupied_escalation_beds=self.occupied_escalation_beds)

                calculate_available_beds(record_available_beds=self.record_available_beds,
                                         n_elective_beds=self.n_elective_beds,
                                         n_surgical_emergency_beds=self.n_surgical_emergency_beds,
                                         n_medical_emergency_beds=self.n_medical_emergency_beds,
                                         n_escalation_beds=self.n_escalation_beds,
                                         occupied_elective_beds=self.occupied_elective_beds,
                                         occupied_surgical_emergency_beds=self.occupied_surgical_emergency_beds,
                                         occupied_medical_emergency_beds=self.occupied_medical_emergency_beds,
                                         occupied_escalation_beds=self.occupied_escalation_beds)


                self.cancel_patient()

                calculate_outliers(occupied_medical_emergency_beds=self.occupied_medical_emergency_beds,
                                   occupied_surgical_emergency_beds=self.occupied_surgical_emergency_beds,
                                   occupied_elective_beds=self.occupied_elective_beds,
                                   record_n_outliers=self.record_n_outliers)

                calculate_escalation(occupied_escalation_beds=self.occupied_escalation_beds,
                                     record_n_escalation=self.record_n_escalation)


                current_time += timedelta(hours=1)

