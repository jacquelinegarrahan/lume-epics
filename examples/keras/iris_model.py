"""
Adaptation of tensorflow tutorial: https://www.tensorflow.org/tutorials/estimator/premade
"""

from lume_model.models import SurrogateModel
from tensorflow import keras
from lume_model.variables import ScalarInputVariable, ScalarOutputVariable
import numpy as np

class IrisModel(SurrogateModel):

    input_variables = {
        'SepalLength': ScalarInputVariable(
            name = 'SepalLength',
            default = 4.3,
            range = [4.3, 7.9]
        ),
        "SepalWidth": ScalarInputVariable(
            name = "SepalWidth",
            default = 2.0,
            range = [2.0, 4.4]
        ),
       "PetalLength": ScalarInputVariable(
            name = 'PetalLength',
            default = 1.0,
            range = [1.0, 6.9]
        ),
       "PetalWidth": ScalarInputVariable(
            name = "PetalWidth",
            default = 0.1,
            range = [0.1, 2.5]
        ),

    }

    output_variables = {
        "Species": ScalarOutputVariable(
            name = "Species",
        )
    }

    def __init__(self, model_file=None):
        self.model_file = model_file
        self.model = keras.models.load_model(model_file)

    def evaluate(self, input_variables):
        self.input_variables = input_variables 
        vector = np.array([var.value for var in input_variables]).reshape(1, 4)

        output = list(self.model.predict(vector)[0])
        self.output_variables["Species"].value = output.index(max(output))
        return list(self.output_variables.values())
        
if __name__ == "__main__":
    from lume_model.utils import save_variables
    save_variables(IrisModel.input_variables, IrisModel.output_variables, "examples/keras/files/iris_variables.pickle")