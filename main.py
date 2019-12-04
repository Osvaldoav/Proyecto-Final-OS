from tabulate import tabulate
import sys

processList = {} # llegada, cpuTotal, I/OTotal, lastCpu, lastI/O
eventTable = []
outputTable = []
colaListos = []
bloqueados = []
terminados = []
quantum = 0
nextCLK = 0
cpu = ''

def llega(timestamp, processID):
  global cpu, nextCLK, processList

  if processID in processList:
    print("Error:\tprocessID %s ya se encuentra en tu lista de procesos")
  else:
    # se agrega a processList con el siguiento formato:
    # [processID] = [tiempo de llegada, tiempo cpu, tiempo I/O, ultima vez en CPU, ultima vez en I/O (bloqueado)]
    processList[processID] = [timestamp, 0, 0, 0, 0] 

  # si no hay nadie en cpu se le asigna directamente
  if cpu == '':
    cpu = processID
    nextCLK = timestamp + quantum # tiempo donde terminara su quantum
    processList[processID][3] = timestamp # ultima vez que entro en CPU
  else:
  # si hay alguien en cpu se manda al final de la cola de listos
    colaListos.append(processID)
  

def acaba(timestamp, processID):
  global cpu, nextCLK, processList

  if not(processID in processList):
    print("Error:\tel proceso %s no se encuentra en la lista de procesos, no se puede determinar tiempo de terminacion" % processID)

  # eliminar de la cola de Listos
  if processID in colaListos:
    colaListos.remove(processID)

  # eliminar de la lista de bloqueados (I/O)
  if processID in bloqueados:
    processList[processID][2] += timestamp - processList[processID][4] # se suma el tiempo que estuvo bloqueado (I/O)
    bloqueados.remove(processID)

  # si el proceso estaba tomando control del cpu....
  if cpu == processID:
    # ahora el primer proceso de la cola de Listos toma el control del cpu en caso de haber alguno
    if colaListos:
      cpu = colaListos.pop(0)
      nextCLK = timestamp + quantum # tiempo donde terminara su quantum
      processList[cpu][3] = timestamp # se guarda la ultima vez que entro en cpu
    else:
      cpu = ''
    processList[processID][1] += timestamp - processList[processID][3] # se suma el tiempo que estuvo en CPU

  endProcess(timestamp, processID) # se calcula time around, tiempo de terminacion, etc.
  terminados.append(processID) # se agrega el proceso a la lista de terminados

def startIO(timestamp, processID):
  global cpu, nextCLK, processList

  if cpu != processID:
    print("Error:\tel proceso %s no puede ejectura una llamada I/O porque no esta ocupando el CPU." % processID)
  else:
    # se asigna al cpu el primer proceso de la cola de Listos de haber alguno
    if colaListos:
      cpu = colaListos.pop(0)
      nextCLK = timestamp + quantum # tiempo donde terminara su quantum
      processList[cpu][3] = timestamp # se guarda la ultima vez que entro en cpu
    else:
      cpu = ''
    bloqueados.append(processID) # se agrega el proceso a la lista de bloqueados (I/O)
    processList[processID][1] += timestamp - processList[processID][3] # se suma el tiempo que estuvo en cpu
    processList[processID][4] = timestamp # ultima vez que entro a la lista de bloqueados (I/O)

def endIO(processID):
  global cpu, nextCLK, processList

  if not(processID in bloqueados):
    print("Error:\tel proceso %s no puede terminar una llamada I/O porque no esta en la lista de bloqueados" % processID)
  else:
    bloqueados.remove(processID) # se elimina el proceso de la lista de bloqueados (I/O)
    processList[processID][2] += timestamp - processList[processID][4] # se suma el tiempo que estuvo en la lista de bloqueados (I/O)
    # si el cpu esta libre...
    if cpu == '':
      cpu = processID # el proceso toma control del cpu
      nextCLK = timestamp + quantum # tiempo donde terminara su quantum
      processList[cpu][3] = timestamp # se guarda la ultima vez que entro en cpu
    # si no, se agrega al final de la cola de listos
    else:
      colaListos.append(processID) 

def endSimulation(line):
  # se anade la ultima linea a la tabla de eventos con el action 'endSimulation'
  addEvent(line)
  # se imprime la tabla de eventos
  print(tabulate(eventTable, headers=['Eventos', 'Cola de Listos', 'CPU', 'Bloqueados', 'Terminados']))
  # se sortea la tabla de procesos
  outputTable.sort()
  # se imprime la tabla de procesos
  print(tabulate(outputTable, headers=['Proceso', 'Tiempo de llegada', 'Tiempo de terminacion','Tiempo de CPU', 'Tiempo de espera', 'Turnaround', 'Tiempo de I/O']))
  sys.exit()

def acaboQuantum(timestamp):
  global cpu, nextCLK, processList

  # si el timestamp actual es mayor al tiempo donde acaba el siguiente quantum...
  while timestamp > nextCLK:
    lastCpu = cpu # se guarda el proceso que acabo su quantum
    if colaListos:
      colaListos.append(cpu) # se manda al proceso que estaba en el cpu al final de la cola de Listas
      cpu = colaListos.pop(0) # se le asigna al cpu el primer proceso de la cola de Listos
    
    processList[lastCpu][1] += nextCLK - processList[lastCpu][3] # se le suma al proceso guardado lastCpu el tiempo que estuvo en cpu
    processList[cpu][3] = nextCLK # se guarda la ultima vez que entro en cpu el proceso que acaba de tomar control del cpu
    addEvent("%s acaboQuantum %s" % (nextCLK, lastCpu))
    nextCLK += quantum # tiempo donde acabara el quantum

def addEvent(line):
  _colaListos = colaListos[:] # copia de la cola de Listos
  _cpu = cpu[:] # copia del cpu
  _bloqueados = bloqueados[:] # copia de la lista de bloqueados
  _terminados = terminados[:] # copia de la lista de terminados
  eventTable.append([line, _colaListos, _cpu, _bloqueados, _terminados]) # se anade una linea a la tabla de eventos

def endProcess(timestamp, processID):
  arriveT, cpuT, ioT = processList[processID][0:3] # se obtienen el tiempo de llegada, tiempo en cpu y tiempo en I/O
  aroundT = timestamp - arriveT # se calcula el time around
  waitT = aroundT - cpuT - ioT # se calcula el tiempo que estuvo en espera

  # se agrega una lina de los procesos con sus respectivos tiempos
  outputTable.append([processID, arriveT, timestamp, cpuT, waitT, aroundT, ioT])

# MAIN
try:
  with open(sys.argv[1]) as fp:
    line = fp.readline().rstrip() # Lee la primera linea del text file y le quita los saltos de linea
    if line != "RR" and line != "FCFS": # Solo soporta RR & FCFS
      print("Error:\t%s no es una politca valida." % (line))
      sys.exit()
    else:
      politica = line # "RR" o "FCFS"

    # Lee segunda linea y obtiene el quantum a utilizar
    quantum = fp.readline().rstrip().split()[1]
    quantum = int(quantum)

    # Itera linea por linea para todo el archivo
    while line:
      line = fp.readline().rstrip() # Elimina saltos de linea
      wordList = line.split() # Divide una linea de texto en palabras
      if len(wordList) > 2: 
        timestamp, action, processID = wordList[0:3] # Si hay mas de 3 palabras se usa un processID
      elif len(wordList) == 2:
        timestamp, action = wordList[0:2] # Si no no
      else:
        print("Error:\t%s **linea invalida**" % line) # Si hay menos de dos palabras por linea, es un error

      timestamp = int(timestamp)

      # Si se acabo el quantum de algun proceso en CPU, se debe de llamar acaboQuantum
      # antes de leer el action de la linea leida
      if politica == "RR" and timestamp > nextCLK:
        acaboQuantum(timestamp)

      # ejecuta una funcion dependiendo su 'action'
      if action == "Llega":
        llega(timestamp, processID)
      elif action == "Acaba":
        acaba(timestamp, processID)
      elif action == "startI/O":
        startIO(timestamp, processID)
      elif action == "endI/O":
        endIO(processID)
      elif action == "endSimulacion":
        endSimulation(line)
      else:
        print("Error:\t%s no es una accion valida." % action)
        sys.exit()
      
      addEvent(line) # se agrega un log del evento

except Exception as ex:
  print ("%s: %s" % (type(ex).__name__, ex.args))