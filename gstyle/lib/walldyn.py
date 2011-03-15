#-*- coding: UTF-8 -*-
from xml.dom.minidom import Document
from xml.dom import minidom


class Hour():
   def fromStr(self, val):
      value1 = val.split(':')
      value2 = value1[1].split()

      self.hour = int(value1[0])
      self.minute = int(value2[0])
      if (value2[1] == "PM" and self.hour != 12):
         self.hour = self.hour + 12
      if (value2[1] != "PM" and self.hour == 12):
         self.hour = 0
      self.hour = divmod(self.hour,24)[1]
      self.minute = divmod(self.minute,60)[1]

   def __init__(self, hour, minute):
      self.hour = divmod(hour,24)[1]
      self.minute = divmod(minute,60)[1]

   def toDelay(self):
      return self.hour*3600 + self.minute*60

   def __lt__(self, other):
      return (self.toDelay() < other.toDelay())

   def __le__(self, other):
      return (self.toDelay() <= other.toDelay())

   def __eq__(self, other):
      return (self.toDelay() == other.toDelay())

   def __ne__(self, other):
      return (self.toDelay() != other.toDelay())

   def __gt__(self, other):
      return (self.toDelay() > other.toDelay())

   def __ge__(self, other):
      return (self.toDelay() >= other.toDelay())

   def addHour(self, hour, minute):
      nbsec = divmod(3600*hour+60*minute+self.toDelay(), 3600*24)[1]
      ret = divmod(nbsec, 3600)
      hour = ret[0]
      minute = divmod(ret[1], 60)[0]
      return Hour(hour, minute)

class CreateXml():
   def __init__(self,sunrise=None, sunset=None):
      self.doc = Document()
      # Creation de la balise background
      self._background = self.doc.createElement("background")
      self.doc.appendChild(self._background)
      # Creation de la balise starttime
      self._starttime = self.doc.createElement("starttime")
      self._background.appendChild(self._starttime)
      # Creation des noeuds de startime
      self._createN(self._starttime,"year","2006")
      self._createN(self._starttime,"month","01")
      self._createN(self._starttime,"days","01")
      # TOCHECK
      # Bug de gnome chez moi? je dois commencer a 1 heure, et faire dans la suite comme ci cela etait 0h.
      # sinon au lieu d'avoir un apres midi (2.jpg) jusqu'a 5pm, je l'ai jusqu'a 4pm (pb heure gmt?)
      self._createN(self._starttime,"hour","1")
      self._createN(self._starttime,"minute","00")
      self._createN(self._starttime,"second","00")
#
#      if (sunrise >= Hour(11,0)) :
#         sunrise = Hour(11,0)
#      elif (sunrise <= Hour(2,30)) :
#         sunrise = Hour(2,30)
#
#      if (sunset <= Hour(15,0)) :
#         sunset = Hour(15,0)
#      elif (sunset >= Hour(22,0)) :
#         sunset = Hour(22,0)

      # 2h30 <= sunrise <= 11h
      # 15h <= sunset <= 22h

#      t1 = sunrise.addHour(-1,-30)
#
#      t2 = sunrise
#
#      t3 = sunrise.addHour(1,30)
#
#      t4 = Hour(13,0)
#
#      t5 = sunset.addHour(-1,-30)
#
#      t6 = sunset
#
#      t7 = sunset.addHour(1,30)
#
#      t8 = Hour(0,0)


#      self._createNStatic(str(t8.DelayUntil(t1)),  path + "4.jpg")
#
#      self._createNTransition(str(t1.DelayUntil(t2)), path + "4.jpg", path + "1.jpg")
#
#      self._createNStatic(str(t2.DelayUntil(t3)),  path + "1.jpg")
#
#      self._createNTransition(str(t3.DelayUntil(t4)), path + "1.jpg",path + "2.jpg")
#
#      self._createNStatic(str(t4.DelayUntil(t5)),  path + "2.jpg")
#
#      self._createNTransition(str(t5.DelayUntil(t6)), path + "2.jpg",path + "3.jpg")
#
#      self._createNStatic(str(t6.DelayUntil(t7)),  path + "3.jpg")
#
#      self._createNTransition(str(t7.DelayUntil(t8)), path + "3.jpg",path + "4.jpg")

   def _createNoeud(self,nom):
      noeud = self.doc.createElement(nom)
      return noeud

   def _createN(self,pere,fils,valeur=""):
      fils = self._createNoeud(fils)
      texte = self.doc.createTextNode(valeur)
      fils.appendChild(texte)
      pere.appendChild(fils)

   def _createNStatic(self,durer,fichier):
      static = self.doc.createElement("static")
      self._background.appendChild(static)
      self._createN(static,"duration",durer)
      self._createN(static,"file",fichier)

   def _createNTransition(self,durer,fichier1,fichier2,mode="overlay"):
      transition = self.doc.createElement("transition")
      transition.setAttribute("type", mode)
      self._background.appendChild(transition)
      self._createN(transition,"duration",durer)
      self._createN(transition,"from",fichier1)
      self._createN(transition,"to",fichier2)


class Diaporama(list):
    def generate(self,path):
        if self:
            xml = CreateXml()
            for item in self:
                if item["type"] == "static":
                    path = item["wallpaper"].get_filename()
                    xml._createNStatic(item["duration"],path)
                elif item["type"] == "transition":
                    path1 = item["wallpaper1"].get_filename()
                    path2 = item["wallpaper2"].get_filename()
                    xml._createNTransition(item["duration"],path1,path2)
            #TODO record xml


    def add_static(self,wallpaper,duration):
        self.append({"type":"static","wallpaper":wallpaper,"duration":duration})

    def add_transition(self,wallpaper1,wallpaper2,duration):
        self.append({"type":"transition","wallpaper1":wallpaper1,"wallpaper2":wallpaper2,"duration":duration})


if __name__ == "__main__":
    pass

