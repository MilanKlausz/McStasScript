import sys
import os

import ipywidgets as widgets
from IPython.display import display

import matplotlib.pyplot as plt

from mcstasscript.interface.functions import name_search
from mcstasscript.interface import plotter
from mcstasscript.jb_interface import plot_interface
from mcstasscript.jb_interface.widget_helpers import HiddenPrints
from mcstasscript.jb_interface.widget_helpers import parameter_has_default
from mcstasscript.jb_interface.widget_helpers import get_parameter_default


class ParameterTextbox:
    def __init__(self, parameter, parameters):

        self.parameter = parameter
        self.parameters = parameters

        if parameter_has_default(parameter):
            self.default_value = get_parameter_default(parameter)
        else:
            self.default_value = ""

        self.name = parameter.name
        self.comment = parameter.comment

    def make_widget(self):
        label = widgets.Label(value=self.name,
                              layout=widgets.Layout(width='15%', height='32px'))
        textbox = widgets.Text(value=str(self.default_value),
                               layout=widgets.Layout(width='10%', height='32px'))
        comment = widgets.Label(value=self.comment,
                                layout=widgets.Layout(width='75%', height='32px'))

        textbox.observe(self.update, "value")

        return widgets.HBox([label, textbox, comment])

    def update(self, change):
        self.parameters[self.name] = change.new


class SimInterface:
    """
    Class for setting up widget that controls McStasScript instrument and plot
    """
    def __init__(self, instrument):
        """
        Sets up widget where the user can input instrument parameters, run the
        simulation, see plotted results and adjust the plots.

        The parameters of the instrument model are displayed with name, default
        value and comment. Can be adjusted with free text.

        A run button starts a simulation, and basic settings can be adjusted.

        A dropdown menu is available for selecting what monitor to view results
        from, and basic settings related to the plot can be adjusted.

        Show the interface with the show_interface method.

        Parameters
        ----------

        instrument: McStas_instr or McXtrace_instr
            instrument for which a widget should be created
        """

        self.instrument = instrument

        self.plot_interface = None

        self.run_button = None

        self.ncount = "1E6"
        self.mpi = "disabled"

        self.parameters = {}
        # get default parameters from instrument
        for parameter in self.instrument.parameter_list:
            if parameter_has_default(parameter):
                self.parameters[parameter.name] = get_parameter_default(parameter)

    def make_parameter_widgets(self):
        """
        Creates widgets for parameters using dedicated class ParameterTextbox
        Preliminary check for parameter type disabled as the ParameterVariable
        class does not set type for default case, will be fixed.

        returns widget including all parameters
        """
        parameter_widgets = []
        for parameter in self.instrument.parameter_list:
            if True: #parameter.type != "":
                par_widget = ParameterTextbox(parameter, self.parameters)
            else:
                raise RuntimeError("Unknown parameter type '"
                                   + parameter.type + "' of par named '"
                                   + parameter.name + "'.")

            parameter_widgets.append(par_widget.make_widget())

        return widgets.VBox(parameter_widgets)

    def run_simulation(self, change):
        """
        Performs the simulation with current parameters and settings.

        Changes icon on button to hourglass while simulation is running, then
        returns to calculator icon.

        Has dummy parameter change to allow the method to be used in on_click
        method of the run button.

        Parameters
        ----------

        change: widget change
            Not used
        """
        run_arguments = {"foldername": "interface",
                         "increment_folder_name": True,
                         "parameters": self.parameters,
                         "ncount": int(float(self.ncount))}
        if self.mpi != "disabled":
            run_arguments["mpi"] = self.mpi

        self.run_button.icon = "hourglass"
        print("Running with:", run_arguments)
        with HiddenPrints():
            data = self.instrument.run_full_instrument(**run_arguments)
        self.run_button.icon = "calculator"

        self.plot_interface.set_data(data)

    def make_run_button(self):
        """
        Creates a run button which perform the simulation
        """
        button = widgets.Button(
            description='Run',
            disabled=False,
            button_style='',  # 'success', 'info', 'warning', 'danger' or ''
            tooltip='Runs the simulation with current parameters',
            icon='calculator'  # (FontAwesome names without the `fa-` prefix)
        )
        button.on_click(self.run_simulation)
        return button

    def make_ncount_field(self):
        """
        Creates field for ncount, links to update_ncount

        The field supports scientific notation
        """
        description_layout = widgets.Layout(width='70px', height='32px',
                                            display="flex",
                                            justify_content="flex-end")
        description = widgets.Label(value="ncount", layout=description_layout)
        textbox = widgets.Text(value=str(self.ncount), layout=widgets.Layout(width='100px', height='32px'))
        textbox.observe(self.update_ncount, "value")

        return widgets.HBox([description, textbox])

    def update_ncount(self, change):
        """
        Updates ncount variable from textbox input

        Only updates when usable input is entered. Supports scientific
        notation in input through conversion to float

        Parameters
        ----------

        change: widget change
            state change of widget
        """
        try:
            self.ncount = int(float(change.new))
        except ValueError:
            pass

    def make_mpi_field(self):
        """
        Creates field for mpi, links to update_mpi
        """
        description_layout = widgets.Layout(width='40px', height='32px',
                                            display="flex",
                                            justify_content="flex-end")
        description = widgets.Label(value="mpi", layout=description_layout)
        textbox = widgets.Text(value=str(self.mpi), layout=widgets.Layout(width='70px', height='32px'))
        textbox.observe(self.update_mpi, "value")

        return widgets.HBox([description, textbox])

    def update_mpi(self, change):
        """
        Updates mpi value when integer or the word 'disabled' is given

        Parameters
        ----------

        change: widget change
            state change of widget
        """
        if change.new == "disabled":
            self.mpi = change.new

        try:
            self.mpi = int(change.new)
        except ValueError:
            pass

    def show_interface(self):
        """
        Builds and shows widget interface
        """

        # Make parameter controls
        parameter_widgets = self.make_parameter_widgets()

        # Make simulation controls
        self.run_button = self.make_run_button()
        ncount_field = self.make_ncount_field()
        mpi_field = self.make_mpi_field()

        simulation_widget = widgets.HBox([self.run_button, ncount_field, mpi_field],
                                         layout=widgets.Layout(border="solid"))

        self.plot_interface = plot_interface.PlotInterface()
        plot_widget = self.plot_interface.show_interface()

        return widgets.VBox([parameter_widgets, simulation_widget, plot_widget])



