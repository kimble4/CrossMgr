import re
import operator
from pyllrp.pyllrp import *
from pyllrp.TagWriter import TagWriter, getTagMask, padToWords, addLengthPrefix, hexToWords
import codecs

# overriding hexToBytes in pyllrp.TagWriter to fix bug
def hexToBytes( epc ):
	assert len(epc) % 2 == 0, 'epc must be a byte multiple'
	return codecs.decode(epc, 'hex_codec')  # fixes typo in pyllrp.TagWriter

def GetReceiveTransmitPowerGeneralCapabilities( connector ):
	# Enable Impinj Extensions
	message = IMPINJ_ENABLE_EXTENSIONS_Message( MessageID = 0xeded )
	response = connector.transact( message )
	hasImpinjExtensions = response.success()
	
	# Query the reader to get the receive and transmit power tables.
	message = GET_READER_CAPABILITIES_Message( MessageID = 0xed, RequestedData = GetReaderCapabilitiesRequestedData.All )
	response = connector.transact( message )
	
	# Receive power expressed as -80db + value relative to maximum power.
	receive_sensitivity_table = [-80 + e.ReceiveSensitivityValue
		for e in sorted(response.getAllParametersByClass(ReceiveSensitivityTableEntry_Parameter), key=operator.attrgetter('Index'))
	]
	# Transmit power expressed as dBm*100 (dB relative to a milliwatt).
	transmit_power_table = [e.TransmitPowerValue/100.0
		for e in sorted(response.getAllParametersByClass(TransmitPowerLevelTableEntry_Parameter), key=operator.attrgetter('Index'))
	]

	# General device info.
	device_fields = {}
	general_capabilities = {}
	
	def set_capability( k, v ):
		general_capabilities[k] = v
		if k not in device_fields:
			device_fields[k] = len(device_fields)

	p = response.getFirstParameterByClass( GeneralDeviceCapabilities_Parameter )
	if p:
		for a in ('ReaderFirmwareVersion', 'DeviceManufacturerName', 'ModelName', 'MaxNumberOfAntennaSupported', 'HasUTCClockCapability'):
			v = getattr( p, a, 'missing' )
			set_capability( a, getVendorName(v) if a == 'DeviceManufacturerName' else v )

	if hasImpinjExtensions:
		# Impinj Detailed Version.
		p = response.getFirstParameterByClass( ImpinjDetailedVersion_Parameter )
		if p:
			for a in ('ModelName', 'SerialNumber', 'SoftwareVersion', 'FirmwareVersion'):
				v = getattr( p, a, 'missing' )
				set_capability( a, v )

		# Reader Temperature.
		message = GET_READER_CONFIG_Message( MessageID = 0xededed, RequestedData = GetReaderConfigRequestedData.All )
		response = connector.transact( message )
		if response.success():
			p = response.getFirstParameterByClass( ImpinjReaderTemperature_Parameter )
			#if not p:
			#	p = ImpinjReaderTemperature_Parameter( Temperature=33 )
			if p:
				a = 'Temperature'
				v = getattr( p, a, 'missing' )
				if isinstance( v, int ):
					set_capability( a, '{}C  |  {}F'.format(v, int(v * (9.0/5.0) + 32.0 + 0.5)) )
	
	return receive_sensitivity_table, transmit_power_table, [(a,general_capabilities[a]) for a in sorted(device_fields.keys(), key=device_fields.__getitem__)]

class TagWriterCustom( TagWriter ):
	# GetAccessSpec copied from pyllrp.TagWriter to fix bug in hexToBytes
	def GetAccessSpec(	self,
						MessageID = None,			# If None, one will be assigned.
						epcOld = '',				# Old EPC.  Empty matches anything.
						epcNew = '0123456789',		# New EPC.
						roSpecID = 0,				# ROSpec to trigger this ROSpec.  0 = run when any ROSpec runs.
						opSpecID = 1,				# Something unique.
						operationCount = 10,		# Number of times to execute.
						antenna = None ):
		
		TagMask = hexToBytes( getTagMask(epcOld) ) if epcOld else b''
		TagData = hexToBytes( addLengthPrefix(epcOld) ) if epcOld else b''
		
		accessSpecMessage = ADD_ACCESSSPEC_Message( MessageID = MessageID, Parameters = [
			AccessSpec_Parameter(
				AccessSpecID  = self.accessSpecID,
				AntennaID = antenna if antenna else 0,	# Unspecified antenna: apply to all antennas
				ProtocolID = AirProtocols.EPCGlobalClass1Gen2,
				CurrentState = bool(AccessSpecState.Disabled),
				ROSpecID = roSpecID,
				
				Parameters = [
					AccessSpecStopTrigger_Parameter(
						AccessSpecStopTrigger = AccessSpecStopTriggerType.Operation_Count,
						OperationCountValue = operationCount
					),
					AccessCommand_Parameter(
						Parameters = [
							C1G2TagSpec_Parameter(
								Parameters = [
									C1G2TargetTag_Parameter(
										MB = 1,						# Memory Bank 1 = EPC
										Pointer = 16,				# 16 bits offset - skip CRC.
										TagMask = TagMask,
										TagData = TagData,
										Match = True,
									)
								]
							),
							C1G2Write_Parameter(
								MB = 1,
								WordPointer = 1,					# Skip CRC, but include the length and flags.
								WriteData = hexToWords( addLengthPrefix(epcNew) ),
								OpSpecID = opSpecID,
								AccessPassword = 0,
							),
						]
					),
					AccessReportSpec_Parameter(
						AccessReportTrigger = AccessReportTriggerType.End_Of_AccessSpec
					)
				]
			)
		])	# ADD_ACCESS_SPEC_Message
		
		return accessSpecMessage
	
	def Connect( self, receivedB, transmitdBm ):
		# In order to validate the parameters, we need to do two connects.
		# The first call gets the tables, the second call sets the receive sensitivity and transmit power based on the available options.
		super().Connect()
		self.receive_sensitivity_table, self.transmit_power_table, self.general_capabilities = GetReceiveTransmitPowerGeneralCapabilities( self.connector )
		super().Disconnect()
		self.setReceiveSensitivity_dB( receivedB )
		self.setTransmitPower_dBm( transmitdBm )
		#print('self.TransmitPower: ' + str(self.transmitPower))
		super().Connect()

	def setReceiveSensitivity_dB( self, dB ):
		self.receiverSensitivity = None
		try:
			dB = float( re.sub('[^.0-9-]', '', dB) )
		except ValueError:
			return
		if len(self.receive_sensitivity_table) <= 1 or dB <= self.receive_sensitivity_table[0]:
			return
		for self.receiverSensitivity, dB_cur in enumerate(self.receive_sensitivity_table, 1):
			if dB_cur >= dB:
				break
		#print('self.receiverSensitivity: ' + str(self.receiverSensitivity))

	def setTransmitPower_dBm( self, dBm ):
		self.transmitPower = None
		try:
			dBm = float( re.sub('[^.0-9]', '', dBm) )
		except ValueError:
			return
		if len(self.transmit_power_table) <= 1 or dBm > self.transmit_power_table[-1]:
			return
		for self.transmitPower, dBm_cur in enumerate(self.transmit_power_table, 1):
			if dBm_cur >= dBm:
				break
		#print('self.setTransmitPower: ' + str(self.transmitPower))
