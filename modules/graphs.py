
import plotly.graph_objs as go


def graph_results(df, graph='occupied'):
    """
    This function should graphically show the results of the simulation
    :return:
    """
    data = df.collect_results()

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
