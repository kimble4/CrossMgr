import socket
import sys
import time
import datetime
now = datetime.datetime.now
import atexit
import subprocess
import threading
import re
import wx
import wx.lib.newevent
import Utils
#import Model
from threading import Thread as Process
from queue import Queue, Empty
#import JChip
import json

class JSONTimer:
	EOL = b'\r\n'		# Sprint timer delimiter
	DEFAULT_PORT = 10123
	DEFAULT_HOST = '81.187.184.219'		# Port to connect to the sprint timer
	
	SPEED_UNKNOWN_UNIT = 0
	SPEED_MPS = 1
	SPEED_MPH = 2
	SPEED_KPH = 3
	SPEED_KTS = 4
	SPEED_FPF = 5
	
	SprintTimerEvent, EVT_SPRINT_TIMER = wx.lib.newevent.NewEvent()
	
	
	def __init__( self ):
		self.q = None
		self.shutdownQ = None
		self.sendQ = None
		self.listener = None
		SprintTimerEvent, EVT_SPRINT_TIMER = wx.lib.newevent.NewEvent()
		self.socket = None
		self.socketLock = None
		
		self.sprintDistance = None
		self.speedUnit = None

		self.readerEventWindow = None
		atexit.register(self.StopListener)
	
	def sendReaderEvent( self, isT2, sprintDict, receivedTime, readerComputerTimeDiff ):
		if json and self.readerEventWindow:
			wx.PostEvent( self.readerEventWindow, JSONTimer.SprintTimerEvent(isT2 = isT2, sprintDict = sprintDict, receivedTime = receivedTime, readerComputerTimeDiff = readerComputerTimeDiff) )

	def setSprintDistance( self, distance = None ):
		self.sprintDistance = distance
		self.writeSettings()
	
	def setSpeedUnit( self, unit = SPEED_UNKNOWN_UNIT ):
		self.speedUnit = unit
		self.writeSettings()
		
	def setBib( self, bib = None):
		if self.sendQ:
			try:
				settings = { "sprintBib": bib }
				message = json.dumps(settings) + '\n'
				self.sendQ.put(message)
			except Exception as e:
				print(e)
				self.qLog( 'send', '{}: {}: "{}"'.format(cmd, _('Failed to write to sendQ'), e) )
			self.processSendQ()

	def writeSettings( self ):
		if self.sendQ:
			try:
				settings = { "sprintDistance": self.sprintDistance, "speedUnit": self.speedUnit }
				message = json.dumps(settings) + '\n'
				self.sendQ.put(message)
			except Exception as e:
				print(e)
				self.qLog( 'send', '{}: {}: "{}"'.format(cmd, _('Failed to write to sendQ'), e) )
			self.processSendQ()
				
	def processSendQ( self ):
		while self.sendQ:
			try:
				message = self.sendQ.get_nowait()
				self.socketWriteLock.acquire()
				self.qLog( 'send', '{}: {}'.format(_('Sending'), message))
				self.socketSend( self.socket, message.encode('utf-8'))
				self.socketWriteLock.release()
			except Empty:
				return
				
	def socketSend( self, s, message ):
		sLen = 0
		while sLen < len(message):
			sLen += s.send( message[sLen:] )
			
	def socketReadDelimited( self, s, delimiter=EOL ):
		len_EOL = len(delimiter)
		buffer = self.socket.recv( 4096 )
		while not buffer.endswith( delimiter ):
			more = self.socket.recv( 4096 )
			if more:
				buffer += more
			else:
				break
		return buffer[:-len_EOL]
		
	def iterAdjacentIPs( self ):
		''' Return ip addresses adjacent to the computer in an attempt to find the reader. '''
		ip = [int(i) for i in Utils.GetDefaultHost().split('.')]
		ipPrefix = '.'.join( '{}'.format(v) for v in ip[:-1] )
		ipLast = ip[-1]
		
		count = 0
		j = 0
		while 1:
			j = -j if j > 0 else -j + 1
			
			ipTest = ipLast + j
			if 0 <= ipTest < 256:
				yield '{}.{}'.format(ipPrefix, ipTest)
				count += 1
				if count >= 8:
					break
			
	def AutoDetect( self, port=DEFAULT_PORT, callback=None ):
		for host in self.iterAdjacentIPs():
			if callback:
				if not callback( '{}:{}'.format(host,port) ):
					return None
			
			try:
				s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
				self.socket.settimeout( 0.5 )
				self.socket.connect( (host, port) )
			except Exception as e:
				continue

			try:
				buffer = socketReadDelimited( s )
			except Exception as e:
				continue
				
			try:
				self.socket.close()
			except Exception as e:
				pass
			
			if buffer.startswith('Connected'):
				return host
				
		return None
	
	def qLog( self, category, message ):
			self.q.put( (category, message) )
			Utils.writeLog( 'JSONTimer: {}: {}'.format(category, message) )

	def Server( self, q, shutdownQ, sendQ, HOST, PORT ):
		
		if not self.readerEventWindow:
			self.readerEventWindow = Utils.mainWin
		
		timeoutSecs = 1
		delaySecs = 3
		
		readerTime = None
		readerComputerTimeDiff = None
		
		def keepGoing():
			try:
				self.shutdownQ.get_nowait()
			except Empty:
				return True
			return False
		
		def autoDetectCallback( m ):
			self.qLog( 'autodetect', '{} {}'.format(_('Checking'), m) )
			return keepGoing()
			
		def makeCall( s, message, getReply=True, comment='' ):
			cmd = message.split(';', 1)[0]
			buffer = None
			self.qLog( 'command', 'sending: {}{}'.format(message, ' ({})'.format(comment) if comment else '') )
			try:
				#socketSend( s, bytes('{}{}'.format(message,EOL)) )
				socketSend( s, bytes(message) )
				if getReply:
					buffer = socketReadDelimited( s )
			except Exception as e:
				self.qLog( 'connection', '{}: {}: "{}"'.format(cmd, _('Connection failed'), e) )
				raise ValueError
			
			return buffer
		
		while keepGoing():
			if self.socket:
				try:
					self.socket.shutdown( socket.SHUT_RDWR )
					self.socket.close()
				except Exception as e:
					pass
				time.sleep( delaySecs )
			
			#-----------------------------------------------------------------------------------------------------
			self.qLog( 'connection', '{} {}:{}'.format(_('Attempting to connect to sprint timer at'), HOST, PORT) )
			try:
				self.socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
				self.socket.settimeout( timeoutSecs )
				self.socket.connect( (HOST, PORT) )
			except Exception as e:
				self.qLog( 'connection', '{}: {}'.format(_('Connection to sprint timer failed'), e) )
				self.socket = None
				self.qLog( 'connection', '{}'.format(_('Attempting AutoDetect...')) )
				HOST_AUTO = self.AutoDetect( callback = autoDetectCallback )
				if HOST_AUTO:
					self.qLog( 'connection', '{}: {}'.format(_('AutoDetect sprint timer at'), HOST_AUTO) )
					HOST = HOST_AUTO
				else:
					time.sleep( delaySecs )
				continue

			self.qLog( 'connection', '{} {}:{}'.format(_('connect to sprint timer SUCCEEDS on'), HOST, PORT) )
			# send the settings and epoch time immediately
			self.socketWriteLock.acquire()
			settings = { "sprintDistance": self.sprintDistance, "speedUnit": self.speedUnit, "wallTime": int(now().timestamp()) }
			message = json.dumps(settings) + '\n'
			self.socketSend(self.socket, message.encode('utf-8'))
			self.socketWriteLock.release()
			
			#-----------------------------------------------------------------------------------------------------
			
			lastHeartbeat = now()
			lastT2 = 0
			lastT1 = 0
			clockOffset = None # positive value means we are ahead of the timer
			while keepGoing():
				# read from the reader
				try:
					buffer = self.socketReadDelimited( self.socket )
					receivedTime = now()
					if buffer:
						sprintDict = json.loads(buffer)
						if "wallTime" in sprintDict:
							if sprintDict["wallTime"]:  #Use the presence of wallTime as the heartbeat
								lastHeartbeat = receivedTime
								ms = 0;
								if "wallMillis" in sprintDict:
									ms = sprintDict["wallMillis"] / 1000.0
								readerTime = datetime.datetime.fromtimestamp(float(sprintDict["wallTime"]) + ms)
								readerComputerTimeDiff = receivedTime - readerTime
								self.qLog( 'time', '{}: {}'.format(_('Our clock is ahead by'), readerComputerTimeDiff.total_seconds() ) )
							
						if "T2micros" in sprintDict:
							if sprintDict["T2micros"] != lastT2:
								lastT2 = sprintDict["T2micros"]
								#self.qLog( 'data', '{}: {}'.format(_('Got new sprint'), str(sprintDict) ) )
								q.put( ('data', sprintDict, receivedTime, readerComputerTimeDiff) )
								self.sendReaderEvent(True, sprintDict, receivedTime, readerComputerTimeDiff)
						elif "T1micros" in sprintDict:
							if sprintDict["T1micros"] != lastT1:
								lastT1 = sprintDict["T1micros"]
								#self.qLog( 'data', '{}: {}'.format(_('Sprint has started'), str(sprintDict) ) )
								self.sendReaderEvent(False, sprintDict, receivedTime, readerComputerTimeDiff)
					else:
						self.qLog( 'connection', '{}'.format(_('Sprint timer socket has CLOSED')) )
						break
				except json.JSONDecodeError:
					self.qLog( 'connection', _('Failed to parse JSON.') )
					continue
				except socket.timeout:
					# timeouts are normal and ordinary, we just go round the loop and try again until we get some data
					if (now() - lastHeartbeat).total_seconds() > 35:
						self.qLog( 'connection', _('Lost heartbeat.') )
						break
					continue
				except Exception as e:
					self.qLog( 'connection', '{}: "{}"'.format(_('Connection failed'), e) )
					break
				
				self.processSendQ()
				
		# Final cleanup.
		try:
			self.socket.shutdown( socket.SHUT_RDWR )
			self.socket.close()
		except Exception:
			pass
			
	def GetData( self ):
		data = []
		while 1:
			try:
				data.append( self.q.get_nowait() )
			except (Empty, AttributeError):
				break
		return data

	def StopListener( self ):		
		# Terminate the server process if it is running.
		# Add a number of shutdown commands as we may check a number of times.
		if self.listener:
			self.qLog( 'connection', _('Shutting down listener') )
			for i in range(32):
				self.shutdownQ.put( 'shutdown' )
			self.listener.join()
		self.listener = None
		
		# Purge the queues.
		while self.q:
			try:
				self.q.get_nowait()
			except Empty:
				self.q = None
				break
		
		self.shutdownQ = None
		
		self.socketWriteLock = None
		
	def IsListening( self ):
		return self.listener is not None

	def StartListener( self, HOST=None, PORT=None, test=False ):
		self.StopListener()
		self.q = Queue()
		self.shutdownQ = Queue()
		self.sendQ = Queue()
		self.socketWriteLock = threading.Lock()
		self.listener = Process( target = self.Server, args=(self.q, self.shutdownQ, self.sendQ, HOST, PORT) )
		self.listener.name = 'JSONTimer Listener'
		self.listener.daemon = True
		self.listener.start()
		
jsonTimer = JSONTimer()

if __name__ == '__main__':
	def doTest():
		try:
			sprintTimer = JSONTimer()
			sprintTimer.setSprintDistance(50)
			sprintTimer.setSpeedUnit(JSONTimer.SPEED_KPH)
			sprintTimer.StartListener( HOST='81.187.184.219', PORT=JSONTimer.DEFAULT_PORT )

			time.sleep( 1 )
			sprintTimer.setSprintDistance(10)
			time.sleep( 5 )
			sprintTimer.setBib( 136 )
			while True:
				time.sleep(1)
				try:
					items = sprintTimer.GetData()
					for item in items:
						if item[0] == 'data':
							print('Got data: ' + str(item[2]) + ' ' + str(item[1]))
				except Empty:
					pass
				
				
				
				
		except KeyboardInterrupt:
			return
		
	t = threading.Thread( target=doTest )
	t.daemon = True
	t.run()
	
	time.sleep( 1000000 )

