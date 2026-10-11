#include <Arduino.h>

// ==================== DRIVER DEL MOTOR ====================
// Driver A4988 (confirmado por el chip impreso) sobre placa portadora HW-434
// VDD del driver alimentado a 3.3V (pin 3V3 del Nano ESP32)
// RESET y SLEEP puenteados a 3.3V (son activos en bajo, deben quedar en HIGH)
// MS1/MS2/MS3 en ON (HIGH) -> modo de microstepping 1/16 del A4988.
const int PIN_STEP = D2; // STEP / PUL
const int PIN_DIR   = D3; // DIR
const int PIN_EN    = D4; // ENABLE (activo en LOW)

const int MICROSTEPS = 16; // MS1/MS2/MS3 en ON en el A4988 -> 1/16 de paso
const int PASOS_POR_VUELTA = 200 * MICROSTEPS; // NEMA típico: 200 pasos/vuelta en full-step, x microstepping real

const unsigned long DELAY_MIN_US = 100;    // límite físico razonable, más rápido que esto no se garantiza
const unsigned long DELAY_MAX_US = 200000; // ~0.15 RPM, por debajo de esto ya es "parado"

float rpmActual = 0;          // 0 = motor detenido
unsigned long delayUs = 0;    // tiempo en HIGH y en LOW por paso

// ==================== POTENCIÓMETRO ====================
const int PIN_POTENCIOMETRO = A0;
const int ADC_RESOLUCION_BITS = 12;
const int ADC_MAX = (1 << ADC_RESOLUCION_BITS) - 1; // 4095

const float POT_RPM_MIN = -60.0; // negativo = sentido de giro invertido
const float POT_RPM_MAX = 60.0;  // ajustar según la velocidad máxima útil para tu aplicación

// Histéresis en cuentas de ADC: evita que ruido del potenciómetro dispare
// actualizaciones (y mensajes por Serial) constantemente.
const int POT_UMBRAL_CUENTAS = 40; // ~1% de 4095

// Zona muerta cerca del centro del potenciómetro: sin esto, sería casi
// imposible por ruido del ADC que el poti caiga justo en 0.0 exacto, y el
// motor nunca llegaría a "detenido" del todo (quedaría girando muy lento
// cerca del centro). Cualquier RPM pedido con |rpm| menor a esto se trata
// como 0 (detenido).
const float POT_ZONA_MUERTA_RPM = 1.0;

int potUltimaLecturaAplicada = -1; // -1 fuerza que la primera lectura siempre se aplique

// ==================== DISPLAY 7 SEGMENTOS x4 (cátodo común, multiplexado) ====================
// Convención según datasheet del display:
//   - Pines 1-4 (comunes de cada dígito) -> van a GND cuando ese dígito está activo (cátodo común)
//   - Pines a-g + dp (aquí "h" = dp, el punto decimal) -> van a +V a través de resistencia
//     limitadora cuando ese segmento está encendido
//
// Mapeo elegido a pines del Nano ESP32 (libres: no chocan con D2/D3/D4 del driver
// ni con A0 del potenciómetro; se dejan A4/A5 libres por si luego se usa I2C):
//
//   Señal display      Pin Nano ESP32
//   ----------------   --------------
//   Segmento a          D5
//   Segmento b          D6
//   Segmento c          D7
//   Segmento d          D8
//   Segmento e          D9
//   Segmento f          D10
//   Segmento g          D11
//   Segmento dp ("h")   D12
//   Dígito 1 (común)    D13
//   Dígito 2 (común)    A1
//   Dígito 3 (común)    A2
//   Dígito 4 (común)    A3
//
// IMPORTANTE - hardware:
//   1) El Nano ESP32 trabaja a 3.3V logicos (NO 5V tolerante). Si el datasheet del display
//      está pensado para 5V, recalculá las resistencias limitadoras para 3.3V (normalmente
//      un valor algo menor da brillo similar). Empezá con algo conservador (ej. 220-330 ohm)
//      y ajustá el brillo a gusto.
//   2) Cuidado con la corriente en el pin de cada dígito: si se encienden varios segmentos
//      a la vez (ej. dígito "8" con punto decimal = 8 segmentos), ese pin debe "hundir" la
//      suma de todas esas corrientes. Eso puede superar el máximo recomendado de un GPIO
//      (~20mA, absoluto ~40mA en ESP32-S3). Lo más seguro es NO conectar el común del dígito
//      directo al GPIO, sino a través de un transistor NPN (ej. 2N2222/BC337): GPIO -> resistencia
//      base (~1k) -> base del transistor; colector -> común del dígito; emisor -> GND.
//      Si hacés eso, DIGITO_ACTIVO_EN_ALTO debe ir en true. Como en este proyecto el común
//      está conectado directo al GPIO (sin transistor ni resistencias limitadoras, por decisión
//      consciente del usuario), queda en false: el GPIO debe ponerse en LOW para "hundir" la
//      corriente del dígito seleccionado.
const int PIN_SEG_A  = D5;
const int PIN_SEG_B  = D6;
const int PIN_SEG_C  = D7;
const int PIN_SEG_D  = D8;
const int PIN_SEG_E  = D9;
const int PIN_SEG_F  = D10;
const int PIN_SEG_G  = D11;
const int PIN_SEG_DP = D12;

const int PINES_SEGMENTOS[8] = {PIN_SEG_A, PIN_SEG_B, PIN_SEG_C, PIN_SEG_D,
                                 PIN_SEG_E, PIN_SEG_F, PIN_SEG_G, PIN_SEG_DP};

const int PIN_DIGITO_1 = D13;
const int PIN_DIGITO_2 = A1;
const int PIN_DIGITO_3 = A2;
const int PIN_DIGITO_4 = A3;

const int PINES_DIGITOS[4] = {PIN_DIGITO_1, PIN_DIGITO_2, PIN_DIGITO_3, PIN_DIGITO_4};

const bool SEGMENTO_ACTIVO_EN_ALTO = true;  // cátodo común: segmento se enciende con el pin en HIGH
const bool DIGITO_ACTIVO_EN_ALTO   = false; // false = común del dígito conectado directo al GPIO (este caso)
                                             // true = común manejado vía transistor NPN (recomendado)

// Patrones de segmentos a,b,c,d,e,f,g para cada dígito 0-9 (true = encendido)
const bool PATRONES_DIGITOS[10][7] = {
    {1, 1, 1, 1, 1, 1, 0}, // 0
    {0, 1, 1, 0, 0, 0, 0}, // 1
    {1, 1, 0, 1, 1, 0, 1}, // 2
    {1, 1, 1, 1, 0, 0, 1}, // 3
    {0, 1, 1, 0, 0, 1, 1}, // 4
    {1, 0, 1, 1, 0, 1, 1}, // 5
    {1, 0, 1, 1, 1, 1, 1}, // 6
    {1, 1, 1, 0, 0, 0, 0}, // 7
    {1, 1, 1, 1, 1, 1, 1}, // 8
    {1, 1, 1, 1, 0, 1, 1}, // 9
};
const bool PATRON_BLANCO[7] = {0, 0, 0, 0, 0, 0, 0}; // dígito apagado
const bool PATRON_GUION[7]  = {0, 0, 0, 0, 0, 0, 1}; // "-" (motor detenido)

const int DIGITO_BLANCO = -1;
const int DIGITO_GUION  = -2;

int valoresDisplay[4]       = {DIGITO_BLANCO, DIGITO_BLANCO, DIGITO_BLANCO, DIGITO_BLANCO};
bool puntoDecimalDisplay[4] = {false, false, false, false};

const unsigned long REFRESCO_DIGITO_US = 2000; // ~2ms por dígito -> ciclo completo ~8ms (125Hz, sin parpadeo)
unsigned long ultimoCambioDigitoUs = 0;
int digitoActivo = 0;

// ==================== DISPLAY: funciones auxiliares ====================
const bool* obtenerPatronSegmentos(int valor) {
  if (valor == DIGITO_BLANCO) return PATRON_BLANCO;
  if (valor == DIGITO_GUION) return PATRON_GUION;
  if (valor >= 0 && valor <= 9) return PATRONES_DIGITOS[valor];
  return PATRON_BLANCO;
}

void escribirSegmento(int pin, bool encendido) {
  bool nivelAlto = SEGMENTO_ACTIVO_EN_ALTO ? encendido : !encendido;
  digitalWrite(pin, nivelAlto ? HIGH : LOW);
}

void apagarTodosLosDigitos() {
  for (int i = 0; i < 4; i++) {
    digitalWrite(PINES_DIGITOS[i], DIGITO_ACTIVO_EN_ALTO ? LOW : HIGH);
  }
}

void seleccionarDigito(int indice) {
  digitalWrite(PINES_DIGITOS[indice], DIGITO_ACTIVO_EN_ALTO ? HIGH : LOW);
}

// Recalcula qué dígitos/segmentos hay que mostrar según el RPM actual.
// Formato: signo (si es negativo) + 2 dígitos enteros + 1 decimal
// (ej. -30.5 -> "-30.5", 5.5 -> " 5.5"). El primer dígito físico se
// reutiliza como signo en vez de dejarlo en blanco, ya que con rango
// ±60 nunca hacen falta 3 dígitos enteros. Si el motor está detenido,
// muestra "----".
void actualizarValoresDisplay() {
  if (rpmActual == 0) {
    for (int i = 0; i < 4; i++) {
      valoresDisplay[i] = DIGITO_GUION;
      puntoDecimalDisplay[i] = false;
    }
    return;
  }

  bool negativo = rpmActual < 0;
  long escalado = lround(fabs(rpmActual) * 10.0); // un decimal de precisión, sobre el valor absoluto
  if (escalado > 999) escalado = 999;              // límite físico: 2 enteros + 1 decimal (99.9)

  int digitoDecenas = (escalado / 100) % 10;
  int digitoUnidades = (escalado / 10) % 10;
  int digitoDecimal = escalado % 10;

  valoresDisplay[0] = negativo ? DIGITO_GUION : DIGITO_BLANCO;
  valoresDisplay[1] = (digitoDecenas == 0) ? DIGITO_BLANCO : digitoDecenas; // sin cero a la izquierda
  valoresDisplay[2] = digitoUnidades;
  valoresDisplay[3] = digitoDecimal;

  puntoDecimalDisplay[0] = false;
  puntoDecimalDisplay[1] = false;
  puntoDecimalDisplay[2] = true; // XX.X
  puntoDecimalDisplay[3] = false;
}

// Multiplexado no bloqueante: cada REFRESCO_DIGITO_US avanza al siguiente
// dígito. Se apaga todo antes de cambiar segmentos para evitar "fantasmas"
// (ghosting) del dígito anterior.
void actualizarDisplayNoBloqueante() {
  unsigned long ahora = micros();
  if (ahora - ultimoCambioDigitoUs < REFRESCO_DIGITO_US) return;
  ultimoCambioDigitoUs = ahora;

  apagarTodosLosDigitos();

  digitoActivo = (digitoActivo + 1) % 4;
  const bool* patron = obtenerPatronSegmentos(valoresDisplay[digitoActivo]);
  for (int i = 0; i < 7; i++) {
    escribirSegmento(PINES_SEGMENTOS[i], patron[i]);
  }
  escribirSegmento(PIN_SEG_DP, puntoDecimalDisplay[digitoActivo]);

  seleccionarDigito(digitoActivo);
}

// ==================== VELOCIDAD Y SENTIDO DEL MOTOR ====================
// rpm > 0 -> sentido horario (DIR = HIGH), rpm < 0 -> antihorario (DIR = LOW).
// La magnitud (abs(rpm)) define la velocidad; el signo solo define el sentido.
void actualizarVelocidad(float rpm) {
  if (fabs(rpm) < POT_ZONA_MUERTA_RPM) {
    rpmActual = 0;
    delayUs = 0;
    Serial.println("Motor detenido (RPM=0)");
    return;
  }

  bool sentidoHorario = rpm > 0;
  float rpmAbs = fabs(rpm);

  float pasosPorSegundo = rpmAbs * PASOS_POR_VUELTA / 60.0;
  unsigned long nuevoDelay = (unsigned long)(500000.0 / pasosPorSegundo); // medio periodo por flanco

  if (nuevoDelay < DELAY_MIN_US) {
    nuevoDelay = DELAY_MIN_US;
    Serial.println("RPM pedido excede el máximo soportado, se limita al máximo");
  } else if (nuevoDelay > DELAY_MAX_US) {
    nuevoDelay = DELAY_MAX_US;
    Serial.println("RPM pedido muy bajo, se limita al mínimo soportado");
  }

  digitalWrite(PIN_DIR, sentidoHorario ? HIGH : LOW);

  rpmActual = sentidoHorario ? rpmAbs : -rpmAbs; // conserva el signo para el display
  delayUs = nuevoDelay;
  Serial.printf("RPM=%.2f (%s) -> delay=%luus por flanco (periodo por paso=%luus)\n",
                rpmActual, sentidoHorario ? "horario" : "antihorario", delayUs, delayUs * 2);
}

// Genera el pulso de STEP sin bloquear el loop (usa micros() en vez de
// delayMicroseconds), para poder atender el potenciómetro y refrescar el
// display en paralelo sin detener/afectar al motor.
// Nota: a velocidades muy cercanas a DELAY_MIN_US, el tiempo que toma leer el
// potenciómetro y refrescar el display podría hacerse comparable al medio
// periodo del paso, degradando la precisión del RPM real. Para el rango
// típico de uso (decenas de RPM) el margen es amplio.
bool pinStepEnAlto = false;
unsigned long ultimoCambioPasoUs = 0;

void actualizarPasoNoBloqueante() {
  if (delayUs == 0) {
    if (pinStepEnAlto) {
      digitalWrite(PIN_STEP, LOW);
      pinStepEnAlto = false;
    }
    return;
  }

  unsigned long ahora = micros();
  if (ahora - ultimoCambioPasoUs >= delayUs) {
    ultimoCambioPasoUs = ahora;
    pinStepEnAlto = !pinStepEnAlto;
    digitalWrite(PIN_STEP, pinStepEnAlto ? HIGH : LOW);
  }
}

// ==================== POTENCIÓMETRO ====================
int leerPotenciometroPromediado() {
  const int NUM_MUESTRAS = 4;
  long suma = 0;
  for (int i = 0; i < NUM_MUESTRAS; i++) suma += analogRead(PIN_POTENCIOMETRO);
  return suma / NUM_MUESTRAS;
}

// El potenciómetro manda la velocidad por defecto. Si llega un comando por
// Serial, ese valor tiene prioridad y "sincroniza" la referencia del
// potenciómetro a su posición actual, para que no lo pise de inmediato:
// el poti solo vuelve a tomar el control cuando se lo mueve más allá del
// umbral de histéresis desde esa posición.
void leerPotenciometro() {
  int lectura = leerPotenciometroPromediado();
  if (abs(lectura - potUltimaLecturaAplicada) > POT_UMBRAL_CUENTAS) {
    potUltimaLecturaAplicada = lectura;
    float rpmPot = POT_RPM_MIN + (lectura / (float)ADC_MAX) * (POT_RPM_MAX - POT_RPM_MIN);
    actualizarVelocidad(rpmPot);
  }
}

// ==================== COMANDOS POR SERIAL ====================
void leerComandoSerial() {
  static String buffer;

  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (buffer.length() > 0) {
        float rpmPedido = buffer.toFloat();
        buffer = "";
        if (rpmPedido >= POT_RPM_MIN && rpmPedido <= POT_RPM_MAX) {
          actualizarVelocidad(rpmPedido);
          potUltimaLecturaAplicada = leerPotenciometroPromediado(); // resincroniza el poti
        } else {
          Serial.printf("Valor invalido, ingresa un numero entre %.0f y %.0f (0 = detener, negativo = sentido inverso)\n",
                        POT_RPM_MIN, POT_RPM_MAX);
        }
      }
    } else {
      buffer += c;
    }
  }
}

// ==================== SETUP / LOOP ====================
void setup() {
  Serial.begin(115200);

  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  pinMode(PIN_EN, OUTPUT);

  digitalWrite(PIN_EN, LOW); // habilita el driver
  digitalWrite(PIN_DIR, HIGH);

  for (int i = 0; i < 7; i++) pinMode(PINES_SEGMENTOS[i], OUTPUT);
  pinMode(PIN_SEG_DP, OUTPUT);
  for (int i = 0; i < 4; i++) pinMode(PINES_DIGITOS[i], OUTPUT);
  apagarTodosLosDigitos();
  for (int i = 0; i < 7; i++) escribirSegmento(PINES_SEGMENTOS[i], false);

  analogReadResolution(ADC_RESOLUCION_BITS);

  actualizarValoresDisplay();

  Serial.println("Listo. Escribe un valor de RPM y Enter (ej: 30 o -30). 0 = detener.");
  Serial.printf("El potenciometro en A0 controla la velocidad entre %.1f y %.1f RPM (negativo = sentido inverso).\n",
                POT_RPM_MIN, POT_RPM_MAX);
}

// Leer el potenciometro (analogRead x4) toma un tiempo nada despreciable
// frente al medio periodo de paso a velocidades altas (a 60 RPM con
// microstepping 1/16 son ~156us). Si se llamara en cada vuelta del loop,
// ese tiempo se le resta a la precision del pulso de STEP y el motor termina
// girando mas lento de lo pedido. Por eso se throttlea a un intervalo fijo:
// 10ms sigue siendo mucho mas rapido de lo que una mano puede girar la
// perilla, pero libera al loop principal para atender los pasos sin demora.
const unsigned long POT_INTERVALO_MS = 10;
unsigned long ultimaLecturaPotMs = 0;

void loop() {
  leerComandoSerial();

  unsigned long ahoraMs = millis();
  if (ahoraMs - ultimaLecturaPotMs >= POT_INTERVALO_MS) {
    ultimaLecturaPotMs = ahoraMs;
    leerPotenciometro();
  }

  actualizarPasoNoBloqueante();
  actualizarValoresDisplay();
  actualizarDisplayNoBloqueante();
}
