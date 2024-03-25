import pandas as pd


def record_occupied_beds(record_n_occupied_beds, occupied_elective_beds, occupied_surgical_emergency_beds,
                         occupied_medical_emergency_beds, occupied_escalation_beds):
    """

    :param record_n_occupied_beds:
    :param occupied_elective_beds:
    :param occupied_surgical_emergency_beds:
    :param occupied_medical_emergency_beds:
    :param occupied_escalation_beds:
    :return:
    """

    record_n_occupied_beds['Elective'].append(len(occupied_elective_beds))
    record_n_occupied_beds['surgical emergency'].append(len(occupied_surgical_emergency_beds))
    record_n_occupied_beds['medical emergency'].append(len(occupied_medical_emergency_beds))
    record_n_occupied_beds['escalation'].append(len(occupied_escalation_beds))


def calculate_outliers(occupied_medical_emergency_beds, occupied_surgical_emergency_beds, occupied_elective_beds,
                       record_n_outliers):
    """

    :param occupied_medical_emergency_beds:
    :param occupied_surgical_emergency_beds:
    :param occupied_elective_beds:
    :param record_n_outliers:
    :return:
    """

    elective_outliers = 0
    medical_outliers = 0
    surgical_outliers = 0

    for outlier in occupied_medical_emergency_beds:
        if outlier[2] == 'Elective':
            elective_outliers += 1
        elif outlier[2] == 'Surgical Emergency':
            surgical_outliers += 1

    for outlier in occupied_surgical_emergency_beds:
        if outlier[2] == 'Elective':
            elective_outliers += 1
        elif outlier[2] == 'Medical Emergency':
            medical_outliers += 1

    for outlier in occupied_elective_beds:
        if outlier[2] == 'Medical Emergency':
            medical_outliers += 1
        elif outlier[2] == 'Surgical Emergency':
            surgical_outliers += 1

    record_n_outliers['Elective'].append(elective_outliers)
    record_n_outliers['surgical emergency'].append(surgical_outliers)
    record_n_outliers['medical emergency'].append(medical_outliers)


def calculate_escalation(occupied_escalation_beds, record_n_escalation):
    """

    :param occupied_escalation_beds:
    :param record_n_escalation:
    :return:
    """
    if occupied_escalation_beds:
        record_n_escalation.append(len(occupied_escalation_beds))
    else:
        occupied_escalation_beds = []


def calculate_available_beds(record_available_beds, n_elective_beds, n_surgical_emergency_beds,
                             n_medical_emergency_beds, n_escalation_beds, occupied_elective_beds,
                             occupied_surgical_emergency_beds, occupied_medical_emergency_beds,
                             occupied_escalation_beds):
    """

    :param record_available_beds:
    :param n_elective_beds:
    :param n_surgical_emergency_beds:
    :param n_medical_emergency_beds:
    :param n_escalation_beds:
    :param occupied_elective_beds:
    :param occupied_surgical_emergency_beds:
    :param occupied_medical_emergency_beds:
    :param occupied_escalation_beds:
    :return:
    """
    record_available_beds['Elective'].append(n_elective_beds-len(occupied_elective_beds))
    record_available_beds['surgical emergency'].append(n_surgical_emergency_beds-len(occupied_surgical_emergency_beds))
    record_available_beds['medical emergency'].append(n_medical_emergency_beds-len(occupied_medical_emergency_beds))
    record_available_beds['escalation'].append(n_escalation_beds-len(occupied_escalation_beds)
                                               if n_escalation_beds-len(occupied_escalation_beds)
                                               else n_escalation_beds)


def collect_results(self):
    """
    This function should collect the results into a tabular format
    # TODO this function needs converting to a func within this .py file
    :return: a dataframe of results from the simulation
    """
    df = pd.DataFrame({
        'DateTime': self.time if self.time else None,
        'Run Name': self.run_name if self.run_name else None,

        'Available medical emergency': self.record_available_beds['medical emergency'],
        'Available surgical emergency': self.record_available_beds['surgical emergency'],
        'Available Elective': self.record_available_beds['Elective'],
        'Available escalation': self.record_available_beds['escalation'],

        'Occupied medical emergency': self.record_n_occupied_beds['medical emergency'],
        'Occupied surgical emergency': self.record_n_occupied_beds['surgical emergency'],
        'Occupied Elective': self.record_n_occupied_beds['Elective'],
        'Occupied escalation': self.record_n_occupied_beds['escalation'],

        'Medical Outliers': self.record_n_outliers['medical emergency'],
        'Surgical Outliers': self.record_n_outliers['surgical emergency'],
        'Elective Outliers': self.record_n_outliers['Elective'],

        'Escalation Beds Used': self.record_n_escalation,
        'Patients Admitted per Hour': self.record_n_admissions_by_hour,
        'Patients Discharged per Hour': self.record_n_discharges_by_hour,
        'Mean time waiting in ED': self.record_mean_ed_queue,
        'Mean time waiting in Non ED': self.record_mean_non_ed_queue,
        'Number of Trolley Waits (ED & Non ED)': self.record_n_trolley_waits,
        'Number of Elective Cancellations': self.record_n_cancellations
    })

    df['Medical Bed % Occ'] = df['Occupied medical emergency'] / df['Available medical emergency']
    df['Surgical Bed % Occ'] = df['Occupied surgical emergency'] / df['Available surgical emergency']
    df['Elective Bed % Occ'] = df['Occupied Elective'] / df['Available Elective']
    df['Escalation Bed % Occ'] = df['Occupied escalation'] / df['Available escalation']

    return df
