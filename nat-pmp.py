import socket
import struct
import netifaces

resultCodes = [
	"Success",
	"Unsupported Version",
	"Not Authorized/Refused (e.g. box supports mapping, but user has turned feature off)",
	"Network Failure (e.g. NAT box itself has not obtained a DHCP lease)",
	"Out of resources (NAT box cannot create any more mappings at this time)",
	"Unsupported operation code"
]

def appendHex(hexValues):
	val = 0
	shift = 0
	for index in range(len(hexValues)):
		intVal = int(hexValues[index], 16)
		if intVal != 0:
			val |= intVal << shift
			shift += 8

	return val

def parseResult(result):
	version = int(result[0], 16)
	opCode = int(result[1], 16)
	resultCode = int(appendHex(result[2:4]))
	secondSinceInit = appendHex(result[4:8])
	privatePort = appendHex(result[8:10])
	publicPort = appendHex(result[10:12])
	mappingLifetime = appendHex(result[12:16])

	resultMessage = resultCodes[resultCode] if resultCode <= len(resultCodes) else "Unknown error code!"

	print "Version: %s\
	\nOperation Code: %s (Requested: %s)\
	\nResult Code: %s - %s\
	\nSeconds Since Mapping Table Initialized: %s\
	\nPrivate Port: %s\
	\nPublic Port: %s\
	\nPort Mapping Lifetime in Seconds: %s" % \
	(version, opCode, str(opCode - 128), resultCode, resultMessage, secondSinceInit, privatePort, publicPort, mappingLifetime)

def checkInt(string):
    try: 
        value = int(string)
        return value
    except ValueError:
        return False

def forwardPort(privatePort, publicPort, lifeTime, protocol):
	privatePort = checkInt(privatePort)
	publicPort = checkInt(publicPort)
	lifeTime = checkInt(lifeTime)

	if privatePort and publicPort and lifeTime:
		#udpPacket = struct.pack("!BBIIII", 0x0, 0x2, 0x0, 0x16, 0x16, 0x3C)
		protocol = 1 if protocol.lower() == "udp" else 2

		udpPacket = struct.pack("!BBIIII", 0x0, protocol, 0x0, privatePort, publicPort, lifeTime)
		gateway = netifaces.gateways()["default"]

		if netifaces.AF_INET in gateway:
			gateway = gateway[netifaces.AF_INET][0]
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			sock.settimeout(10)
			try:
				sock.connect((gateway, 5351))

				sock.send(udpPacket)
				response = sock.recvfrom(16)
				sock.close

				resultArray = map(ord, response[0])
				for index in range(len(resultArray)):
					resultArray[index] = hex(resultArray[index])

				parseResult(resultArray)
			except socket.timeout:
				print "Could not connect to NAT-PMP on port 5351 (timed out after 10 seconds)"
		else:
			print "Not connected to a network!"

	else:
		print "Please input valid values"

privatePort = raw_input("Private Port: ")
publicPort = raw_input("Public Port: ")
lifeTime = raw_input("Lifetime in seconds: ")
protocol = raw_input("Protocol (TCP or UDP): ")
forwardPort(privatePort, publicPort, lifeTime, protocol)
