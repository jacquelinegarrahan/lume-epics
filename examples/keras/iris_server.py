from examples.keras.iris_model import IrisModel
from lume_epics.epics_server import Server

prefix = "test"
server = Server(
    IrisModel, 
    IrisModel.input_variables, 
    IrisModel.output_variables, 
    prefix,
    model_kwargs={"model_file": "examples/keras/files/iris_model.h5"}
)

server.start(monitor=True)