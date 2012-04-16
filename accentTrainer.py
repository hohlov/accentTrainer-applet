#!/usr/bin/env python
# example of destroy() was taken from http://code.google.com/p/pomodoro-applet/source/browse/trunk/pomodoro-applet.py?r=3


import sys

import gtk
import pygtk
import gnomeapplet
import gobject

import os.path

import pyaudio
import wave
import threading

from SimpleXkbWrapper import SimpleXkbWrapper

pygtk.require('2.0')

def applet_factory(applet, iid):
  Recorder(applet,iid)
  return True



#-------------------------------------------------------------------



  # Final State Machine
class FSM():
  def __init__(self, recorder):
    self.recorder = recorder
    self.state = "waiting"
    self.keyPressedTicks=0
    self.shortPressTicks = 2
    self.wave = []
    self.py_audio = pyaudio.PyAudio()
    self.wavefile = '/tmp/output.wav'

  def destroy(self):
    #print "FSM is being deleting..."
    self.py_audio.terminate()


  def CheckState(self):
    #print self.state

    if self.state == "waiting"   :
        if self.recorder.check_Ctrl_modifier()  :
          self.state = "recording"
          #print "Start recording"
          self.keyPressedTicks = 0

          th= threading.Thread ( None, self.StartRecording )
          th.start()

    elif self.state == "recording"  :
        if self.recorder.check_Ctrl_modifier()  :

            self.keyPressedTicks += 1

            if (self.keyPressedTicks < self.shortPressTicks + 1 )and(self.keyPressedTicks > self.shortPressTicks - 1 ) :
                self.ChangeLabelText("Recording...", 'red')
        else  :
            self.ChangeLabelText("Idle")
            self.state = "waiting"

            if self.keyPressedTicks > self.shortPressTicks  :
                self.SaveRecord()
            else:
                pass#print "didn't save cause of tiks = ", self.keyPressedTicks

            self.CloseRecord()
            self.PlayRecord()

    elif self.state == "playing"  :
      pass

    return True



  def ChangeLabelText(self, str, color="white"):
    self.recorder.label.modify_fg(gtk.STATE_NORMAL,  gtk.gdk.color_parse(color))
    self.recorder.label.set_markup(str)


  def StartRecording(self):
    chunk = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 60

    stream = self.py_audio.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                input = True,
                frames_per_buffer = chunk)

    #print "* recording"

    #while self.state == "recording" :
    for i in range(0, RATE / chunk * RECORD_SECONDS):
        data = stream.read(chunk)
        self.wave.append(data)

        if self.state != "recording" : break

    #print "i=", i
    #print "* done recording"

    stream.close()
    #p.terminate()

  def CloseRecord(self):
      pass


  def SaveRecord(self):
  # write data to WAVE file
        chunk = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        #WAVE_OUTPUT_FILENAME = "output.wav"

        #if os.path.exists("output.wav") :
        #        os.remove('output.wav')

        data = ''.join(self.wave)
        wf = wave.open(self.wavefile, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.py_audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(data)
        wf.close()
        del self.wave[:]

        #print "output.wav has been saved"




  def PlayRecord(self):
      chunk = 1024
      wf = wave.open(self.wavefile, 'rb')

      # open stream
      stream = self.py_audio.open(format =
                self.py_audio.get_format_from_width(wf.getsampwidth()),
                channels = wf.getnchannels(),
                rate = wf.getframerate(),
                output = True)

      # read data
      data = wf.readframes(chunk)

      # play stream
      while data != '':
          stream.write(data)
          data = wf.readframes(chunk)
      wf.close()
      stream.close()

#-------------------------------------------------------------------



class Recorder(gnomeapplet.Applet):
  def __init__(self,applet,iid):
# Initialisation of xkb wrapper
    self.xkb = SimpleXkbWrapper()
    display_name = None
    major_in_out = 1
    minor_in_out = 0
    self.ret = self.xkb.XkbOpenDisplay(display_name, major_in_out, minor_in_out)

# Applet GUI
    self.timeout_interval = 1000 * 1 #Timeout set to 1secs
    self.applet = applet
  # Label
    self.label = gtk.Label("")
    self.label.set_use_markup(True)
    self.label.set_markup("(Idle)")
    self.applet.add(self.label)
  # OnExit event
    self.applet.connect("destroy", self.destroy)


    self.fsm = FSM(self)
# General timer
    gobject.timeout_add(50, self.fsm.CheckState)


    self.applet.show_all()


  def destroy(self, event):
    self.fsm.destroy()
    del self.fsm
    del self.applet
    print "Recorder is being deleting..."

  def check_Ctrl_modifier(self):
    display_handle = self.ret['display_handle']
    device_spec = self.xkb.XkbUseCoreKbd
    xkbstaterec = self.xkb.XkbGetState(display_handle, device_spec)
    #print self.xkb.ExtractLocks(xkbstaterec)
    return xkbstaterec.base_mods & self.xkb.ControlMask !=0

#-------------------------------------------------------------------------

gobject.type_register(Recorder)



#Very useful if I want to debug. To run in debug mode python hindiScroller.py -d
if len(sys.argv) == 2:
	if sys.argv[1] == "-d": #Debug mode
		main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		main_window.set_title("Python Applet")
		main_window.connect("destroy", gtk.main_quit )
		app = gnomeapplet.Applet()
		applet_factory(app,None)
		app.reparent(main_window)
		main_window.show_all()
		gtk.main()
		sys.exit()

#If called via gnome panel, run it in the proper way
if __name__ == '__main__':
  gnomeapplet.bonobo_factory("OAFIID:AccentTrainer_Factory",
    gnomeapplet.Applet.__gtype__, 
    'Accent Trainer', '0.1', 
    applet_factory)
