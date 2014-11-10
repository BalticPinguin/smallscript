#!/usr/bin/python
#include [[functions_smsc.py]]
import functions_smsc as of 
#include [[OPA.py]]
import OPA 
#include [[broaden.py]]
import broaden as br
#include further dicts
import sys, os, re, mmap, numpy as np

def usage():
   print "usage: smallscript <input-file>"

def invokeLogging(mode="important"):
   """ initialises the logging-functionality
   ==PARAMETERS==
   mode:	5 different values are possible (see below); the lowest means: print much, higher values mean 
		less printing
   ==RETURNS==
   logging: 	number of respective mode
   log:		opened file to write in
   """
   log=open("calculation.log", "a")
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
   # todo specifies the sub-tasks to be done in numerical values (powers of 2).
   todo=0
   # here: evaluate the file with respect to the tasks to be done
   if (re.search(r"HR-fact",f, re.I) is not None) is True:
      todo+=1
   opts.append(re.findall(r"(?<=HR-fact)[\w.,\(\) \=:\-]+", f, re.I))
   if (re.search(r"FC-spect",f, re.I) is not None) is True:
      if (re.search(r"HR-file: ",f, re.I) is not None) is True:
	 #calculation of HR-facts not neccecary
	 todo+=2
      else: #if 
	 todo=3
   opts.append(re.findall(r"(?<=FC-spect)[\w\d\.\=,\(\): -]+",f,re.I))
   if (re.search(r"Duschinsky-spect",f, re.I) is not None) is True:
      if todo==0:
	 todo=5
      else:
	 todo+=4
   opts.append(re.findall(r"(?<=Duschinsky-spect)[\w:\d\=.\(\), -]+",f,re.I))
   if (re.search(r"Broadening",f, re.I) is not None) is True:
      todo+=8
   opts.append(re.findall(r"(?<=Broadening)[\w\d\.,:\(\)\= -]+",f,re.I))
   if todo>=16 or todo==0 or todo in [4,6,9]:
      print "options for calculation don't make sense. Please check the input-file!"
      print opts
      return 0

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
      #invoke logging: take options of HR-fact, if exists, else: from FC-spect, else: from Duschinsky-spect
      loglevel=re.findall(r"(?<=print\=)[\w]+",opt, re.I)
      if loglevel==[]:
	 logging=invokeLogging()
      else:
	 logging=invokeLogging(loglevel[0])
      initial=re.findall(r"(?<=initial: )[\w.]+",f, re.I)
      final=re.findall(r"(?<=final: )[\w.]+",f, re.I)
      ## the calculation of all needed quantities is done in this function
      HR, funi, Energy, J, K, f=of.CalculationHR(logging, initial, final, opt)

   if np.mod(todo,4)>=2:
      #calculate FC-spect
      #here exists only one possibility for the options 
      opt=opts[1][0] 
      loglevel=re.findall(r"(?<=print\=)[\w]+",opt, re.I)
      if loglevel==[]:
	 logging[1].close()
	 logging=invokeLogging()
      else:
	 logging[1].close()
	 logging=invokeLogging(loglevel[0])
      try: 
	 #test, whether HR-facts were calculated above
	 HR
      except NameError:
	 #otherwise they have to be extracted from file
	 HRfile=re.findall(r"(?<=HR-file: )[\w.,\/\-]+",f, re.I)
	 assert len(HRfile)==1, 'There must be exactly one file specified containing HR-facts.'
	 HR, funi, E=of.ReadHR(HRfile[0])
	 Energy=np.zeros(2)
	 Energy[0]=E
	 Energy[1]=0
      T=re.findall(r"(?<=T=)[ \=\s\d\.]+", opt, re.M)
      if len(T)==0:
	 T=300
      else:
	 T=float(T[0])
      if logging[0]<=1:
	 logging[1].write("temperature of system: "+repr(T))
      T*=8.6173324e-5/27.21138386 # multiplied by k_B in hartree/K
      part=re.findall(r"(?<=particles:)[ \d]*", opt, re.I)
      if float(part[0])==1:
	 for i in range(len(initial)):
	    linspect=of.calcspect(logging, HR[i], funi[i], Energy[0]-Energy[1+i], 0, 5, 5, T, "OPA")
      elif float(part[0])==2:
	 for i in range(len(initial)):
	    linspect=of.calcspect(logging, HR[i], funi[i], Energy[0]-Energy[1+i], 0, 5, 5, T, "TPA")
      else:
	 for i in range(len(initial)):
	    linspect=of.calcspect(logging, HR[i], funi[i], Energy[0]-Energy[1+i], 0, 5, 5, T)
      if ((re.search(r"broaden",opt, re.I) is not None) is True) and todo<8:
	 if opts[2]!=[]:
	    ## i.e.: the FC-spectrum has to be broadened and the Duschinsky-spect to be calculated
	    secondlinspect=linspect
	 if np.mod(todo,16)<8:
	    todo+=8

   if np.mod(todo,8)>=4:
      #calculate Duschinsky-spect
      opt=opts[2][0]
      loglevel=re.findall(r"(?<=print\=)[\w]+",opt, re.I)
      if loglevel==[]:
	 logging[1].close()
	 logging=invokeLogging()
      else:
	 logging[1].close()
	 logging=invokeLogging(loglevel[0])
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
      model=re.findall(r"(?<=model\=)[\w]+",opt, re.I)
      try:
	 model=model[0]
      except IndexError:
	 for i in range(len(initial)): 
	    k=[0,i]
	    linspect=OPA.resortFCfOPA(logging, J[i], K[i], f[k], Energy[0]-Energy[1], 5, T, 0)
      if model in ['Simple', 'simple', 'SIMPLE']:
	 for i in range(len(initial)):
	    k=[0,i]
	    ############# make linspect to append; at the moment it will be replaced!!!
	    linspect=OPA.simpleFCfOPA(logging, J[i], K[i], f[k], Energy[0]-Energy[1], 5, T, 0)
      elif model in ['Resort', 'resort', 'RESORT']:
	 for i in range(len(initial)): #calculate separate line-spects for different states
	    k=[0,i]
	    linspect=OPA.resortFCfOPA(logging, J[i], K[i], f[k], Energy[0]-Energy[1], 5, T, 0)
      elif model in ['Distributing', 'distributing', 'DISTRIBUTING', 'dist', 'DIST', 'Dist']:
	 for i in range(len(initial)): #calculate separate line-spects for different states
	    k=[0,i]
	    linspect=OPA.distFCfOPA(logging, J[i], K[i], f[k], Energy[0]-Energy[1], 5, T, 0, 4)
	    # the threshold (4) can be made to be a parameter as well
      else:
	 logging[1].write('An error occured. The option of "model" is not known! Please check the spelling,'\
	       ' meanwile the Duschinsky-rotated spectrum is calculated using "resort".')
	 for i in range(len(initial)):
	    k=[0,i]
	    linspect=OPA.resortFCfOPA(logging, J[i], K[i], f[k], Energy[0]-Energy[1], 5, T, 0)

   if np.mod(todo,16)>=8:
      #calculate Broadening
      opt=0
      if opts[3]!=[]:
	 opt=opts[3][0]
      else:
	 for i in range(len(opts)):
	    if opts[i]!=[]:
	       if (re.search(r"(?<=broaden)[\w\.\-\= ,()]", opts[i][0], re.M) is not None) is True:
	       	  opt=re.findall(r"(?<=broaden)[\w\.\-\= ,()]", opts[i][0], re.M)[0]
	       break
      if opt==0:
	 print 'You want nothing to be calculated? Here it is:\n nothing'
	 return 2
      loglevel=re.findall(r"(?<=print\=)[\w]+",opt, re.I)
      if loglevel==[]:
	 logging[1].close()
	 logging=invokeLogging()
      else:
	 logging[1].close()
	 logging=invokeLogging(loglevel[0])
      T=re.findall(r"(?<=T=)[ \=\s\d\.]+", opt, re.M)
      if len(T)==0:
	 T=300
      else:
	 T=float(T[0])
      T*=8.6173324e-5/27.21138386 # multiplied by k_B in hartree/K

      try:
	 linspect 
      except NameError:
	 linespectrum=re.findall(r"(?<=linspect: )[\w\.]+", f, re.I)
	 if linespectrum==[]:
	    linespectrum=re.findall(r"(?<=linespect:)[ \w\.]+", f, re.I)
	 assert len(linespectrum)==1, "if no spectrum calculation was done before"+\
				 ", please specify a file containing line-spectrum."
	 freq=[]
	 intens=[]
	 mode=[]
	 with open(linespectrum[0]) as lines:
	    ##### handel: also files containing further information!
	    lis=[line.split() for line in lines]  # create a list of lists
	    for i,x in enumerate(lis):        # print the list items 
	       freq.append(float(x[0]))
	       intens.append(float(x[1]))
	       mode.append(float(x[2]))
	 linspect=np.zeros((3,len(freq)))
	 linspect[0]=np.matrix(freq)
	 linspect[1]=np.matrix(intens)
	 linspect[2]=np.matrix(mode)
      ################## change this to make it work with multiple files!!
      br.outspect(logging, T, opt, linspect)
      ###if to nPA is specified: #### need energy-difference -> need to read it, if spectrum is taken from file...
	 #br.outspect(logging, T, opt, linspect, Energy-difference)
      try:
	 # if FC- and Dusch-spect were calculated; than probably both spectra need to be calculated in broadening...
	 secondlinspect
	 opt=opts[2][0]
	 br.outspect(logging, T, opt, linspect)
      except NameError:
	 opt=opts[0] #do something arbitrary

   logging[1].write("end of calculation reached. Normal exit.")
   logging[1].close()
   
if __name__ == "__main__":
   main(sys.argv[1:])

version=1.2
