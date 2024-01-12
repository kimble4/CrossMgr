import Utils
import Model

def SetNoDataDNS():
	race = Model.race
	if not race or not race.setNoDataDNS:
		return
		
	try:
		externalInfo = race.excelLink.read()
	except Exception:
		return
	
	Finisher, DNS, NP = Model.Rider.Finisher, Model.Rider.DNS, Model.Rider.NP
	
	isChanged = False
	
	if race.isRunning():
		for num in externalInfo.keys():
			if race.getRiderStatus(num) == NP:
				if race.riderHasValidTimes(num):
					race.setRiderStatus( num, Finisher )
					isChanged = True
			elif race.getRiderStatus(num) == Finisher:
				if not race.riderHasValidTimes(num):
					race.setRiderStatus( num, NP )
					isChanged = True
	
	elif race.isFinished():
		for num in externalInfo.keys():
			if race.getRiderStatus(num) == NP:
				race.setRiderStatus( num, Finisher if race.riderHasValidTimes(num) else DNS)
				isChanged = True
	
	if isChanged:
		race.setChanged()
