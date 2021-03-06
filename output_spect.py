#!/usr/bin/python,2
# filename: output_spect.py

#include [[MultiPart.py]]
import MultiPart
import numpy as np
import re 

# CHANGELOG
# =========
#in version 0.1.0:  
#   1) intitialised class
#   2) fixed class-related issues (missing self.)
#   3) Added function concise to speed-up calculations.
#

class broaden():
   """ This class computes the broadened spectrum out of a stick-spectrum.
         
       **Interface functions **
       init     - initialisation of the class. Its argument is a pointer 
                  to a class of type Spect (or inherited from it); than
                  all required quantities are copied from there.
       outspect - computes the broadened spectrum and saves it to a file.
   """
   #set default values (to have all variables set)
   gridfile=None
   gamma=1 #by default: only slight broadening
   gridpt=5000
   omega=None
   minfreq=0
   maxfreq=0
   shape='g'
   stick=False
   log=""
   shorten=False

   #BEGIN DEFINITION OF METHODS
   def __init__(self, parent):
      """ initialise the quantities needed for the calculation of
         broadened spectrum
      """
      #get a pointer to parent-object that e.g. has the stick-spectrum
      self.parent=parent
      self.log=self.parent.log

      #get some information about the grid
      tmpgrid=re.findall(r"(?<=grid=)[\s\w\.;]+", parent.broadopt, re.M)
      if (tmpgrid==[]):
         tmpgrid=re.findall(r"(?<=grid=)[ \s\w\.;]+", parent.broadopt, re.M)
      if len(tmpgrid)==1: 
         # i.e. if grid is specified
         grid=re.findall(r"[\w\.]+", tmpgrid[0], re.M)
         if len(grid)==1:
            #that means, if either one number (# of gridpoints or a file) is given
            try:
               self.gridpt=float(grid[0])
            except ValueError: # if grid is no a number
               self.gridfile=grid[0]
         elif len(grid)==3:
            # that means there is the number of gridpoints, min- and max frequency given
            self.gridpt=float(grid[0])
            self.minfreq=float(grid[1])
            self.maxfreq=float(grid[2])
         else:
            self.log.write("\n WARNING: Grid was specified but not recognised!\n")
   
         if self.gridfile!=None:
               #read file in format of spect
               grid=[]
               with open(self.gridfile) as f:
                  lis=[line.split() for line in f]  # create a list of lists
                  for i,x in enumerate(lis):        # get the list items 
                     grid.append(float(x[0]))
               self.omega=np.zeros(len(grid))
               for i in range(len(grid)):
                  self.omega[i]=grid[i]

      #see, whether a broadening is given
      if (re.search(r"(?<=gamma=)[ \d\.,]+", parent.broadopt, re.I) is not None)  is True:
         gamma=re.findall(r"(?<=gamma=)[ \d\.]+", parent.broadopt, re.I)
         self.gamma=float(gamma[0])
   
      #which line shape function should be used?
      # FIXME: also some Voigt-profile should be possible here.
      shape=re.findall(r"(?<=shape=)[\w]+", parent.broadopt, re.I)
      if len(shape)==[]:
         shape=re.findall(r"(?<=shape= )[\w]+", parent.broadopt, re.I)
      if len(shape)>0:
      # there are several options each
         if shape[0] in ["lorentzian", "Lorentzian", "L", "l"]:
            self.shape="l"
         elif shape[0] in ["gaussian", "Gaussian", "G", "g"]:
            self.shape="g"

      # should the stick-spectrum be printed?
      if (re.search(r"stick", parent.broadopt, re.I) is not None) is True:
         self.stick=True
      if (re.search(r"shorten", parent.broadopt, re.I) is not None) is True:
         self.shorten=True
     
      #output-file for the broadened spectrum
      spectfile=re.findall(r"(?<=spectfile=)[\w._\-]+", parent.broadopt, re.I)
      if spectfile==[]:
         spectfile=re.findall(r"(?<=spectfile= )[\w._\-]+", parent.broadopt, re.I)
         if spectfile==[]:
            self.spectfile=None
         else:
            self.spectfile=spectfile[-1]
      else:
         self.spectfile=spectfile[-1]

   def outspect(self, E=0):
      """This function calculates the broadened spectrum given the line spectrum, 
         frequency-rage and output-file whose name is first argument. 
         As basis-function a Lorentzian is assumed with a common width.
      
         **PARAMETERS:**
         E:       energy-shift of the 0-0 transition. Important if the excited 
                  state is not the lowest and
                  thermal equilibration with the lower states should be considered
   
         **RETURNS:**
         nothing; the key values (broadened spectra/ many-particle-app. 
                  linespectra) are printed into log-files.
         
      """

      minint=0
      self.log.write("\n STARTING TO CALCULATE BROADENED SPECTRUM.\n")
      self.spect=self.parent.spect

      #sort spectrum with respect to size of elements
      index=np.argsort(self.spect[1], kind='heapsort')
      self.spect[0]=self.spect[0][index] #frequency
      self.spect[1]=self.spect[1][index] #intensity
      self.spect[2]=self.spect[2][index] #mode
      #find transition with minimum intensity to be respected
   
      #truncate all transitions having less than 0.0001% of
      for i in range(len(self.spect[1])):
         if self.spect[1][i]>=1e-6*self.spect[1][-1]:
            minint=i
            break
      self.log.write('neglect '+repr(minint)+' transitions, use only '+
                                repr(len(self.spect[1])-minint)+" instead.\n", 3)
   
      self.log.write('minimal and maximal intensities:\n'+
              repr(self.spect[1][minint])+' '+repr(self.spect[1][-1])+"\n", 2)
      
      #important for later loops: avoiding '.'s speeds python-codes up!!
      logwrite=self.log.write  

      #make nPA from OPA if requested.
      n=re.findall(r"(?<=to nPA:)[ \d]*", self.parent.broadopt, re.I)
      if n!=[]:
         MakeFull=MultiPart.OPAtoNPA(float(n[-1].strip()))
         logwrite("\n REACHING OPA TO NPA-PART. \n")
         logwrite(" ----------------------------------------"+
                                                 "-------- \n")
         MakeFull.GetSpect(self.spect, minint)
         TPAintens, TPAfreq=MakeFull.Calc()
         
         #sort spectrum with respect to size of intensities
         index=np.argsort(self.spect[1], kind='heapsort')
         self.spect[0]=self.spect[0][index] #frequency
         self.spect[1]=self.spect[1][index] #intensity
         self.spect[2]=self.spect[2][index] #mode
         #find transition with minimum intensity to be respected
      
         #truncate all transitions having less than 0.0001% of
         for i in range(len(self.spect[1])):
            if self.spect[1][i]>=1e-6*self.spect[1][-1]:
               minint=i
               break
      else: 
         TPAfreq=self.spect[0][minint:]
         TPAintens=self.spect[1][minint:]

      #needed for DR spectra:
      norm=np.sum(TPAintens)
      TPAintens/=norm
            
      #find transition with minimum intensity to be respected
      #the range of frequency ( should be greater than the transition-frequencies)
      if self.omega==None:
         if self.minfreq==0:
            self.minfreq=np.min(TPAfreq)-20-self.gamma*15
         if self.maxfreq==0:
            self.maxfreq=np.max(TPAfreq)+20+self.gamma*15
         #if no other grid is defined: use linspace in range
         self.omega=np.linspace(self.minfreq,self.maxfreq,self.gridpt)
         self.log.write("omega is equally spaced\n",2)
      else:
         self.minfreq=self.omega[0]
         self.maxfreq=self.omega[-1]
      self.log.write('maximal and minimal frequencies:\n {0} {1}\n'.format(self.maxfreq, self.minfreq), 3)
   
      if self.gamma*1.1<=(self.maxfreq-self.minfreq)/self.gridpt:
         self.log.write("\n WARNING: THE GRID SPACING IS LARGE COMPARED TO THE WIDTH OF THE PEAKS.\n"
              "THIS CAN ALTER THE RATIO BETWEEN PEAKS IN THE BROADENED SPECTRUM!")
   
      index=np.argsort(TPAfreq,kind='heapsort') #sort by freq
      freq=TPAfreq[index]
      intens=TPAintens[index]

      #print the stick-spectrum to a .stick-file, if it was requested:
      if self.stick:
         stickfile=self.parent.log.logfile.split(".")[0]
         stickout=open(stickfile+".stick", "w")
         stickout.write(" Intensity  \t frequency \n")
         for i in range(len(freq)):
            stickout.write(" %3.6g  \t %3.6f\n"%(intens[i],freq[i]))
         stickout.close()
   
      if self.spectfile==None:
         self.out=self.log
      else:
         self.out = open(self.spectfile, "w")
   
      if self.spectfile==None: #that means spectrum is printed into log-file
         logwrite("broadened spectrum:\n frequency      intensity\n")
      if self.shape=='g':
         self.__broadenGauss(intens, freq)
      else:  #shape=='l':
         self.__broadenLorentz(intens, freq)
      if self.spectfile!=None:
         #only close file if it was opened here
         self.out.close()

   def __broadenGauss(self, intens, freq):
      """This private function does the actual computation of the spectrum
         in case of a Gaussian as line spape function.
         The intensities and frequencies are required to be sorted by increasing
         frequencies.
      """
      gamma=self.gamma
      sigma=gamma*2/2.355 #if gaussian used: same FWHM
      omega=self.omega
      sigmasigma=2.*sigma*sigma # these two lines are to avoid multiple calculations of the same
      npexp=np.exp
      norm=1./np.sqrt(np.pi*sigmasigma)
      outwrite=self.out.write

      #this shrinks the size of the spectral lines; hopefully accelerates the script.
      if self.shorten:
         intens, freq=concise(intens, freq, sigma)
      assert len(freq)>0, "No transitions are given."
      lenfreq=len(freq)
      maxi=lenfreq-1 #just in case Gamma is too big or frequency-range too small
      mini=0
      # set the largest index to be taken into account for the first transition.
      for i in range(0,lenfreq-1):
         if freq[i]>=10*sigma+freq[0]:
            maxi=i
            break

      # go through grid for the broadened spectrum and
      # compute the intensity at this point.
      for i in xrange(len(omega)): 
         omegai=omega[i]
         #re-adjust the limits for the transitions to be taken into account at this point
         for j in range(maxi,lenfreq):
            #print j, lenfreq, len(freq)
            if freq[j]>=10*gamma+omegai:
               maxi=j
               break
         for j in range(mini,maxi):
            if freq[j]>=omegai-10*gamma:
               # else it becomes -1 and hence the spectrum is wrong
               mini=max(j-1,0) 
               break
         spect=0
         #sum up all contributions of neighbouring transitions.
         for k in range(mini,maxi+1):
            spect+=norm*intens[k]*npexp((omegai-freq[k])*(freq[k]-omegai)/sigmasigma )
         #write the value to file
         outwrite(u" %f  %e\n" %(omegai, spect))

   def __broadenLorentz(self, intens, freq):
      """This private function does the actual computation of the spectrum
         in case of a Lorentzian as line spape function.
         The intensities and frequencies are required to be sorted by increasing
         frequencies.
      """
      gamma=self.gamma
      omega=self.omega
      gammagamma=gamma*gamma
      norm=gamma/np.pi
      outwrite=self.out.write
      
      #this shrinks the size of the spectral lines; hopefully accelerates the script.
      if self.shorten:
         intens, freq=concise(intens,freq, sigma)
      lenfreq=len(freq)
      maxi=lenfreq-1 #just in case Gamma is too big or frequency-range too low
      mini=0
      for i in range(0,lenfreq-1):
         if freq[i]>=10*self.gamma+freq[0]:
            maxi=i
            break
      
      # go through grid for the broadened spectrum and
      # compute the intensity at this point.
      for i in xrange(len(omega)): 
         omegai=omega[i]
         #re-adjust the limits for the transitions to be taken into account at this point
         for j in range(maxi,lenfreq):
            if freq[j]>=10*gamma+omegai:
               maxi=j
               break
         for j in range(mini,maxi):
            if freq[j]>=omegai-10*gamma:
               # else it becomes -1 and hence the spectrum is wrong
               mini=max(j-1,0) 
               break
         omegai=omega[i]
         spect=0
         #sum up all contributions of neighbouring transitions.
         for k in range(mini,maxi+1):
            spect+=norm*intens[k]/((omegai-freq[k])*(omegai-freq[k])+gammagamma)
         #write the value to file
         outwrite(u" %f   %e\n" %(omegai, spect))
   #END DEFINITION OF METHODS
   
def concise(intens, freq, sigma):
   """ This function shrinks length of the stick-spectrum to speed-up the 
      calculation of broadened spectrum (folding with lineshape-function).
      It puts all transitions within a tenth of the Gaussian-width into one line.
   
      ==PARAMETERS==
      intens:    vector containing the intensities of the stick spectrum
      freq:      vector containing the frequencies of the stick spectrum
                 vectors need to be sorted by frequency.
      sgima:     width of the lineshape function; specifying, 
                 how many lines will be put together
   
      ==RETURNS==
      Sintens:     shrinked intensity-vector, sorted by increasing frequency
      Sfreq:       shrinked frequency-vector, sorted by increasing frequency
   """
   Sintens=[]
   Sfreq=[]
   tmpintens=0
   endfreq=freq[0]+sigma/10.
   startfreq=freq[0]
   startind=0
   for i in range(1,len(freq)):
      if freq[i]>endfreq:
         #add the respective transition:
         if startind==i-1:
            Sfreq.append(freq[i-1])
            Sintens.append(tmpintens)
         else:
            #chose the frequency as average over transitions
            Sfreq.append(sum(freq[startind:i-1])/(i-1-startind))
            Sintens.append(tmpintens)
         startind=i
         tmpintens=0
         endfreq=freq[i]+sigma/10
      tmpintens+=intens[i]
   #add the last transitions:
   if startind==len(freq)-1:
      Sfreq.append(freq[-1])
      Sintens.append(tmpintens)
   else:
      #chose the frequency as average over transitions
      Sfreq.append(sum(freq[startind:])/len(freq[startind:]))
      Sintens.append(tmpintens)
   #for i in range(len(Sfreq)):
   #   print Sintens[i], Sfreq[i]
   return Sintens, Sfreq
      
version='0.1'
#End of output_spect.py
