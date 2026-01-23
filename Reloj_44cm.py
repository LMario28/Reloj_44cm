# NOTAS:

# 1) El orden en los datos del tiempo (tupla) es:
#    Año, mes (1-12), día del mes (1-31), hora (0-23), minuto (0-59), segundo (0-59), día de
#    la semana (0-6 de lunes a domingo), día de año (1-366)

# 2) Pasos para actualizar el sketch en el ESP32

#    Requisitos: 1) Debe estar en donde está la aplicación el sketch ota.py;
#                2) En GitHub, repositorio Aro debe existir  un arhivo con nombre version.json con las lineas:
#                   {
#                     "version":2
#                   }
#                   el número de la versión debe ser mayor que el mismo archivo en el ESP32

#    a) Abrir www.github.com
#    b) lmmsegura@hotmail.com / le...24
#    c) Copiar la nueva versión del sketch a GitHub, repositorio Aro

# 3) Los timers no se borran (pendiente corregir)

import machine
from machine import Pin
import neopixel
import time

import BlynkLib     # https://github.com/vshymanskyy/blynk-library-python/blob/master/examples/03_sync_virtual.py
from BlynkTimer_lmms import BlynkTimer
import network
from ota_deepseek import OTAUpdater
import random
import math

from machine import WDT

#///////////////////////////////////////////////////////////////////////////////
#/                               CONSTANTES                                   //
#///////////////////////////////////////////////////////////////////////////////
WIFI_SSID = ['INFINITUM2426_2.4','Electronica Hotspot PC','TP-Link_LMario']
WIFI_PASS = ['CNnC917MDE','electronica23','lmario28']
SSID=''
PASSWD=''
BLYNK_AUTH = 'AeC4cVG45H4nmiq6g-nFef9-VNfJItuB'


NUMERO_LEDs_RELOJ=120
PERIODO_FLASH_LED=1000
LEDs_HORA=10
LEDs_MINUTO=2

INTERVALO_BASE_ENTRE_TICKS=200                                                      # ms

# Colores navideños
ROJO = (255, 0, 0)
VERDE = (0, 255, 0)
BLANCO = (255, 255, 255)
DORADO = (255, 215, 0)
AZUL = (0, 0, 255)
AMARILLO = (255, 255, 0)
MARRON = (139, 69, 19)                                                         # Color para el tronco
CAFE = (128, 64, 0)                                                            # Color para el tronco

DENSIDAD_COPOS_NIEVE=40

# 16,15,15,15,15,15,15,15,15,15,15,17 LEDs
#define NUMERO_INTENTOS 5

#define MAXIMUN_RETRIES_TO_CONNECT_BLYNK 20                                    //
#define MAXIMUN_ATTEMPTS_TO_RECONNECT_WIFI 18                                  // Intentos maximos para conectarse a la red WiFi
#define TIEMPO_ESPERA_RECONECTAR_BLYNK 30000L                                  // Tiempo de espera par intentar reconectare a Blynk (milliseconds)

# ANIMACIONES
NUMERO_ANIMACIONES=14
#                              Arbol      Copos de     Rotación       Halloween Eyes  Cylon Bounce
#                             navideño     nieve       Navidad
BANDERA_ANIMACION_ACTIVA = [   True,       True,        True,           False,          False,     \
#                             New KITT       Twinkle     Twinkle Random      Sparkle      Snow Sparkle
#                             (Navidad)                     (Navidad)                       (Navidad)
                               False,          False,          False,           False,          False,      \
#                           Running Lights  Color Wipe    Rainbow Cycle    Theater Chase
#                             (Navidad)                     (Navidad)        (Navidad)
                               False,          False,          False,           False                       \
                           ]

#ANIMACION=5                                                                   # 1: Flash LED, 2: Todo blanco, 3: Reloj, 4: Bandera, 5. Fiestas patrias,
ZONA_MEXICO=-6                                                                 # 6. Navidad 1, 7. Navidad 2
WATCHDOG=False
DURACION_CUADRO_ANIMACIONES=5
#NUMERO_ANIMACIONES=5


#///////////////////////////////////////////////////////////////////////////////
#/                               OBJETOS                                    //
#///////////////////////////////////////////////////////////////////////////////
pixels = neopixel.NeoPixel(Pin(16, Pin.OUT), NUMERO_LEDs_RELOJ)
from machine import RTC
(year, month, mday, weekday, hour, minute, second, milisecond)=RTC().datetime()                
if (WATCHDOG):
  wdt = WDT(timeout = 30000)

#///////////////////////////////////////////////////////////////////////////////
#/                               VARIABLES                                    //
#///////////////////////////////////////////////////////////////////////////////
#tiempoLocal=''
#redActiva=0
#fechaHoraInicio=''
#ahorita=''
#diaInicial=''
#timerReloj=''
banderaHoraRecuperadaBlynk=False
opcion_seleccionada_azar=0
i=1
#j=1
#k=0
bandera_reloj=True
bandera_animacion_iniciada=False
#incrementoDecremento=1
#contadorAnimaciones=0

offset=0

#///////////////////////////////////////////////////////////////////////////////
#/                               FUNCIONES                                    //
#///////////////////////////////////////////////////////////////////////////////
#-------------------------------------------------------------------------------
def seleccionarMejorRedWiFiDisponible():
#-------------------------------------------------------------------------------

  global SSID
  global PASSWD
  global redActiva

  wiFi = network.WLAN(network.STA_IF)
  wiFi.active(True)

  authmodes = ['Open', 'WEP', 'WPA-PSK' 'WPA2-PSK4', 'WPA/WPA2-PSK']
  redesWiFiDisponibles = wiFi.scan()
#   for (ssid, bssid, channel, RSSI, authmode, hidden) in redesWiFiDisponibles:
#     print("* {:s}".format(ssid))
#     print("   - Auth: {} {}".format(authmodes[authmode], '(hidden)' if hidden else ''))
#     print("   - Channel: {}".format(channel))
#     print("   - RSSI: {}".format(RSSI))
#     print("   - BSSID: {:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}".format(*bssid))
#     print()

  rssiMasFuerte = 999
  for redWiFi in redesWiFiDisponibles:
    #print ("> " + str(redWiFi[0],"utf-8"))
    #print ("> " + str(redWiFi[3]))
    ssid = str(redWiFi[0],"utf-8")
    try:
      indiceRed = WIFI_SSID.index(ssid)
    except ValueError:
      continue

    SSID = ssid
    PASSWD = WIFI_PASS[indiceRed]
    redActiva = indiceRed + 1
      
    if rssiMasFuerte!=999:
      rssi = str(redWiFi[3])
      if rssi<rssiMasFuerte:
        rssiMasFuerte = rssi
    print("Mejor red disponible:",redActiva,"|",SSID,"|",PASSWD)

#-------------------------------------------------------------------------------
def actualizarSketch():
#-------------------------------------------------------------------------------
  global SSID
  global PASSWD

  firmware_url = "https://raw.githubusercontent.com/LMario28/Reloj_44cm/"

  print("*************************")
  print("ACTUALIZANDO SKETCH...")
  try:
    ota_updater = OTAUpdater(SSID, PASSWD, firmware_url, "Reloj_44cm.py")
    ota_updater.download_and_install_update_if_available()
  except:
    print("NO SE PUDO ACTUALIZAR EL SKETCH")
  print("*************************")

#-------------------------------------------------------------------------------
def desplegarMensajeVisual(tipLla):
#-------------------------------------------------------------------------------
  # Conexión a red WLAN fallida (un parpadeo en rojo)
  if(tipLla==1):
    for i in range(1):
      pixels.fill((255,0,0))
      pixels.write()
      time.sleep(0.25)
      pixels.fill((0,0,0))
      pixels.write()
      time.sleep(0.25)
  # Conexión a red WLAN exitosa (un parpadeo en verde opaco)
  elif(tipLla==2):
    for i in range(1):
      pixels.fill((0,100,0))
      pixels.write()
      time.sleep(0.25)
      pixels.fill((0,0,0))
      pixels.write()
      time.sleep(0.25)
  # Conexión a Blink WLAN exitosa (un parpadeo en verde brillante)
  elif(tipLla==3):
    for i in range(1):
      pixels.fill((0,255,0))
      pixels.write()
      time.sleep(0.25)
      pixels.fill((0,0,0))
      pixels.write()
      time.sleep(0.25)
      
#-------------------------------------------------------------------------------
def actualizarHora():
#-------------------------------------------------------------------------------
  if(not banderaReloj):
    return

  global tiempoLocal

  pixels.fill((0,0,0))
  desplegarEsqueleto()
  desplegarHoraHora()
  desplegarHoraMinuto()
  desplegarHoraSegundo()
  pixels.write()

#-------------------------------------------------------------------------------
def desplegarEsqueleto():
#-------------------------------------------------------------------------------
  # MINUTO MINUTO MINUTO
  for i in range(60):
    pixels[2*i] = (0,4,0)

  # HORA HORA HORA
  pixels[119] = (10,0,10)                                                         # LED 183
  pixels[0] = (10,0,10)
  pixels[1] = (10,0,10)
  for i in range(1,12):
    pixels[10*i-1] = (10,0,10)
    pixels[10*i] = (10,0,10)
    pixels[10*i+1] = (10,0,10)
  print(f"Desplegada la hora: {RTC().datetime()[4]}:{RTC().datetime()[5]}:{RTC().datetime()[6]}")

#-------------------------------------------------------------------------------
def desplegarHoraHora():
#-------------------------------------------------------------------------------
  hora = RTC().datetime()[4]
  if(hora>=12):
    hora -= 12
  ledHoraActual = map(3600 * hora + 60 * RTC().datetime()[5] + RTC().datetime()[6], 0, 43200, 0, NUMERO_LEDs_RELOJ) + 1;
  pixels[ledHoraActual-1] = (255,0,0)
  pixels[ledHoraActual] = (255,0,0)
  pixels[ledHoraActual+1] = (255,0,0)

  pixels[LEDs_HORA*redActiva + 2] = (1,1,1)

#-------------------------------------------------------------------------------
def map(x, in_min, in_max, out_min, out_max):
#-------------------------------------------------------------------------------
  return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min;

#-------------------------------------------------------------------------------
def desplegarHoraMinuto():
#-------------------------------------------------------------------------------
  ledMinutoActual = RTC().datetime()[5] * LEDs_MINUTO
  pixels[ledMinutoActual-1] = (0,255,0)
  pixels[ledMinutoActual] = (0,255,0)

#-------------------------------------------------------------------------------
def desplegarHoraSegundo():
#-------------------------------------------------------------------------------
  ledSegundoActual = RTC().datetime()[6] * LEDs_MINUTO
  pixels[ledSegundoActual] = (255,255,0)

#///////////////////////////////////////////////////////////////////////////////
#/                              LUCES NAVIDEÑAS                               //
#///////////////////////////////////////////////////////////////////////////////
def desplegar_luces_navidenas():

  if (opcion_seleccionada_azar==1):                                            # PINO NAVIDEÑO
    # Semicirculo izquierdo (Copa) (de 9PM a 12PM)
    base_inicio = int(NUMERO_LEDs_RELOJ * 0.70)
    base_fin = NUMERO_LEDs_RELOJ
    for i in range(base_inicio, base_fin):
      intensidad = 100 + int(50 * math.sin(i * 0.2))
      pixels[i] = (0, intensidad, 0)

    # Semicirculo derecho (Copa) (12PM a 3PM)
    base_inicio = 0
    base_fin = int(NUMERO_LEDs_RELOJ * 0.3)
    for i in range(0, int(NUMERO_LEDs_RELOJ * 0.3)):
      intensidad = 100 + int(50 * math.sin(i * 0.2))
      pixels[i] = (0, intensidad, 0)

    # DECORACIONES EN LA COPA DEL ARBOL
    # semicírculo izquierdo
    base_inicio = int(NUMERO_LEDs_RELOJ * 0.70)
    base_fin = NUMERO_LEDs_RELOJ
    for _ in range(12):
      posicion = random.randint(base_inicio, base_fin - 1)
      color = random.choice([ROJO, BLANCO, DORADO, AZUL, AMARILLO])
      pixels[posicion] = color

    # semicírculo derecho
    base_inicio = 0
    base_fin = int(NUMERO_LEDs_RELOJ * 0.3)
    for _ in range(12):
      posicion = random.randint(base_inicio, base_fin - 1)
      color = random.choice([ROJO, BLANCO, DORADO, AZUL, AMARILLO])
      pixels[posicion] = color

    # Estrella en la parte superior (12 PM)
    pixels[NUMERO_LEDs_RELOJ-1] = DORADO
    pixels[0] = DORADO
    pixels[1] = DORADO

    pixels.write()

  elif (opcion_seleccionada_azar==2):                                          # COPOS DE NIEVE
    apagar_todos_leds()
    for _ in range(DENSIDAD_COPOS_NIEVE):
      led = random.randint(0, NUMERO_LEDs_RELOJ - 1)
      intensidad = random.randint(50, 200)
      pixels[led] = (intensidad, intensidad, intensidad)

    pixels.write()

  elif (opcion_seleccionada_azar==3):                                          # ROTACION NAVIDADCOLORES NAVIDEÑOS
    """Rotación de colores navideños en círculo - SOLO CÍRCULO"""
    global offset

    offset = (offset + 1) % NUMERO_LEDs_RELOJ
        
    for i in range(0, NUMERO_LEDs_RELOJ):
      pos_circulo = i
      pos = (pos_circulo - offset) % NUMERO_LEDs_RELOJ
      if pos % 4 == 0:
        pixels[i] = VERDE
      elif pos % 4 == 1:
        pixels[i] = BLANCO
      elif pos % 4 == 2:
        pixels[i] = ROJO
      else:
        pixels[i] = DORADO
        
    pixels.write()

#-------------------------------------------------------------------------------
def apagar_todos_leds():
#-------------------------------------------------------------------------------
  for i in range(NUMERO_LEDs_RELOJ):
    pixels[i] = (0, 0, 0)
  pixels.write()

#///////////////////////////////////////////////////////////////////////////////
#/ PROCESO   PROCESO   PROCESO   PROCESO   PROCESO   PROCESO   PROCESO        //
#///////////////////////////////////////////////////////////////////////////////
#seleccionarMejorRedWiFiDisponible()

seleccionarMejorRedWiFiDisponible()
print("Connecting to WiFi network '{}'".format(SSID))
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID,PASSWD)
if(SSID=="TP-Link_LMario"):
  wifi.ifconfig(("192.168.40.238", "255.255.255.0", "192.168.40.1", "4.2.2.2"))
while not wifi.isconnected():
  time.sleep(5)
  if (WATCHDOG):
    wdt.feed()
  print('WiFi connect retry ...')
print("conectado a:")
print("IP:", wifi.ifconfig()[0])
print("Netmask:", wifi.ifconfig()[1])
print("Gateway:", wifi.ifconfig()[2])
print("DNS:", wifi.ifconfig()[3])

actualizarSketch()

print("Connecting to Blynk server...")
#blynk = BlynkLib.Blynk(BLYNK_AUTH,insecure=True)             // Funciona
blynk = BlynkLib.Blynk(BLYNK_AUTH,server="ny3.blynk.cloud")   # Funciona

# Create BlynkTimer Instance
timer = BlynkTimer()

#///////////////////////////////////////////////////////////////////////////////
#/                               FUNCIONES BLYNK
#///////////////////////////////////////////////////////////////////////////////
@blynk.on("connected")
def blynk_connected(ping):
  desplegarMensajeVisual(3)
  print('Blynk ready. Ping:', ping, 'ms')
  blynk.send_internal("utc","time")
  print('RTC sync request was sent')

@blynk.on("disconnected")
def blynk_disconnected():
    print('Blynk disconnected')
banderaSalida=False

@blynk.on("internal:utc")
def on_utc(value):
  global tiempoLocal,banderaHoraRecuperadaBlynk

  if value[0] == "time":
    ts = int(value[1])//1000
    # on embedded systems, you may need to subtract time difference between 1970 and 2000
    ts -= 946684800
    # Ajuste por zona
    ts += 3600 * ZONA_MEXICO
    tiempoLocal = time.localtime(ts)
    # Año, mes (1-12), día del mes (1-31), hora (0-23), minuto (0-59), segundo (0-59), día de
    # la semana (0-6 de lunes a domingo), día de año (1-366)
    # SINCRONIZACIÓN DEL RELOJ INTERNO E IMPRESIÓN DE FECHA Y HORA
    #RTC().init((year, month, mday, weekday, hour, minute, second, milisecond))
    RTC().init((tiempoLocal[0], tiempoLocal[1], tiempoLocal[2], tiempoLocal[6], tiempoLocal[3], \
                tiempoLocal[4], tiempoLocal[5], milisecond))
    print ("Fecha: {:02d}/{:02d}/{}".format(RTC().datetime()[2],
                                        RTC().datetime()[1],
                                        RTC().datetime()[0]))
    print ("Hora: {:02d}:{:02d}:{:02d}".format(RTC().datetime()[4],
                                           RTC().datetime()[5],
                                           RTC().datetime()[6]))

  #elif value[0] == "tz_name":
    #print("Timezone: ", value[1])

  banderaHoraRecuperadaBlynk=True

#///////////////////////////////////////////////////////////////////////////////
#/                             FIN FUNCIONES BLYNK
#///////////////////////////////////////////////////////////////////////////////

#///////////////////////////////////////////////////////////////////////////////
#/                                   TIMERS
#///////////////////////////////////////////////////////////////////////////////
#timerReloj=timer.set_interval(1,actualizarHora)
#timer.set_interval(60,actualizarSketch)
#///////////////////////////////////////////////////////////////////////////////
#/                                FIN DE TIMERS
#///////////////////////////////////////////////////////////////////////////////
def proceso():
  pass

diaInicial=RTC().datetime()[2]
opcionSeleccionadaAzar=0
random.seed()
banderaAnimacionEstablecida=False
banderaReloj = True

while not banderaHoraRecuperadaBlynk:
  blynk.run()
  timer.run()
blynk.disconnect()
wifi.disconnect()
time.sleep(1)
if not wifi.isconnected():
  print("Desconectado de Blynk y WiFi")
else:
  print("WiFi connected. Can't disconnect")

# CICLO INFINITO EN ESPERA POR EVENTOS
hora_inicial_tarea=time.ticks_ms()-1000
while True:
  try:
    # Posiciones en RTC(): 0. Año; 1: Mes; 2: Día; 4: Hora; 5: Minuto; 6: Segundo
    if (RTC().datetime()[2]!=diaInicial):                                       # Actualizar día
      bandera_animacion_iniciada=False
      opcion_seleccionada_azar=0
      diaInicial = RTC().datetime()[2]

    if (RTC().datetime()[1]==9):                                                # Septiembre
      if (RTC().datetime()[5]%5!=0):
        if (not bandera_reloj):
          #timerReloj = timer.set_interval(1,actualizarHora)
          bandera_reloj = True
          bandera_animacion_iniciada = False
      else:
        if (not bandera_animacion_iniciada):
          #timer._delete(timerReloj)
          #print("Timer del reloj borrado")
          bandera_reloj = False
          if (opcion_seleccionada_azar==0):
            opcion_seleccionada_azar = random.randint(1,1)
          if (opcion_seleccionada_azar==1):
            bandera()
          bandera_animacion_iniciada = True
    elif (RTC().datetime()[1]==12 or (RTC().datetime()[1]==1 and RTC().datetime()[2]<7)):                    # Diciembre|Enero
      if (RTC().datetime()[5]%2!=0):
        if (not bandera_reloj):                                                  # Reloj
          #timerReloj = timer.set_interval(1,actualizarHora)
          bandera_reloj = True
          bandera_animacion_iniciada = False
          print("Desplegando la hora")
        if(time.ticks_ms()-hora_inicial_tarea>1000):
          actualizarHora()
          hora_inicial_tarea = time.ticks_ms()
      else:                                                                    # Animaciones Navideñas
        if (not bandera_animacion_iniciada):
          bandera_reloj = False
          opcion_seleccionada_azar = random.randint(1,3)
          while(not BANDERA_ANIMACION_ACTIVA[opcion_seleccionada_azar-1]):
            opcion_seleccionada_azar = random.randint(1,3)
          apagar_todos_leds()
          hora_inicial_tarea = time.ticks_ms()
          hora_inicial_tick = time.ticks_ms()
          print("Desplegando animaciones navideñas (efecto:",opcion_seleccionada_azar,")")
          if(opcion_seleccionada_azar==1 or opcion_seleccionada_azar==2):
            pass
          elif(opcion_seleccionada_azar==3):
            offset = 0
          desplegar_luces_navidenas()
          bandera_animacion_iniciada = True
        else:
          if(opcion_seleccionada_azar==1 or opcion_seleccionada_azar==2):
            if(time.ticks_ms()-hora_inicial_tick>INTERVALO_BASE_ENTRE_TICKS):
              desplegar_luces_navidenas()
              hora_inicial_tick = time.ticks_ms()
          elif(opcion_seleccionada_azar==3):
            if(time.ticks_ms()-hora_inicial_tick>50):
              desplegar_luces_navidenas()
              hora_inicial_tick = time.ticks_ms()
    else:                                                                       # Otros meses (sólo reloj)
      if(time.ticks_ms()-hora_inicial_tarea>1000):
        actualizarHora()
        hora_inicial_tarea = time.ticks_ms()

  except KeyboardInterrupt:
    print("Deteniendo programa...")
    apagar_todos_leds()
    break

  if (WATCHDOG):
    wdt.feed()

#///////////////////////////////////////////////////////////////////////////////
#/ PROVISIONAL   PROVISIONAL   PROVISIONAL   PROVISIONAL   PROVISIONAL        //
#///////////////////////////////////////////////////////////////////////////////

#///////////////////////////////////////////////////////////////////////////////
#/ FIN PROVISIONAL
#///////////////////////////////////////////////////////////////////////////////
