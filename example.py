from pyiiod import EmulatedContext, EmulatedDevice, EmulatedTrigger, EmulatedChannel, iiod
import socketserver

g_amplitude = 100

# Example ADC generates a sinusoid with its amplitude controlled by a global variable
class MagicADC(EmulatedDevice):
	name = "magic-adc"
	attrs = {
		"sampling_frequency": 100
	}
	channels = {
		"voltage0": EmulatedChannel("le:s8/8>>0", output=False)
	}

	# Trigger-less operation - blocking
	def rx(self, nsamples):
		global g_amplitude
		for i in range(nsamples):
			t = time.time()
			x = int(g_amplitude * math.sin(t * 60))
			self.push_scan({
				"voltage0": x
			})
			time.sleep(1 / self.attrs["sampling_frequency"])

	# Triggered operation
	def handle_trigger(self):
		global g_amplitude
		t = time.time()
		x = int(g_amplitude * math.sin(t * 60))
		self.push_scan({
			"voltage0": x
		})

# Example DAC prints samples and stores them in a global variable ("wired to ADC")
class MagicDAC(EmulatedDevice):
	name = "magic-dac"
	attrs = {
		"sampling_frequency": 10
	}
	channels = {
		"voltage0": EmulatedChannel("le:u7/8>>0", output=True)
	}

	# Trigger-less operation - blocking
	def tx(self, buffers):
		global g_amplitude
		for sample in buffers["voltage0"]:
			print(f"DAC output: {sample}")
			g_amplitude = sample
			time.sleep(1 / self.attrs["sampling_frequency"])

# Example periodic trigger
class MagicTrigger(EmulatedTrigger):
	def __init__(self, period):
		self.period = period

	def start(self):
		self.timer = threading.Timer(self.period, self.tick)
		self.timer.start()

	def stop(self):
		self.timer.stop()

ctx = EmulatedContext(
	name="Magic emulated context",
	description="All IIO operations in this context are defined in Python",
	attrs={
		"context-attribute-1": "Hello, ",
		"context-attribute-2": "world!",
	},
	devices={
		"iio:device-0": MagicADC(),
		"iio:device-1": MagicDAC(),
		"trigger1": MagicTrigger(0.01)
	}
)
HOST = 'localhost'
PORT = 10101

with socketserver.ThreadingTCPServer((HOST, PORT), iiod(ctx)) as server:
		server.serve_forever()
