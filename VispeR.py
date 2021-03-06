#!/usr/bin/python2
# filename: VispeR.py

#include [[Spect.py]]
import Spect

#include [[HR_spects.py]]
import HR_spects as HR

#include [[FC_spects.py]]
import FC_spects as FC

#include [[DR_spects.py]]
import DR_spects as DR

#include [[output_spect.py]]
import output_spect

#include further dicts
import sys, re, mmap, numpy as np
import time

#   CHANGELOG   
#   =========   
#version=2.0.1  
#  1. removed class GFC.  
#  2. added class HR.  
#

def usage():
   print "usage: VispeR <input-file>"

def getModel(f):
   """ This function looks into the input-file 'f' and searches for the option model.
   If it is given, it is evaluated, whether this model is one of the known models.
   If not, or if no model is specified, than the model 'unknown' is used.
   
   The purpose of this function is to have only one name per model in the later programme.

   **PARAMETERS**
   f  is a file-name. It should be in the same folder as where the script is called.

   **OUTPUT**
   model is a string, specifying the given model.

   """
   #search the file
   if (re.search(r"model",f, re.I) is not None) is True:
      model = re.findall(r"(?<=model )[\w]+", f, re.I)
      if model==[]:
	 model = re.findall(r"(?<=model: )[\w]+", f, re.I)
      model=model[-1]
   else:
     #if no model is specified:
     print "You must specify a model to be used."
     model = 'unknown'
   if model in ['HR', 'hr', 'Hr']:
      model = "HR"
   elif model in ['FC', 'fc', 'Fc']:
      model = "FC"
   elif model in ['CFC', 'cfc', 'Cfc']:
      model = "CFC"
   elif model in ['URDR', 'urdr', 'UrDR', 'urDR']:
      model = "URDR"
   elif model in ['DR', 'dr', 'Dr', 'dR']:
      model = "DR"
   else:
      #else: a typo or unknown model is given.
      model = 'unknown'
   return model

def main(argv=None):
   """ This is the main-function of Visper (smallscript). 
      Its input-argument is a file containing all options. 
   
      The main part of the evaluaten of options as well as the
      calculations of all necessary quantiies is performed within the 
      classes. This keeps the main-function clean from technical details.
   """

   #INTRODUCTION START
   assert len(argv)==1, 'exactly one argument required.'
   #open input-file (if existent and readable) and map it to f
   
   # try to open the input-file. If it doesn't exist or one is not alowed to open it,
   # print a usage-information and quit calculation.
   try:
      infile=open(argv[0], "r")
      f=mmap.mmap(infile.fileno(), 0, prot=mmap.PROT_READ)
      infile.close()
   except IOError:
      print "file", argv[0], "not found."
      usage()
      return 2

   #If the input-file exists, get tasks and their options:
   model =getModel(f)

   #look, what kind of spectrum is to be obtained and initialise 
   # an object of respective class. The initialisation-routine
   # already does most of the calculations needed.
   if model == "HR":
      spect = HR.HR_spect(f)
   elif model == "FC":
      spect = FC.FC_spect(f)
   elif model == "CFC":
      spect = FC.CFC_spect(f)
   elif model == "URDR":
      spect= DR.URDR_spect(f)
  # this model is not available at the moment.  
   elif model == "DR":  
      spect = DR.SDR_spect(f)  
   else:
      print "ERROR: error in the model, ", model, "not known."
      return 2
   #INTRODUCTION END

   #import SpecPurpose as sp   
   #vibro=sp.VibDeform(spect,0)   
   #alpha=[-0.5,-0.4,-0.3,-0.2,-0.1,0.1,0.2,0.3,0.4,0.5]   
   #for i in [7,13,25]:   
   #   vibro.printDeformed(i, alpha)   

   #PERFORM CALCULATION OF SPECTRA  
   #At this point, already all necessary quantities are calculated.
   spect.calcspect()
   #FINISHED PERFORM CALCULATION OF SPECTRA

   #do some special-purpose-calculations if wanted.
   
   #with this, the broadened spectrum is calculated.
   broaden=output_spect.broaden(spect)
   broaden.outspect()

   #END PERFORMING CALCULATION OF SPECTRA
    
if __name__ == "__main__":
   main(sys.argv[1:])

version='2.0.1'
# End of VispeR.py
