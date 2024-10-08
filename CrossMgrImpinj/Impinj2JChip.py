import re
import os
import socket
import time
import threading
import datetime
from queue import Empty

#------------------------------------------------------------------------------	
# JChip delimiter (CR, **not** LF)
CR = '\r'
bCR = CR.encode()
		
#------------------------------------------------------------------------------	
# Function to format number, lap and time in JChip format
# Z413A35 10:11:16.4433 10  10000      C7
count = 0
def formatMessage( tagID, t ):
	global count
	message = "DA{} {} 10  {:05X}      C7 date={}{}".format(
				tagID,								# Tag code in decimal, no leading zeros.
				t.strftime('%H:%M:%S.%f'),			# hh:mm:ss.ff
				count,								# Data index number in hex.
				t.strftime('%Y%m%d'),				# YYYYMMDD
				CR
			)
	count += 1
	return message

class Impinj2JChip:
	def __init__( self, dataQ, messageQ, shutdownQ, crossMgrHost, crossMgrPort ):
		''' Queues:
				dataQ:		tag/timestamp data to be written out to CrossMgr.
				messageQ:	queue to write status messages.
				shutdownQ:	queue to receive shutdown message to stop gracefully.
		'''
		self.dataQ = dataQ
		self.messageQ = messageQ
		self.shutdownQ = shutdownQ
		self.crossMgrHost = crossMgrHost
		self.crossMgrPort = crossMgrPort
		self.keepGoing = True
		self.tagCount = 0
	
	def shutdown( self ):
		self.keepGoing = False
		
	def checkKeepGoing( self ):
		if not self.keepGoing:
			return False
			
		try:
			d = self.shutdownQ.get( False )
			self.keepGoing = False
			return False
		except Empty:
			return True

	def getCmd( self, sock ):
		# Read from the socket until we get data ending in the delimiter.
		# Handle all exceptions, and return them.
		received = b''
		while self.keepGoing and received[-1:] != bCR:
			try:
				received += sock.recv(4096)
			except Exception as e:
				return received.decode(), e
		return received[:-1].decode(), None

	def runServer( self ):
		instance_name = '{}-{}'.format(socket.gethostname(), os.getpid())
		while self.checkKeepGoing():
			self.messageQ.put( ('Impinj2JChip', 'state', False) )
			self.messageQ.put( ('Impinj2JChip', 'Trying to connect to CrossMgr at {}:{} as "{}"...'.format(self.crossMgrHost, self.crossMgrPort, instance_name)) )

			#------------------------------------------------------------------------------	
			# Connect to the CrossMgr server.
			#
			self.tagCount = 0
			while self.checkKeepGoing():
				try:
					sock = None
					sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
					# Set the timeout with CrossMgr to 2 seconds.  If CrossMgr fails to respond within this time, re-establish the connection.
					sock.settimeout( 2.0 )
					sock.connect( (self.crossMgrHost, self.crossMgrPort) )
					break
				except Exception as e:
					sock = None
					self.messageQ.put( ('Impinj2JChip', 'CrossMgr Connection Failed: {}.'.format(e)) )
					self.messageQ.put( ('Impinj2JChip', 'Trying again at {}:{} as "{}" in 2 sec...'.format(self.crossMgrHost, self.crossMgrPort, instance_name)) )
					for t in range(2):
						time.sleep( 1 )
						if not self.checkKeepGoing():
							break

			if not self.checkKeepGoing():
				break
				
			#------------------------------------------------------------------------------
			# Send client identity.
			#
			self.messageQ.put( ('Impinj2JChip', 'state', True) )
			self.messageQ.put( ('Impinj2JChip', '******************************' ) )
			self.messageQ.put( ('Impinj2JChip', 'CrossMgr Connection succeeded!' ) )
			self.messageQ.put( ('Impinj2JChip', 'Sending identifier "{}"...'.format(instance_name)) )
			try:
				sock.sendall( "N0000{}{}".format(instance_name, CR).encode() )
			except Exception as e:
				self.messageQ.put( ('Impinj2JChip', 'CrossMgr error: {}.'.format(e)) )
				sock.close()
				sock = None
				continue

			#------------------------------------------------------------------------------	
			self.messageQ.put( ('Impinj2JChip', 'Waiting for GT (get time) command from CrossMgr...') )
			received, e = self.getCmd( sock )
			if not self.checkKeepGoing():
				break
			if e:
				self.messageQ.put( ('Impinj2JChip', 'CrossMgr error: {}.'.format(e)) )
				sock.close()
				sock = None
				continue
			self.messageQ.put( ('Impinj2JChip', 'Received: "{}" from CrossMgr'.format(received)) )
			if received != 'GT':
				self.messageQ.put( ('Impinj2JChip', 'Incorrect command (expected GT).') )
				sock.close()
				sock = None
				continue

			# Send 'GT' (GetTime response to CrossMgr).
			self.messageQ.put( ('Impinj2JChip', 'Sending GT (get time) response...') )
			# format is GT0HHMMSShh<CR> where hh is 100's of a second.  The '0' (zero) after GT is the number of days running, ignored by CrossMgr.
			dBase = datetime.datetime.now()
			message = 'GT0{} date={}{}'.format(
				dBase.strftime('%H%M%S%f'),
				dBase.strftime('%Y%m%d'),
				CR)
			self.messageQ.put( ('Impinj2JChip', message[:-1]) )
			try:
				sock.sendall( message.encode() )
			except Exception as e:
				self.messageQ.put( ('Impinj2JChip', 'CrossMgr exception: {}.'.format(e)) )
				sock.close()
				sock = None
				continue

			#------------------------------------------------------------------------------	
			if not self.checkKeepGoing():
				break

			self.messageQ.put( ('Impinj2JChip', 'Waiting for S0000 (send) command from CrossMgr...') )
			received, e = self.getCmd( sock )
			if not self.checkKeepGoing():
				break
			if e:
				self.messageQ.put( ('Impinj2JChip', 'CrossMgr error: {}.'.format(e)) )
				sock.close()
				sock = None
				continue
			self.messageQ.put( ('Impinj2JChip', 'Received: "{}" from CrossMgr'.format(received)) )
			if not received.startswith('S'):
				self.messageQ.put( ('Impinj2JChip', 'Incorrect command (expected S0000).') )
				sock.close()
				sock = None
				continue

			#------------------------------------------------------------------------------
			# Enter "Send" mode - keep sending data until we get a shutdown.
			# If the connection fails, return to the outer loop.
			#
			self.messageQ.put( ('Impinj2JChip', 'Start sending data to CrossMgr...') )
			self.messageQ.put( ('Impinj2JChip', 'Waiting for RFID reader data...') )
			while self.checkKeepGoing():
				try:
					# Get all the entries from the receiver and forward them to CrossMgr.
					d = self.dataQ.get(timeout=60)
					
					if d == 'shutdown':
						self.keepGoing = False
						break
					
					# Expect message if the form [tag, time].
					message = formatMessage( d[0], d[1] )
					try:
						sock.sendall( message.encode() )
						self.tagCount += 1
						self.messageQ.put( ('Impinj2JChip', 'Forwarded {}: {}'.format(self.tagCount, message[:-1])) )
					except Exception as e:
						self.dataQ.put( d )	# Put the data back on the queue for resend.
						self.messageQ.put( ('Impinj2JChip', 'CrossMgr error: {}.'.format(e)) )
						self.messageQ.put( ('Impinj2JChip', 'Attempting to reconnect...') )
						break
				except Empty:
					# Timeout getting data - resend the current time as a keepalive.
					dBase = datetime.datetime.now()
					message = 'GT0{} date={}{}'.format(
						dBase.strftime('%H%M%S%f'),
						dBase.strftime('%Y%m%d'),
						CR)
					self.messageQ.put( ('Impinj2JChip', message[:-1]) )
					try:
						sock.sendall( message.encode() )
					except Exception as e:
						self.messageQ.put( ('Impinj2JChip', 'CrossMgr exception: {}.'.format(e)) )
						break
		
			sock.close()
			sock = None
			
def CrossMgrServer( dataQ, messageQ, shutdownQ, crossMgrHost, crossMgrPort ):
	impinj2JChip = Impinj2JChip( dataQ, messageQ, shutdownQ, crossMgrHost, crossMgrPort )
	impinj2JChip.runServer()
