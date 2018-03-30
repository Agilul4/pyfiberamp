from scipy.integrate import solve_bvp

from pyfiberamp.models.giles_model import GilesModel
from .boundary_conditions import BasicBoundaryConditions
from .helper_funcs import *
from .initial_guess_maker import InitialGuessMaker
from .channels import Channels
from .simulation_result import SimulationResult


class FiberAmplifierSimulation:
    """FiberAmplifierSimulation is the main class used for running Giles model simulations without Raman. The class
    defines the fiber, boundary conditions and optical channels used in the simulation."""
    def __init__(self, fiber):
        """
        Parameters
        ----------
        fiber : class instance derived from FiberBase
            The fiber used in the simulation.
        """
        self.fiber = fiber
        self.model = GilesModel
        self.boundary_conditions = BasicBoundaryConditions
        self.channels = Channels(fiber)
        self.slices = {}

    def add_cw_signal(self, wl, power, mode_field_diameter=0.0):
        """Adds a new forward propagating single-frequency CW signal to the simulation.
        Parameters
        ----------
        wl : float
            Wavelength of the signal
        power : float
            Input power of the signal at the beginning of the fiber
        mode_field_diameter : float (optional)
            Mode field diameter of the signal. If left undefined, will be calculated using the Petermann II equation.
        """
        self.channels.add_forward_signal(wl, power, mode_field_diameter)

    def add_forward_pump(self, wl, power, mode_field_diameter=0.0):
        """Adds a new forward propagating single-frequency pump to the simulation.
        Parameters
        ----------
        wl : float
            Wavelength of the pump
        power : float
            Input power of the pump a the beginning of the fiber
        mode_field_diameter : float (optional)
            Mode field diameter of the pump. If left undefined, will be calculated using the Petermann II equation.
        """
        self.channels.add_forward_pump(wl, power, mode_field_diameter)

    def add_backward_pump(self, wl, power, mode_field_diameter=0.0):
        """Adds a new backward propagating single-frequency pump to the simulation.
        Parameters
        ----------
        wl : float
            Wavelength of the pump
        power : float
            Input power of the pump a the beginning of the fiber
        mode_field_diameter : float (optional)
            Mode field diameter of the pump. If left undefined, will be calculated using the Petermann II equation.
        """
        self.channels.add_backward_pump(wl, power, mode_field_diameter)

    def add_ase(self, wl_start, wl_end, n_bins):
        """Adds amplified spontaneous emission (ASE) channels to the simulation.
        Parameters
        ----------
        wl_start : float
            The shortest wavelength of the ASE band
        wl_end : float
            The longest wavelength of the ASE band
        n_bins : float
            The number of simulated ASE channels. More channels improves accuracy, but incurs a heavier computational
            cost.
        """
        self.channels.add_ase(wl_start, wl_end, n_bins)

    def run(self, npoints=20, tol=1e-3):
        """Runs the simulation, i.e. calculates the steady state of the defined fiber amplifier.
        Paremeters
        ----------
        npoints : float
            Initial number of grid points used by the solver. Should be changed only if the solution does not
            converge.
        tol : float
            Target error tolerance of the solver. ASE or raman simulations might require higher tolerance than the
            default value. It is best to decrease the tolerance until the result no longer changes.
        """
        self._init_slices()

        boundary_condition_residual = self.boundary_conditions(self.channels)
        model = self.model(self.channels, self.fiber)
        rate_equation_rhs, upper_level_func = model.make_rate_equation_rhs()

        guess_maker = InitialGuessMaker(self.channels.get_input_powers(), self.slices, self._start_z(npoints))
        guess = guess_maker.make_guess()
        sol = solve_bvp(rate_equation_rhs, boundary_condition_residual,
                        self._start_z(npoints), guess, max_nodes=SOLVER_MAX_NODES, tol=tol, verbose=2)
        return self._finalize(sol, upper_level_func)

    def _start_z(self, npoints):
        """Creates the linear starting grid."""
        return np.linspace(0, self.fiber.length, npoints)

    def _finalize(self, sol, upper_level_func):
        """Creates the SimulationResult object from the solution object."""
        res = SimulationResult(sol)
        res.upper_level_fraction = upper_level_func(sol.y)
        res = self._add_wls_and_slices_to_result(res)
        return res

    def _init_slices(self):
        self.slices = self.channels.get_slices()

    def _add_wls_and_slices_to_result(self, res):
        res.slices = self.slices
        res.wavelengths = self.channels.get_wavelengths()
        res.is_passive_fiber = self.fiber.is_passive_fiber()
        return res




