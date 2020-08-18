from bokeh.io import curdoc
from bokeh import palettes
from bokeh.layouts import column, row
from bokeh.models import LinearColorMapper

from lume_epics.client.controller import Controller
from lume_model.utils import load_variables
from lume_epics.client.widgets.controls import build_sliders
from lume_epics.client.controller import Controller
from lume_epics.client.widgets.tables import ValueTable

prefix = "test"
variable_filename = "examples/keras/files/iris_variables.pickle"

# load variables
input_variables, output_variables = load_variables(variable_filename)

# use all input variables for slider
# prepare as list for rendering
input_variables = list(input_variables.values())

# set up controller
controller = Controller("ca") # can also use pvaccess

# build sliders
sliders = build_sliders(input_variables, controller, prefix)


output_variables = list(output_variables.values())


# extend the value table to update based on classification map of:
# class maps 0, 1, 2 to 'setosa', 'versicolor', 'virginica'
class ClassificationValueTable(ValueTable):

    classification_map = {
        0: "setosa",
        1: "versicolor",
        2: "virginica"
    }

    def update(self):
        """
        Callback function to update data source to reflect updated values.
        """
        for variable in self.pv_monitors:
            v = self.pv_monitors[variable].poll()
            self.output_values[variable] = self.classification_map[int(v)]

        x_vals = [self.labels[var] for var in self.output_values.keys()]
        y_vals = list(self.output_values.values())
        self.source.data = dict(x=x_vals, y=y_vals)


# class maps 0, 1, 2 to 'setosa', 'versicolor', 'virginica'
value_table =  ClassificationValueTable(output_variables, controller, prefix)


# render
curdoc().title = "Demo App"
curdoc().add_root(
            row(
                column([slider.bokeh_slider for slider in sliders], width=350), column(value_table.table)
                ) 
    )

curdoc().add_periodic_callback(value_table.update, 250)
for slider in sliders:
    curdoc().add_periodic_callback(slider.update, 250)
