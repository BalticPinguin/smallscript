#!/usr/bin/python
#include [[functions_smsc.py]]
import functions_smsc as of 
#include [[OPA.py]]
import OPA
#include [[Dusch_unrest.py]]
import Dusch_unrest as DR
#include [[broaden.py]]
import broaden as br
#include further dicts
import sys, re, mmap, numpy as np
from progressbar import ProgressBar
import time

def usage():
   print "usage: smallscript <input-file>"

def invokeLogging(logfile, mode="important"):
   """ initialises the logging-functionality
   ==PARAMETERS==
   logfile      name of file to be used as log-file. It is expected to be an array of length 0 or one.
   mode:        5 different values are possible (see below); the lowest means: print much, higher values mean 
                less printing
   ==RETURNS==
   logging:     number of respective mode
   log:         opened file to write in
   """
   if logfile==[]:
      log=open("calculation.log", "a")
   else:
      s=logfile[0].strip()
      log=open(s, "a")
   if mode in ['all', 'ALL', 'All', '0']:
      logging=0
      log.write('use log-level all\n')
   elif mode in ['detailed', 'DETAILED', 'Detailed', "1"]:
      logging=1
      log.write('use log-level detailed\n')
   elif mode in ['medium', 'MEDIUM','Medium', '2']:
      logging=2
      log.write('use log-level medium\n')
   elif mode in ['important', 'IMPORTANT','Important', '3']:
      logging=3
   elif mode in ['short', 'SHORT','Short', '4']:
      logging=4
   else:
      logging=3
      log.write("logging-mode not recognized. Using 'important' instead\n")
   return logging, log

def main(argv=None):
   assert len(argv)==1, 'exactly one argument required.'
   #pbar = ProgressBar(maxval=100)
   #open input-file (if existent and readable) and map it to f
   try:
      infile=open(argv[0], "r")
      f=mmap.mmap(infile.fileno(), 0, prot=mmap.PROT_READ)
      infile.close()
   except IOError:
      print "file", inputf, "not found."
      usage()
      return 2
   #opts is an array containing all options of respective sub-tasks, which are evaluated in the respective part
   opts=[]
   # todo specifies the sub-tasks to be done in numeral values (powers of 2).
   todo=0
   # here: evaluate the file with respect to the tasks to be done
   if (re.search(r"HR-fact",f, re.I) is not None) is True:
      todo+=1
   opts.append(re.findall(r"(?<=HR-fact)[\w.,\(\) \=;:-]+", f, re.I))
   if (re.search(r"FC-spect",f, re.I) is not None) is True:
      if (re.search(r"HR-file: ",f, re.I) is not None) is True:
         #calculation of HR-facts not neccecary
         todo+=2
      else: #if 
         todo=3
   opts.append(re.findall(r"(?<=FC-spect)[\w\d\.\=,\(\):; -]+",f,re.I))
   if (re.search(r"Duschinsky-spect",f, re.I) is not None) is True:
      if todo==0:
         todo=5
      else:
         todo+=4
   opts.append(re.findall(r"(?<=Duschinsky-spect)[\w:\d\=.\(\),; -]+",f,re.I))
   if ((re.search(r"Broadening",f, re.I) is not None) is True) or\
       ((re.search(r"broaden",f, re.I) is not None) is True):
      todo+=8
   opts.append(re.findall(r"(?<=Broadening)[\w\d\.,:\(\)\=; -]+",f,re.I))
   #error: This should never be true but due to unconvenient option-combinations it may be
   if todo>=16 or todo in [0,4,6,9]: 
      print "options for calculation don't make sense. Please check the input-file!"
      print opts
      return 0
   #invoke logging (write results into file specified by 'out: ' or into 'calculation.log'
   logfile=re.findall(r"(?<=out: )[\.\-_ \w]+",f, re.I)
   if logfile==[]:
      log=open("calculation.log", "a")
   else:
      log=open(logfile[0], "a")
   log.write("\n==================================================================\n"
             "===================  output of smallscript  ======================\n"
             "==================================================================\n\n")
   log.write("   INPUT-FILE:\n")
   log.write(f)
   log.write(" \n   END OF INPUT-FILE \n\n")
   log.write("calculations to be done: %s\n"%(todo))
   log.close()
   
   #update the process-bar. 
   #   (This gives not that satisfying resutls but better than none)
   #pbar.update(5)
   if np.mod(todo,2)==1: 
      #calculation up to HR-facts needed (FC- or Duschinsky spect)
      #first find in where the options for this task are written in
      if opts[0]!=[]:
         opt=opts[0][0]
      elif opts[1]!=[]:
         opt=opts[1][0]
      elif opts[2]!=[]:
         opt=opts[2][0]
      else:
          print 'You want nothing to be calculated? Here it is:\n \n'
          return 2
      #invoke logging: take options of HR-fact, if exists, 
      #       else: from FC-spect, else: from Duschinsky-spect
      loglevel=re.findall(r"(?<=print\=)[\w]+",opt, re.I)
      if loglevel==[]:
         logging=invokeLogging(logfile)
      else:
         logging=invokeLogging(logfile,loglevel[0])
      final=re.findall(r"(?<=final: )[\w.\-]+",f, re.I)
      initial=re.findall(r"(?<=initial: )[\w.\-]+",f, re.I)
      # the calculation of all needed quantities is done in this function
      HRthresh=re.findall(r"(?<=HRthreshold=)[ \d.]+",opt,re.I)
      if HRthresh==[]:
         HRthresh=0.015
      else:
         HRthresh=float(HRthresh[0])
      method=re.findall(r"(?<=method:)[ \w]+",opt, re.I)
      if method==[]:
         logging[1].write("\nUse default method for the calculation of"+
                                                  " all quantities.\n")
         HR, funi, Energy, J, K, f=of.CalculationHR(logging, initial, 
                                                 final, opt, HRthresh)
      else:
         method=re.findall(r"[\w]+",method[0], re.I) # clean by spaces
         if method[0] in ["gradient", "Gradient", 'grad', 
                                    "gradient ", "grad "]:
            logging[1].write("\nUse method %s for the calculation of all quantities.\n"%(method[0]))
            HR, funi, Energy, J, K, f=of.gradientHR(logging, initial, 
                                                final, opt, HRthresh)
         elif (method[0] in ["shift", "SHIFT", "Shift"]) or\
              (method[0] in ["changed", "CHANGED", "Changed"]):
            logging[1].write("\nUse method %s for the calculation of all quantities.\n"%(method[0]))
            HR, funi, Energy, J, K, f=of.CalculationHR(logging, initial, 
                                                   final, opt, HRthresh)
         else:
            logging[1].write("method %s not recognised. Use Shift instead.\n"%(method))
            HR, funi, Energy, J, K, f=of.CalculationHR(logging, initial, 
                                                   final, opt, HRthresh)

   #pbar.update(12)
   if np.mod(todo,4)>=2:
      #calculate FC-spect
      #here exists only one possibility for the options 
      opt=opts[1][0] 
      loglevel=re.findall(r"(?<=print\=)[\w]+",opt, re.I)
      if loglevel==[]:
         try:
            logging[1].close()
            logging=invokeLogging(logfile)
         except UnboundLocalError:
            logging=invokeLogging(logfile)
      else:
         try:
            logging[1].close()
            logging=invokeLogging(logfile, loglevel[0])
         except UnboundLocalError:
            logging=invokeLogging(logfile, loglevel[0])
      try: 
         #test, whether HR-facts were calculated above
         HR
      except NameError:
         #otherwise they have to be extracted from file
         HRfile=re.findall(r"(?<=HR-file: )[\w.,\/\-]+",f, re.I)
         assert len(HRfile)==1, 'There must be exactly one file specified containing HR-facts.'
         initial, HR, funi, E=of.ReadHR(logging, HRfile[0])
         Energy=np.zeros(2)
         Energy[0]=E
         Energy[1]=0
      T=re.findall(r"(?<=T=)[ \=\s\d\.]+", opt, re.M)
      if len(T)==0:
         T=300
      else:
         T=float(T[0])
      if logging[0]<=1:
         logging[1].write("temperature of system: "+repr(T)+"\n")
      T*=8.6173324e-5/27.21138386 # multiplied by k_B in hartree/K
      states=re.findall(r"(?<=states=)[\d ]*", opt, re.I)
      if len(states)==0:
	 states1=5
         states2=0
      else:
	 try:
	    states1=int(states[0])
	    states2=0
	    logging[1].write("number of states: %d and %d \n"%(states1, states2))
	 except ValueError:
            try:
               states1=int(states[0].split(",")[0])
               states2=int(states[0].split(",")[1])
               logging[1].write("number of states: %d and %d \n"%(states1, states2))
            except ValueError:
               states1=5
               states2=0
               logging[1].write("number of vibrational states {0} is not an integer.",
                                    " Use default instead.\n".format(states1, states2))
      Hartree2cm_1=219474.63 
      for j in range(len(HR[0])):
         #print K[j]*K[j]*f[1][j]*0.5*np.pi*0.25, f[1][j]*Hartree2cm_1
         print HR[0][j], funi[1][j]*Hartree2cm_1
      if (re.search(r"changed", opt, re.I) is not None):
         logging[1].write("Calculate the stick-spectrum in FC-picture with %s excitations"\
            " and changing frequencies\n" %(states1) )
         linspect=of.changespect(logging, HR[0], funi, Energy[0]-Energy[1], 0, states1, states2, T)
      else:
         logging[1].write("Calculate the line-spectrum in FC-picture with %s excitations\n."%states )
         linspect=of.calcspect(logging, HR[0], funi[1], Energy[0]-Energy[1], 0, states1, states2, T)
      if ((re.search(r"broaden",opt, re.I) is not None) is True) and todo<8:
         if opts[2]!=[]:
            # i.e.: the FC-spectrum has to be broadened and the Duschinsky-spect to be calculated
            secondlinspect=linspect
         if np.mod(todo,16)<8:
            todo+=8

   #pbar.update(20)
   if np.mod(todo,8)>=4:
      #calculate Duschinsky-spect
      opt=opts[2][0]
      loglevel=re.findall(r"(?<=print\=)[\w]+",opt, re.I)
      if loglevel==[]:
         try:
            logging[1].close()
            logging=invokeLogging(logfile)
         except UnboundLocalError:
            logging=invokeLogging(logfile)
      else:
         try:
            logging[1].close()
            logging=invokeLogging(logfile, loglevel[0])
         except UnboundLocalError:
            logging=invokeLogging(logfile, loglevel[0])
      if (re.search(r"broaden",opt, re.I) is not None) is True and todo<8: 
         if np.mod(todo,16)<8:
            todo+=8
      try: #test, whether HR-facts were calculated above
         J
      except NameError:
         logging[1].write('fatal error: No calculation of first part. But it is required')
         logging[1].close()
         return 2
      T=re.findall(r"(?<=T=)[ \=\s\d\.]+", opt, re.M)
      if len(T)==0:
         T=300
      else:
         T=float(T[0])
      if logging[0]<=1:
         logging[1].write("temperature of system: {0}\n".format(T))
      T*=8.6173324e-5/27.21138386 # multiplied by k_B in hartree/K
      states=re.findall(r"(?<=states=)[ \d]+", opt, re.I)
      if len(states)==0: # i.e. there was no specification by user
	 states=5
      else: 
         # try to read it
	 try:
	    states=int(states[0])
	    logging[1].write("number of states: {0}\n".format(states))
         # if unreadable: take default, but write some comment
	 except ValueError: 
	    logging[1].write("number of vibrational states {0} is not an integer. "
                              "Use default instead.\n".format(states))
	    states=5
      model=re.findall(r"(?<=model\=)[\w]+",opt, re.I)
      # test, if there is a model specified
      try: 
         model=model[0]
      except IndexError:
         #if not, than calculate in resort-model (default).
         for i in range(len(initial)): 
            k=[0,i]
            logging[1].write("\n Use the model 'resort' since none has been specified.\n")
            linspect=OPA.resortFCfOPA(logging, J, K, f[k], Energy[0]-Energy[1], states, T, 0)
      #else: try to find the model, the user wants to use
      if model in ['Simple', 'simple', 'SIMPLE']:
         logging[1].write("\n Use the model %s for the calculation of linespectrum.\n"%(model))
         linspect=OPA.simpleFCfOPA(logging, J, K, f, Energy[0]-Energy[1], states, T, 0)
      elif model in ['Resort', 'resort', 'RESORT']:
         logging[1].write("\n Use the model %s for the calculation of linespectrum.\n"%(model))
         linspect=OPA.resortFCfOPA(logging, J, K, f, Energy[0]-Energy[1], states, T, 0)
      elif model in ['Distributing', 'distributing', 'DISTRIBUTING', 'dist', 'DIST', 'Dist']:
         shifts=re.findall(r"(?<=maxshift\=)[\d]+",opt, re.I)
         if len(shifts)==1:
            logging[1].write("\n Use the model %s for the calculation of linespectrum.\n"
                              "Number of shifts taken into account: %d \n"%(model,int(shifts[0])))
            linspect=OPA.distFCfOPA(logging, J, K, f, Energy[0]-Energy[1], states, T, 0, int(shifts[0]))
         else:
            logging[1].write("\n Use the model %s for the calculation of linespectrum.\n"
                              "Number of shifts not specified, use 6 as default.\n"%(model) )
            linspect=OPA.distFCfOPA(logging, J, K, f, Energy[0]-Energy[1], states, T, 0, 6)
         # the threshold (4) can be made to be a parameter as well
      elif model in ["Unrestricted", 'UNRESTRITED', 'unrestricted', 'unrest']:
         #make 5 (number of excitations), 10 (number of vibrational mode taken into account) to parameters
         modes=re.findall(r"(?<=modes\=)[\d]+",opt, re.I)
         if len(modes)==1:
            logging[1].write("\n Use the model %s for the calculation of linespectrum.\n"
                              "Number of modes to be taken into account:  %s .\n"%(model,int(modes[0])))
            linspect=DR.unrestricted(logging, J, K, f, Energy[0]-Energy[1], states, T, 0, int(modes[0]))
         else:
            logging[1].write("\n Use the model %s for the calculation of linespectrum.\n"
                              "Number of modes to be taken into account not specified, use 10 as default.\n"%(model))
            linspect=DR.unrestricted(logging, J, K, f, Energy[0]-Energy[1], states, T, 0, 10)
      else:
         # i.e.: the model was specified but not found. (give warning and do default)
         logging[1].write('An error occured. The option of "model" is not known! Please check the spelling,'\
               ' meanwile the Duschinsky-rotated spectrum is calculated using "resort".\n')
         linspect=OPA.resortFCfOPA(logging, J, K, f, Energy[0]-Energy[1], states, T, 0)

   #pbar.update(30)
   np.set_printoptions(suppress=True)
   if np.mod(todo,16)>=8:
      #calculate Broadening
      opt=0
      if opts[3]!=[]:
         opt=opts[3][0]
      else:
         for i in range(len(opts)):
            if opts[i]!=[]:
               if (re.search(r"(?<=broaden)[\w\.\-\= ,\(\):]", opts[i][0], re.M) is not None) is True:
                  opt=re.findall(r"(?<=broaden)[\w\.\-\= ,\(\):]+", opts[i][0], re.M)[0]
               break
      if opt==0:
         print 'You want nothing to be calculated? Here it is:\n nothing'
         return 2
      loglevel=re.findall(r"(?<=print\=)[\w]+",opt, re.I)
      if loglevel==[]:
         try:
            logging[1].close()
            logging=invokeLogging(logfile)
         except UnboundLocalError:
            logging=invokeLogging(logfile)
      else:
         try:
            logging[1].close()
            logging=invokeLogging(logfile, loglevel[0])
         except UnboundLocalError:
            logging=invokeLogging(logfile, loglevel[0])
      T=re.findall(r"(?<=T=)[ \=\s\d\.]+", opt, re.M)
      if len(T)==0:
         T=300
      else:
         T=float(T[0])
      T*=8.6173324e-5/27.21138386 # multiplied by k_B in hartree/K
      #test if there exists a line-spectrum already (calculated above
      try:
         linspect 
      except NameError:
         #if not, than extract it from the input-file specified by 'linspect: ' or 'linespect: '
         linespectrum=re.findall(r"(?<=linspect: )[\w\.]+", f, re.I)
         if linespectrum==[]:
            linespectrum=re.findall(r"(?<=linespect: )[\w\.]+", f, re.I)
         assert len(linespectrum)==1, "if no spectrum calculation was done before"+\
                                 ", please specify a file containing line-spectrum."
         freq=[]
         intens=[]
         mode=[]
         with open(linespectrum[0]) as lines:
            lis=[line.split() for line in lines]  # create a list of lists
            for i,x in enumerate(lis):            # print the list items 
               freq.append(float(x[0]))
               intens.append(float(x[1]))
               try:
                  mode.append(float(x[2]))
               except IndexError:
                  mode.append(42)
         linspect=np.zeros((3,len(freq)))
         linspect[0]=np.matrix(freq)
         linspect[1]=np.matrix(intens)
         linspect[2]=np.matrix(mode)
      #pbar.update(50)
      #this is real purpuse of this method; here the broadened spectrum is calculated.
      if re.search(r"broadenparallel", opt, re.I) is not None:
         br.parallelspect(logging, T, opt, linspect)
      else:
         print opt
         br.outspect(logging, T, opt, linspect)
      #pbar.update(80)
      #if to nPA is specified: #### need energy-difference -> need to read it, if spectrum is taken from file...
      try:
         # if FC- and Dusch-spect were calculated; than probably both spectra need to be calculated in broadening...
         secondlinspect
         opt=opts[2][0]
         #pbar.update(50)
         br.outspect(logging, T, opt, linspect)
         #pbar.update(80)
      except NameError:
         opt=opts[0] #do something arbitrary

   logging[1].write("end of calculation reached. Normal exit.\n")
   logging[1].close()
   #pbar.finish()
   
if __name__ == "__main__":
   main(sys.argv[1:])

version=1.5
