from tkinter import *
import tkinter.messagebox as messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os, time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	SETUP_STR = 'SETUP'
	PLAY_STR = 'PLAY'
	PAUSE_STR = 'PAUSE'
	TEARDOWN_STR = 'TEARDOWN'

	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3

	RTSP_VER = "RTSP/1.0"
	TRANSPORT = "RTP/UDP"

	begin = 0
	stop  = True
	sumTime = 0
	sumData = 0
	counter = 0
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		"""Setup button handler."""
	#TODO
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
	
	def exitClient(self):
		"""Teardown button handler."""
	#TODO
		self.sendRtspRequest(self.TEARDOWN)
		self.master.destroy()  # Close the gui window
		try:
			os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
		except:
			"No cache file to delete."
		if not self.stop:
			self.sumTime += time.time() - self.begin
		if self.sumTime > 0:
			rateData = float(int(self.sumData)/int(self.sumTime))
			print('-'*40 + "\nVideo Data Rate: " + str(rateData) + "\n" + '-'*40)
			rateLoss = float(self.counter/self.frameNbr)
			print('-'*40 + "\nRTP Packet Loss Rate: " + str(rateLoss) + "\n" + '-'*40)

	def pauseMovie(self):
		"""Pause button handler."""
	#TODO
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
	#TODO
		if self.state == self.READY:
			# Create a new thread to listen for RTP packets
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
		self.begin = time.time()
		self.stop = False
		while True:
			try:
				print("LISTENING...")
				data = self.rtpSocket.recv(20480)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)

					self.sumData += len(data)
					
					currFrameNbr = rtpPacket.seqNum()
					print ("CURRENT SEQUENCE NUM: " + str(currFrameNbr))

					try:
						if self.frameNbr + 1 != currFrameNbr:
							self.counter += 1
							print('!'*60 + "\nPACKET LOSS\n" + '!'*60)
						# currFrameNbr = rtpPacket.seqNum()
						# version = rtpPacket.version()
					except:
						print("seqNum() error")
						print('-'*40)
						traceback.print_exc(file=sys.stdout)
						print('-'*40)
										
					if currFrameNbr > self.frameNbr: # Discard the late packet
						self.frameNbr = currFrameNbr
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
				self.sumTime += time.time() - self.begin
				self.stop = True
				# Stop listening upon requesting PAUSE or TEARDOWN
				if self.playEvent.isSet(): 
					break
				
				# Upon receiving ACK for TEARDOWN request,
				# close the RTP socket
				if self.teardownAcked == 1:
					try:
						self.rtpSocket.shutdown(socket.SHUT_RDWR)
						self.rtpSocket.close()
					finally:
						break

		self.sumTime += time.time() - self.begin
		self.stop = True
		
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
	#TODO
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb")
		file.write(data)
		file.close()

		return cachename
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
	#TODO
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image=photo, height=288)
		self.label.image = photo
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
	#TODO
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		
		# Setup request
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()

			# Update RTSP sequence number.
			self.rtspSeq += 1

			# Write the RTSP request to be sent.
			request = "%s %s %s" % (self.SETUP_STR, self.fileName, self.RTSP_VER)
			request += "\nCSeq: %d" % self.rtspSeq
			request += "\nTransport: %s; client_port= %d" % (self.TRANSPORT, self.rtpPort)

			# Keep track of the sent request.
			self.requestSent = self.SETUP

			# Play request
		elif requestCode == self.PLAY and self.state == self.READY:

			# Update RTSP sequence number.
			self.rtspSeq += 1

			# Write the RTSP request to be sent.
			request = "%s %s %s" % (self.PLAY_STR, self.fileName, self.RTSP_VER)
			request += "\nCSeq: %d" % self.rtspSeq
			request += "\nSession: %d" % self.sessionId

			# Keep track of the sent request.
			self.requestSent = self.PLAY

            # Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:

			# Update RTSP sequence number.
			self.rtspSeq += 1

			request = "%s %s %s" % (self.PAUSE_STR, self.fileName, self.RTSP_VER)
			request += "\nCSeq: %d" % self.rtspSeq
			request += "\nSession: %d" % self.sessionId

			self.requestSent = self.PAUSE

			# Teardown request
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:

			# Update RTSP sequence number.
			self.rtspSeq += 1

			# Write the RTSP request to be sent.
			request = "%s %s %s" % (self.TEARDOWN_STR, self.fileName, self.RTSP_VER)
			request += "\nCSeq: %d" % self.rtspSeq
			request += "\nSession: %d" % self.sessionId

			self.requestSent = self.TEARDOWN

		else:
			return

		# Send the RTSP request using rtspSocket.
		self.rtspSocket.send(request.encode())

		print('\nData sent:\n' + request)
	
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
		while True:
			reply = self.rtspSocket.recv(1024)

			if reply:
				self.parseRtspReply(reply)

			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
		lines = data.decode().split('\n')
		seqNum = int(lines[1].split(' ')[1])

		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session

			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200:
					if self.requestSent == self.SETUP:
						#-------------
						# TO COMPLETE
						#-------------

						# Update RTSP state.
						self.state = self.READY

						# Open RTP port.
						self.openRtpPort()
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
					elif self.requestSent == self.PAUSE:
						self.state = self.READY

						# The play thread exits. A new thread is created on resume.
						self.playEvent.set()
					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT

						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		
		# Set the timeout value of the socket to 0.5sec
		# ...
		self.rtpSocket.settimeout(0.5)

		try:
			# Bind the socket to the address using the RTP port given by the client user.
			self.state = self.READY
			self.rtpSocket.bind(('', self.rtpPort))
		except:
			messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO
		self.pauseMovie()
		if messagebox.askokcancel("Exit?", "Are you sure you want to Exit?"):
			self.exitClient()
		else:  # When the user presses cancel, resume playing.
			self.playMovie()
