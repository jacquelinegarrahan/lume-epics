
import flask
import logging
import numpy as np
import time
import requests

logger = logging.getLogger(__name__)

# initialize our Flask application and the Keras model
global online_model
app = flask.Flask(__name__)

@app.route("/evaluate", methods=["POST"])
def predict():
    # initialize the data dictionary that will be returned from the
    # view
    data = {"success": False, "output_variables":  None}

    # ensure an image was properly uploaded to our endpoint
    if flask.request.method == "POST":
        print(flask.request.json)


        for variable in flask.request.json:
            online_model.input_variables[variable].value = flask.request.json[variable]


        logger.info("Running model")
        t1 = time.time()
        output_variables = online_model.evaluate(online_model.input_variables)
        t2 = time.time()
        logger.info("Ellapsed time: %s", str(t2 - t1))

        # convert image values to list for jsonsification
        for variable in output_variables:
            if variable.variable_type == "image":
                variable.value = variable.value.tolist()

        # another hack for returning
        data["output_variables"] = {var.name: var.value for var in output_variables}

        # indicate that the request was a success
        data["success"] = True

    # return the data dictionary as a JSON response
    return flask.jsonify(data)

def flask_model_thread(model_class, port, model_kwargs={}):
    global online_model
    online_model = model_class(**model_kwargs)
    app.run(host='localhost', port=port)


def run_model(input_variables, output_variables, url):
    input_data = {var_name: variable.value for var_name, variable in input_variables.items()}
    payload = input_data
    # submit the request
    r = requests.post(url, json=payload)

    # ensure the request was successful
    if r.status_code == 200:
        print("Success")
        model_output = r.json()["output_variables"]

        for var in output_variables:
            if output_variables[var].variable_type == "image":
                output_variables[var].value =  np.array(model_output[var])

            else:
                output_variables[var].value =  model_output[var]

        return output_variables

    # otherwise, the request failed
    else:
        print("Request failed")
        return output_variables



if __name__ == "__main__":
   # import threading
    # don't need reloader, not in main thread
   # threading.Thread(target=model_thread, use_reloader=False)
    from examples.model import DemoModel
    from lume_model.utils import load_variables
    import threading

    variable_filename = "examples/variables.pickle"
    input_variables, output_variables = load_variables(variable_filename)

    model_kwargs = {"input_variables": input_variables, "output_variables": output_variables}
    model_thread = threading.Thread(target=flask_model_thread, args=(DemoModel,), kwargs={"model_kwargs": model_kwargs})
    model_thread.start()

    # import the necessary packages
    import requests
    KERAS_REST_API_URL = "http://localhost:5000/evaluate"

    input_data = {var_name: variable.value for var_name, variable in input_variables.items()}
    payload = input_data
    # submit the request
    r = requests.post(KERAS_REST_API_URL, json=payload)

    # ensure the request was successful
    if r.status_code == 200:
        # loop over the predictions and display them
    #  for (i, result) in enumerate(r["predictions"]):
    #     print("{}. {}: {:.4f}".format(i + 1, result["label"],
        #        result["probability"]))

        print("Success")
        print(r.json()["output_variables"])

    # otherwise, the request failed
    else:
        print("Request failed")