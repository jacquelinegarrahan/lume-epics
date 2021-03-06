import time
import logging
import threading
import multiprocessing
from typing import Dict, Mapping, Union, List

from threading import Thread, Event, local
from queue import Full, Empty

from lume_model.variables import Variable, InputVariable, OutputVariable
from lume_model.models import SurrogateModel
from .epics_pva_server import PVAServer
from .epics_ca_server import CAServer

logger = logging.getLogger(__name__)
multiprocessing.set_start_method("fork")


class Server:
    """
    Server for EPICS process variables. Can be optionally initialized with only
    pvAccess or Channel Access protocols; but, defaults to serving over both.

    Attributes:
        model (SurrogateModel): SurrogateModel class to be served

        input_variables (List[Variable]): List of lume-model variables passed to model.

        ouput_variables (List[Variable]): List of lume-model variables to use as
            outputs.

        ca_server (SimpleServer): Server class that interfaces between the Channel
            Access client and the driver.

        ca_driver (CADriver): Class used by server to handle to process variable
            read/write requests.

        pva_server (P4PServer): Threaded p4p server used for serving pvAccess
            variables.

        exit_event (Event): Threading exit event marking server shutdown.

    """

    def __init__(
        self,
        model_class: SurrogateModel,
        prefix: str,
        protocols: List[str] = ["pva", "ca"],
        model_kwargs: dict = {},
    ) -> None:
        """Create OnlineSurrogateModel instance in the main thread and
        initialize output variables by running with the input process variable
        state, input/output variable tracking, start the server, create the
        process variables, and start the driver.

        Args:
            model_class (SurrogateModel): Surrogate model class to be
            instantiated.

            prefix (str): Prefix used to format process variables.

            protocols (List[str]): List of protocols used to instantiate server.

            model_kwargs (dict): Kwargs to instantiate model.


        """
        # check protocol conditions
        if not protocols:
            raise ValueError("Protocol must be provided to start server.")

        if any([protocol not in ["ca", "pva"] for protocol in protocols]):
            raise ValueError(
                'Invalid protocol provided. Protocol options are "pva" '
                '(pvAccess) and "ca" (Channel Access).'
            )

        # need these to be global to access from threads
        self.prefix = prefix
        self.protocols = protocols

        self.model = model_class(**model_kwargs)
        self.input_variables = self.model.input_variables

        # update inputs for starting value to be the default
        for variable in self.input_variables.values():
            if variable.value is None:
                variable.value = variable.default

        model_input = list(self.input_variables.values())

        self.input_variables = self.model.input_variables
        self.output_variables = self.model.evaluate(model_input)
        self.output_variables = {
            variable.name: variable for variable in self.output_variables
        }

        self.in_queue = multiprocessing.Queue()
        self.out_queues = dict()
        for protocol in protocols:
            self.out_queues[protocol] = multiprocessing.Queue()

        self.exit_event = Event()

        self._running_indicator = multiprocessing.Value("b", False)

        # we use the running marker to make sure pvs + ca don't just keep adding queue elements
        self.comm_thread = threading.Thread(
            target=self.run_comm_thread,
            kwargs={
                "model_kwargs": model_kwargs,
                "in_queue": self.in_queue,
                "out_queues": self.out_queues,
                "running_indicator": self._running_indicator,
            },
        )

        # initialize channel access server
        if "ca" in protocols:
            self.ca_process = CAServer(
                prefix=self.prefix,
                input_variables=self.input_variables,
                output_variables=self.output_variables,
                in_queue=self.in_queue,
                out_queue=self.out_queues["ca"],
                running_indicator=self._running_indicator,
            )

        # initialize pvAccess server
        if "pva" in protocols:

            manager = multiprocessing.Manager()
            self._pva_conf = manager.dict()
            self.pva_process = PVAServer(
                prefix=self.prefix,
                input_variables=self.input_variables,
                output_variables=self.output_variables,
                in_queue=self.in_queue,
                out_queue=self.out_queues["pva"],
                conf_proxy=self._pva_conf,
                running_indicator=self._running_indicator,
            )

    def __enter__(self):
        """Handle server startup
        """
        self.start(monitor=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Handle server shutdown
        """
        self.stop()

    def run_comm_thread(
        self,
        *,
        running_indicator: multiprocessing.Value,
        model_kwargs={},
        in_queue: multiprocessing.Queue = None,
        out_queues: Dict[str, multiprocessing.Queue] = None,
    ):
        """Handles communications between pvAccess server, Channel Access server, and model.

        Arguments:
            model_class: Model class to be executed.

            model_kwargs (dict): Dictionary of model keyword arguments.

            in_queue (multiprocessing.Queue):

            out_queues (Dict[str: multiprocessing.Queue]): Maps protocol to output assignment queue.

            running_marker (multiprocessing.Value): multiprocessing marker for whether comm thread computing or not

        """
        model = self.model

        while not self.exit_event.is_set():
            try:

                data = in_queue.get(timeout=0.1)

                # mark running
                running_indicator.value = True

                for pv in data["pvs"]:
                    self.input_variables[pv].value = data["pvs"][pv]

                # sync pva/ca
                for protocol, queue in out_queues.items():
                    if protocol == data["protocol"]:
                        continue

                    queue.put(
                        {
                            "input_variables": [
                                self.input_variables[pv] for pv in data["pvs"]
                            ]
                        }
                    )

                # update output variable state
                model_input = list(self.input_variables.values())
                predicted_output = model.evaluate(model_input)
                for protocol, queue in out_queues.items():
                    queue.put({"output_variables": predicted_output}, timeout=0.1)

                running_indicator.value = False

            except Empty:
                continue

            except Full:
                logger.error(f"{protocol} queue is full.")

        logger.info("Stopping comm thread")

    def start(self, monitor: bool = True) -> None:
        """Starts server using set server protocol(s).

        Args:
            monitor (bool): Indicates whether to run the server in the background
                or to continually monitor. If monitor = False, the server must be
                explicitly stopped using server.stop()

        """
        self.comm_thread.start()

        if "ca" in self.protocols:
            self.ca_process.start()

        if "pva" in self.protocols:
            self.pva_process.start()

        if monitor:
            try:
                while True:
                    time.sleep(0.1)

            except KeyboardInterrupt:
                self.stop()

    def stop(self) -> None:
        """Stops the server.

        """
        logger.info("Stopping server.")
        self.exit_event.set()
        self.comm_thread.join()

        if "ca" in self.protocols:
            self.ca_process.shutdown()

        if "pva" in self.protocols:
            self.pva_process.shutdown()

        logger.info("Server is stopped.")
