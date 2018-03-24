from .helper_funcs import *


DEFAULT_GUESS_PARAMS = {
    'signal_conversion_guess': 0.5,
    'signal_gain_shape': 'linear',
    'pump_absorption_factor': 0.01,
    'ase_output_power': 1e-3
}


class InitialGuessMaker:
    def __init__(self, input_powers, slices, z, params=DEFAULT_GUESS_PARAMS):
        self.input_powers = input_powers
        self.signal_powers = input_powers[slices['signal_slice']]
        self.co_pump_powers = input_powers[slices['co_pump_slice']]
        self.counter_pump_powers = input_powers[slices['counter_pump_slice']]
        self.forward_ase_powers = input_powers[slices['forward_ase_slice']]
        self.backward_ase_powers = input_powers[slices['backward_ase_slice']]
        self.forward_raman_powers = input_powers[slices['forward_raman_slice']]
        self.backward_raman_powers = input_powers[slices['backward_raman_slice']]

        self.slices = slices
        self.z = z
        self.params = params

    def guess_shape(self):
        return len(self.input_powers), len(self.z)

    def make_guess(self, ):
        guess = np.zeros(self.guess_shape())
        guess[self.slices['signal_slice']] = self.make_signal_guess()
        guess[self.slices['co_pump_slice']] = self.make_co_pump_guess()
        guess[self.slices['counter_pump_slice']] = self.make_counter_pump_guess()
        guess[self.slices['forward_ase_slice']] = self.make_forward_ase_guess()
        guess[self.slices['backward_ase_slice']] = self.make_backward_ase_guess()
        guess[self.slices['forward_raman_slice']] = self.make_forward_raman_guess()
        guess[self.slices['backward_raman_slice']] = self.make_backward_raman_guess()
        return guess

    def make_signal_guess(self):
        total_pump_power = np.sum(self.co_pump_powers) + np.sum(self.counter_pump_powers)
        signal_start = self.signal_powers
        signal_end = self.params['signal_conversion_guess'] * total_pump_power + signal_start
        signal_gain_shape = self.params['signal_gain_shape']
        if signal_gain_shape == 'linear':
            guess = self.linear_guess(signal_start, signal_end)
        elif signal_gain_shape == 'exponential':
            guess = self.exponential_guess(signal_start, signal_end)
        else:
            raise RuntimeError('Unrecognized signal gain shape parameter.')
        return guess

    def make_co_pump_guess(self):
        co_pump_start = self.co_pump_powers
        co_pump_end = self.params['pump_absorption_factor'] * co_pump_start
        return self.linear_guess(co_pump_start, co_pump_end)

    def make_counter_pump_guess(self):
        counter_pump_start = self.params['pump_absorption_factor'] * self.counter_pump_powers
        counter_pump_end = self.counter_pump_powers
        return self.linear_guess(counter_pump_start, counter_pump_end)

    def make_forward_ase_guess(self):
        forward_ase_start = self.forward_ase_powers
        forward_ase_end = np.full_like(forward_ase_start, self.params['ase_output_power'])
        return self.linear_guess(forward_ase_start, forward_ase_end)

    def make_backward_ase_guess(self):
        backward_ase_end = self.backward_ase_powers
        backward_ase_start = np.full_like(backward_ase_end, self.params['ase_output_power'])
        return self.linear_guess(backward_ase_start, backward_ase_end)

    def make_forward_raman_guess(self):
        forward_raman_start = self.forward_raman_powers
        forward_raman_end = self.forward_raman_powers * 2
        return self.linear_guess(forward_raman_start, forward_raman_end)

    def make_backward_raman_guess(self):
        backward_raman_start = self.backward_raman_powers
        backward_raman_end = self.backward_raman_powers
        return self.linear_guess(backward_raman_start, backward_raman_end)

    def linear_guess(self, start, end):
        return linspace_2d(start, end, len(self.z))

    def exponential_guess(self, start, end):
        start = start[:, np.newaxis]
        end = end[:, np.newaxis]
        gain = np.log(end / start) / self.z[-1]
        return start * np.exp(gain * self.z)


