import iio
import threading

def sanitize_xml(string):
	string = str(string)
	string = string.replace('&', '&amp;')
	string = string.replace('<', '&lt;')
	string = string.replace('>', '&gt;')
	string = string.replace('\'', '&apos;')
	string = string.replace('"', '&quot;')
	return string

class EmulatedContext(iio.Context):
	def __init__(self):
		self._attrs = {}
		self._name = "emulated"
		self._description = "Emulated Context"
		self._version = (0, 1, "testing")

	def __del__(self):
		pass

	def set_timeout(self, timeout):
		raise NotImplementedError()

	def clone(self):
		raise NotImplementedError()

	def find_device(self, name_or_id_or_label):
		raise NotImplementedError()

	devices = property(
		lambda self: [],
		None,
		None,
		"List of devices contained in this context.\n\ttype=list of iio.Device and iio.Trigger objects",
	)

	@property
	def xml(self):
		xml = "<?xml version=\"1.0\" encoding=\"utf-8\"?>" + \
		"<!DOCTYPE context [" + \
		"<!ELEMENT context (device | context-attribute)*>" + \
		"<!ELEMENT context-attribute EMPTY>" + \
		"<!ELEMENT device (channel | attribute | debug-attribute | buffer-attribute)*>" + \
		"<!ELEMENT channel (scan-element?, attribute*)>" + \
		"<!ELEMENT attribute EMPTY>" + \
		"<!ELEMENT scan-element EMPTY>" + \
		"<!ELEMENT debug-attribute EMPTY>" + \
		"<!ELEMENT buffer-attribute EMPTY>" +  \
		"<!ATTLIST context name CDATA #REQUIRED version-major CDATA #REQUIRED " + \
		"version-minor CDATA #REQUIRED version-git CDATA #REQUIRED description CDATA #IMPLIED>" + \
		"<!ATTLIST context-attribute name CDATA #REQUIRED value CDATA #REQUIRED>" + \
		"<!ATTLIST device id CDATA #REQUIRED name CDATA #IMPLIED label CDATA #IMPLIED>" + \
		"<!ATTLIST channel id CDATA #REQUIRED type (input|output) #REQUIRED name CDATA #IMPLIED>" + \
		"<!ATTLIST scan-element index CDATA #REQUIRED format CDATA #REQUIRED scale CDATA #IMPLIED>" + \
		"<!ATTLIST attribute name CDATA #REQUIRED filename CDATA #IMPLIED>" + \
		"<!ATTLIST debug-attribute name CDATA #REQUIRED>" + \
		"<!ATTLIST buffer-attribute name CDATA #REQUIRED>" + \
		"]>"

		xml += f'<context name="{sanitize_xml(self._name)}"'
		xml += f' version-major="{sanitize_xml(self._version[0])}"'
		xml += f' version-minor="{sanitize_xml(self._version[1])}"'
		xml += f' version-git="{sanitize_xml(self._version[2])}"'
		if self._description:
			xml += f' description="{sanitize_xml(self._description)}"'
		xml += '>'

		for attr in self._attrs:
			xml += f'<context-attribute name="{sanitize_xml(attr)}" value="{sanitize_xml(self._attrs[attr].value)}" />'

		for i, (name, device) in enumerate(self.devices.items()):
			xml += f'<device id="iio:device{i}"'
			if device.name:
				xml += f' name="{sanitize_xml(device.name)}"'
			if device.label:
				xml += f' label="{sanitize_xml(device.label)}"'
			xml += '>'
			
			xml += '</device>'

		xml += '</context>'

		return xml

class EmulatedDevice(iio.Device):
	pass


def iiod(ctx):
	class RWThread(threading.Thread):
		class WaitingBuffer:
			def __init__(self):
				self.chunks = []
				self.evt = threading.Event()

			def get_chunk(self):
				self.evt.wait()
				chunk = self.chunks.pop(0)
				if not self.chunks:
					self.evt.clear()
				return chunk

		def __init__(self, *args, **kwargs):
			super().__init__(*args, **kwargs)
			self.recvlist = set()

		def run(self, *args):
			self.running = True
			while self.running:
				


		def stop(self):
			self.running = False

		def start_read(self, nbytes):
			wb = WaitingBuffer(nbytes)
			self.recvlist.add(wb)
			return wb

		def write(self, data):
			raise NotImplementedError()

	def iiod_open(device, samples_count, mask, cyclic):
		pass

	def iiod_close(device):
		pass

	def iiod_readbuf_chunks(device, nbytes):
		waiting_buffer = rwthreads[device].start_read(nbytes)
		while nbytes > 0:
			chunk = waiting_buffer.get_chunk()
			nbytes -= len(chunk)
			yield chunk

	def iiod_writebuf(device, data):
		rwthreads[device].write(data)

	class ConnectionHandler(socketserver.StreamRequestHandler):
		def setup(self):
			super().setup()
			print(f'Got a connection from {self.client_address}')

		def handle(self):
			def respond(msg):
				print(f'> {repr(msg)}')
				if type(msg) == int:
					self.wfile.write(f'{msg}\r\n'.encode())
				elif type(msg) == bytes:
					self.wfile.write(f'{len(msg)}\r\n'.encode() + msg + b'\r\n')
				else:
					msg = str(msg)
					self.wfile.write(f'{len(msg)}\r\n{msg}\r\n'.encode())

			while command := self.rfile.readline():
				command = command.strip().decode().split()
				if not command:
					continue

				try:
					match command:
						case ["HELP"]:
							respond("Available commands:\n\n" + \
									"\tHELP\n" + \
									"\t\tPrint this help message\n" + \
									"\tPRINT\n" + \
									"\t\tDisplays a XML string corresponding to the current IIO context\n" + \
									"\tZPRINT\n" + \
									"\t\tGet a compressed XML string corresponding to the current IIO context\n" + \
									"\tVERSION\n" + \
									"\t\tGet the version of libiio in use\n" + \
									"\tBINARY\n" + \
									"\t\tEnable binary protocol\n" + \
									"\tTIMEOUT <timeout_ms>\n" + \
									"\t\tSet the timeout (in ms) for I/O operations\n" + \
									"\tOPEN <device> <samples_count> <mask> [CYCLIC]\n" + \
									"\t\tOpen the specified device with the given mask of channels\n" + \
									"\tCLOSE <device>\n" + \
									"\t\tClose the specified device\n" + \
									"\tREAD <device> DEBUG|BUFFER|[INPUT|OUTPUT <channel>] [<attribute>]\n" + \
									"\t\tRead the value of an attribute\n" + \
									"\tWRITE <device> DEBUG|BUFFER|[INPUT|OUTPUT <channel>] [<attribute>] <bytes_count>\n" + \
									"\t\tSet the value of an attribute\n" + \
									"\tREADBUF <device> <bytes_count>\n" + \
									"\t\tRead raw data from the specified device\n" + \
									"\tWRITEBUF <device> <bytes_count>\n" + \
									"\t\tWrite raw data to the specified device\n" + \
									"\tGETTRIG <device>\n" + \
									"\t\tGet the name of the trigger used by the specified device\n" + \
									"\tSETTRIG <device> [<trigger>]\n" + \
									"\t\tSet the trigger to use for the specified device\n" + \
									"\tSET <device> BUFFERS_COUNT <count>\n" + \
									"\t\tSet the number of kernel buffers for the specified device\n")

						case ["EXIT"]:
							break

						case ["PRINT"]:
							respond(ctx.xml)

						case ["VERSION"]:
							respond(f"{ctx._version[0]}.{ctx._version[1]}.{ctx._version[2]:-7.7}")

						case ["TIMEOUT", timeout_ms]:
							respond(self.ctx.set_timeout(int(timeout_ms)))

						case ["OPEN", device, samples_count, mask]:
							respond(iiod_open(device, int(samples_count), int(mask), False))

						case ["OPEN", device, samples_count, mask, "CYCLIC"]:
							respond(iiod_open(device, int(samples_count), int(mask), True))

						case ["CLOSE", device]:
							respond(iiod_close(device))

						case ["READ", device, "DEBUG", attribute]:
							respond(self.ctx.find_device(device).debug_attrs[attribute].value)

						case ["READ", device, "INPUT", channel, attribute]:
							respond(self.ctx.find_device(device).find_channel(channel, False).attrs[attribute].value)

						case ["READ", device, "OUTPUT", channel, attribute]:
							respond(self.ctx.find_device(device).find_channel(channel, True).attrs[attribute].value)
						
						case ["WRITE", device, "DEBUG", attribute, nbytes]:
							value = rfile.read(int(nbytes))
							attr = self.ctx.find_device(device).debug_attrs[attribute]
							attr.value = value
							respond(attr.value)

						case ["WRITE", device, "INPUT", channel, attribute, nbytes]:
							value = rfile.read(int(nbytes))
							attr = self.ctx.find_device(device).find_channel(channel, False).attrs[attribute]
							attr.value = value
							respond(attr.value)

						case ["WRITE", device, "OUTPUT", channel, attribute, nbytes]:
							value = rfile.read(int(nbytes))
							attr = self.ctx.find_device(device).find_channel(channel, True).attrs[attribute]
							attr.value = value
							respond(attr.value)

						case ["READBUF", device, nbytes]:
							raise NotImplementedError()
							device = self.ctx.find_device(device)
							for chunk in iiod_readbuf_chunks(device, int(nbytes)):
								respond(chunk)

						case ["WRITEBUF", device, nbytes]:
							raise NotImplementedError()
							device = self.ctx.find_device(device)
							data = rfile.read(int(nbytes))
							iiod_writebuf(device, data)
							respond(0)

						case ["GETTRIG", device]:
							respond(self.ctx.find_device(device).trigger.name)

						case ["SETTRIG", device]:
							self.ctx.find_device(device).trigger = None
							respond(0)

						case ["SETTRIG", device, trigger]:
							trigger = self.ctx.find_device(trigger)
							if not trigger:
								respond(-ENOENT)
								break

							self.ctx.find_device(device).trigger = trigger
							respond(0)

						case ["SET", device, "BUFFERS_COUNT", nbuf]:
							raise NotImplementedError()

				except (ValueError, KeyError):
					respond(-EINVAL) # EINVAL
				except NotImplementedError:
					respond(-ENOSYS) # ENOSYS
				except:
					respond(-EIO) # EIO

	return ConnectionHandler
