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
	DEFAULT_PORT = 123
	DEFAULT_HOST = '81.187.184.219'		# Port to connect to the sprint timer
	
	def __init__( self ):
		self.q = None
		self.shutdownQ = None
		self.listener = None
		SprintTimerEvent, EVT_SPRINT_TIMER = wx.lib.newevent.NewEvent()

		self.readerEventWindow = None
		atexit.register(self.CleanupListener)
	
	def sendReaderEvent( self, json, receivedTime ):
		if json and self.readerEventWindow:
			wx.PostEvent( self.readerEventWindow, SprintTimerEvent(json = json, receivedTime = receivedTime) )

	

	def parseTagTime(  self, s ):
		_, ChipCode, Seconds, Milliseconds, _ = s.split(',', 4)
		t = datetime.datetime(1980, 1, 1) + datetime.timedelta( seconds=int(Seconds), milliseconds=int(Milliseconds) )
		return ChipCode, t

	

	def socketSend( self, s, message ):
		sLen = 0
		while sLen < len(message):
			sLen += s.send( message[sLen:] )
			
	def socketReadDelimited( self, s, delimiter=EOL ):
		len_EOL = len(delimiter)
		buffer = s.recv( 4096 )
		while not buffer.endswith( delimiter ):
			more = s.recv( 4096 )
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
				s.settimeout( 0.5 )
				s.connect( (host, port) )
			except Exception as e:
				continue

			try:
				buffer = socketReadDelimited( s )
			except Exception as e:
				continue
				
			try:
				s.close()
			except Exception as e:
				pass
			
			if buffer.startswith('Connected'):
				return host
				
		return None

	def Server( self, q, shutdownQ, HOST, PORT, startTime ):
		#global readerEventWindow
		
		if not self.readerEventWindow:
			self.readerEventWindow = Utils.mainWin
		
		timeoutSecs = 5
		delaySecs = 3
		
		readerTime = None
		readerComputerTimeDiff = None
		
		s = None
		passingsCur = 0
		status = None
		startOperation = None
		
		def qLog( category, message ):
			self.q.put( (category, message) )
			Utils.writeLog( 'JSONTimer: {}: {}'.format(category, message) )
		
		def keepGoing():
			try:
				self.shutdownQ.get_nowait()
			except Empty:
				return True
			return False
		
		def autoDetectCallback( m ):
			qLog( 'autodetect', '{} {}'.format(_('Checking'), m) )
			return keepGoing()
			
		def makeCall( s, message, getReply=True, comment='' ):
			cmd = message.split(';', 1)[0]
			buffer = None
			qLog( 'command', 'sending: {}{}'.format(message, ' ({})'.format(comment) if comment else '') )
			try:
				#socketSend( s, bytes('{}{}'.format(message,EOL)) )
				socketSend( s, bytes(message) )
				if getReply:
					buffer = socketReadDelimited( s )
			except Exception as e:
				qLog( 'connection', '{}: {}: "{}"'.format(cmd, _('Connection failed'), e) )
				raise ValueError
			
			return buffer
		
		while keepGoing():
			if s:
				try:
					s.shutdown( socket.SHUT_RDWR )
					s.close()
				except Exception as e:
					pass
				time.sleep( delaySecs )
			
			#-----------------------------------------------------------------------------------------------------
			qLog( 'connection', '{} {}:{}'.format(_('Attempting to connect to sprint timer at'), HOST, PORT) )
			try:
				s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
				s.settimeout( timeoutSecs )
				s.connect( (HOST, PORT) )
			except Exception as e:
				qLog( 'connection', '{}: {}'.format(_('Connection to sprint timer failed'), e) )
				s, status, startOperation = None, None, None
				
				qLog( 'connection', '{}'.format(_('Attempting AutoDetect...')) )
				HOST_AUTO = self.AutoDetect( callback = autoDetectCallback )
				if HOST_AUTO:
					qLog( 'connection', '{}: {}'.format(_('AutoDetect sprint timer at'), HOST_AUTO) )
					HOST = HOST_AUTO
				else:
					time.sleep( delaySecs )
				continue

			qLog( 'connection', '{} {}:{}'.format(_('connect to sprint timer SUCCEEDS on'), HOST, PORT) )
			
			#-----------------------------------------------------------------------------------------------------
			
			lastHeartbeat = now()
			lastSprintTime = 0
			lastSprintStart = 0
			clockOffset = None # positive value means we are ahead of the timer
			while keepGoing():
				try:
					buffer = self.socketReadDelimited( s )
					receivedTime = now()
					if buffer:
						sprintDict = json.loads(buffer)
						if sprintDict["wallTime"]:  #Use the presence of wallTime as the heartbeat
							lastHeartbeat = receivedTime
							ms = 0;
							if sprintDict["wallMillis"]:
								ms = sprintDict["wallMillis"] / 1000.0
							timersTime = datetime.datetime.fromtimestamp(float(sprintDict["wallTime"]) + ms)
							clockOffset = receivedTime - timersTime
							qLog( 'time', '{}: {}'.format(_('Our clock is ahead by'), clockOffset.total_seconds() ) )
							
						if "sprintTime" in sprintDict:
							if sprintDict["sprintTime"] != lastSprintTime:
								lastSprintTime = sprintDict["sprintTime"]
								if "sprintStart" in sprintDict:
									lastSprintStart = sprintDict["sprintStart"]
								qLog( 'data', '{}: {}'.format(_('Got new sprint'), str(sprintDict) ) )
								self.sendReaderEvent(sprintDict, receivedTime)
						elif "sprintStart" in sprintDict:
							if sprintDict["sprintStart"] != lastSprintStart:
								lastSprintStart = sprintDict["sprintStart"]
								qLog( 'data', '{}: {}'.format(_('Sprint has started'), str(sprintDict) ) )
								self.sendReaderEvent(sprintDict, receivedTime)
					else:
						qLog( 'connection', '{}'.format(_('Sprint timer socket has CLOSED')) )
						break
				except json.JSONDecodeError:
					qLog( 'connection', _('Failed to parse JSON.') )
					continue
				except socket.timeout:
					# timeouts are normal and ordinary, we just go round the loop and try again until we get some data
					if (now() - lastHeartbeat).total_seconds() > 60:
						qLog( 'connection', _('Lost heartbeat.') )
						break
					continue
				except Exception as e:
					qLog( 'connection', '{}: "{}"'.format(_('Connection failed'), e) )
					break
		
		# Final cleanup.
		try:
			s.shutdown( socket.SHUT_RDWR )
			s.close()
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
		
	def IsListening( self ):
		return self.listener is not None

	def StartListener( self, startTime=now(), HOST=None, PORT=None, test=False ):
		self.StopListener()
		
		self.q = Queue()
		self.shutdownQ = Queue()
		self.listener = Process( target = self.Server, args=(self.q, self.shutdownQ, HOST, PORT, startTime) )
		self.listener.name = 'JSONTimer Listener'
		self.listener.daemon = True
		self.listener.start()
		
	def CleanupListener( self ):
		#global shutdownQ
		#global listener
		if self.listener and self.listener.is_alive():
			self.shutdownQ.put( 'shutdown' )
			self.listener.join()
		self.listener = None
		
	
if __name__ == '__main__':
	def doTest():
		try:
			sprintTimer = JSONTimer()
			sprintTimer.StartListener( HOST='81.187.184.219', PORT=JSONTimer.DEFAULT_PORT )
			count = 0
			while 1:
				time.sleep( 1 )
				#sys.stdout.write( '.' )
				#messages = sprintTimer.GetData()
				#if messages:
					#sys.stdout.write( '\n' )
				#for m in messages:
					#if m[0] == 'data':
						#count += 1
						#print( '{}: {}'.format(count, m[1]) )
					#else:
						#print( 'other: {}, {}'.format(m[0], ', '.join('"{}"'.format(s) for s in m[1:])) )
				#sys.stdout.flush()
		except KeyboardInterrupt:
			return
		
	t = threading.Thread( target=doTest )
	t.daemon = True
	t.run()
	
	time.sleep( 1000000 )

