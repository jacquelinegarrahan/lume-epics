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
variable_filename = "examples/keras/files/variables.pickle"

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

value_table = ValueTable(output_variables, controller, prefix)


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
