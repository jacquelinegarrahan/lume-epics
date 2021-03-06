import subprocess
import numpy as np
import os
import logging
from lume_epics import epics_server
from lume_model.models import SurrogateModel
from lume_model.variables import *

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


class TestModel(SurrogateModel):
    input_variables = {
        "input1": ScalarInputVariable(name="input1", default=1.0, range=[0.0, 5.0]),
        "input2": ScalarInputVariable(
            name="input2", default=2.0, range=[0.0, 5.0], is_constant=True
        ),
        "input3": ImageInputVariable(
            name="input3",
            default=np.array([[1, 6,], [4, 1]]),
            value_range=[1, 10],
            axis_labels=["count_1", "count_2"],
            x_min=0,
            y_min=0,
            x_max=5,
            y_max=5,
        ),
        "input4": ArrayInputVariable(
            name="input4", default=np.array([1, 2]), range=[0, 5]
        ),
    }

    output_variables = {
        "output1": ScalarOutputVariable(name="output1"),
        "output2": ScalarOutputVariable(name="output2"),
        "output3": ImageOutputVariable(
            name="output3", axis_labels=["count_1", "count_2"],
        ),
        "output4": ArrayOutputVariable(name="output4"),
    }

    def evaluate(self, input_variables):
        self.input_variables = {variable.name: variable for variable in input_variables}

        self.output_variables["output1"].value = (
            self.input_variables["input1"].value * 2
        )
        self.output_variables["output2"].value = (
            self.input_variables["input2"].value * 2
        )

        self.output_variables["output3"].value = (
            self.input_variables["input3"].value * 2
        )
        self.output_variables["output3"].x_min = (
            self.input_variables["input3"].x_min / 2
        )
        self.output_variables["output3"].x_max = (
            self.input_variables["input3"].x_max / 2
        )
        self.output_variables["output3"].y_min = (
            self.input_variables["input3"].y_min / 2
        )
        self.output_variables["output3"].y_max = (
            self.input_variables["input3"].y_max / 2
        )
        self.output_variables["output3"].x_min = (
            self.input_variables["input3"].x_min / 2
        )
        self.output_variables["output3"].x_max = (
            self.input_variables["input3"].x_max / 2
        )
        self.output_variables["output3"].y_min = (
            self.input_variables["input3"].y_min / 2
        )
        self.output_variables["output3"].y_max = (
            self.input_variables["input3"].y_max / 2
        )

        self.output_variables["output4"].value = np.array(
            [
                self.output_variables["output1"].value,
                self.output_variables["output2"].value,
            ]
        )

        # return inputs * 2
        return list(self.output_variables.values())


if __name__ == "__main__":
    prefix = "test"
    server = epics_server.Server(TestModel, prefix)
    server.start(monitor=True)
