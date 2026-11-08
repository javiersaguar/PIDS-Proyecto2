# Kit del rival 2 en movimiento

En la rotonda (tramo R1), nuestro robot retrocede 1,25 m a 0,1 m/s disparando hacia su
izquierda. El **rival 2** es un segundo RoboMaster que avanza en paralelo, 1,2 m a su
izquierda: 0,75 m a 0,05 m/s, unos 15 s.

Lo maneja Alejandro desde su portátil con `rival_movil.py`. El rival espera quieto y arranca
de una de estas dos formas:
- con el aviso que manda nuestra demo al empezar ese tramo;
- con Enter, si el aviso no llega.

El circuito completo está en [`../circuito_paso_a_paso.md`](../circuito_paso_a_paso.md).

| Fichero | Para qué sirve |
|---|---|
| `rival_movil.py` | Conecta el robot rival, espera el aviso o Enter y lo mueve |
| `conectar_rival.py` | Une el robot rival a la wifi del laboratorio con un QR (modo networking) |
| `config_rival.ejemplo.json` | Plantilla de la configuración: se copia como `config_rival.json` |
| `aviso.py` | El aviso por la red (UDP); lo usan también `demo.py` y `rival_movil.py` |

## 1. Qué hace falta

- Un segundo RoboMaster EP con la batería cargada (más del 50 %). No es el nuestro.
- Su **número de serie**. Está en la pegatina del robot, en la app RoboMaster o en la caja.
- Un portátil con el repositorio (rama `javier-saguar` o `main` cuando se fusione) y
  **Python 3.8**. El SDK de RoboMaster no funciona con versiones más nuevas. No hacen falta
  torch ni el modelo.

Entorno, desde `ENTREGA 2/WEEK3`:

```
uv venv --python 3.8 .venv
uv pip install --python .venv\Scripts\python.exe "robomaster>=0.1.1.68,<0.2"
```

En Linux o macOS, `.venv/bin/python` en lugar de `.venv\Scripts\python.exe`. Si ya está el
entorno de la demo (`.venv` con torch), sirve el mismo.

## 2. Configuración (una vez)

En `ENTREGA 2/WEEK3/rival/`, copiar `config_rival.ejemplo.json` como `config_rival.json` y
rellenarlo:

```json
{
  "conexion": "networking",
  "serial": "número de serie del robot RIVAL",
  "ssid": "wifi del laboratorio",
  "password": "contraseña de esa wifi",
  "puerto": 50555
}
```

- **`config_rival.json` no se sube nunca a GitHub.** Está en `.gitignore` porque lleva la
  contraseña de la wifi y el número de serie, igual que `connect.py`.
- El número de serie tiene que ser el del robot rival. Con él, el script nunca se conecta
  por error a nuestro robot, que está en la misma red. Por eso tampoco se usa
  `serial_number.txt`, que es el de nuestro robot.

## 3. Conectar el robot rival

### Opción A: networking (recomendada)

Así el rival arranca solo con el aviso de la demo. Los dos robots y los dos portátiles
están en la wifi del laboratorio.

1. En el robot rival, deslizar la pestaña de conexión hasta el icono del router y pulsar el
   botón rojo de al lado. El robot se queda esperando un QR.
2. Ejecutar `python rival/conectar_rival.py`. Se abre un QR (`rival/qrcode.png`, que tampoco
   se sube).
3. Coger el robot por la base y apuntar su cámara al QR hasta que avise de que se ha
   conectado.
4. Mirar la IP del portátil de Alejandro en la wifi del laboratorio y pasársela a Javier:
   - Windows: `ipconfig`, en «Dirección IPv4» del adaptador wifi;
   - Linux: `hostname -I`;
   - macOS: `ipconfig getifaddr en0`.

### Opción B: wifi directo

El portátil se conecta a la wifi `RMEP-...` del robot rival; la contraseña está en su
pegatina.

- Pestaña de conexión en el icono de wifi directo.
- En `config_rival.json`, `"conexion": "wifi"`, o lanzar con `--conexion wifi`.
- **Inconveniente:** el portátil sale de la red del laboratorio y el aviso de la demo no le
  llega. Se usa `--modo enter` y se arranca a mano (apartado 6).

## 4. Probar el aviso sin robots

Hay que hacerlo antes del día de la demo, en la red del laboratorio.

1. Portátil de Alejandro:
   ```
   python rival/rival_movil.py --sin-robot
   ```
2. Portátil de Javier, con la IP del paso 3.4:
   ```
   python rival/rival_movil.py --enviar <IP de Alejandro>
   ```
3. En el de Alejandro debe salir `Salida por aviso de <IP de Javier>`.

Si no llega:
- **Cortafuegos.** En Windows, la primera vez que se ejecuta pregunta si Python puede
  recibir conexiones. Hay que permitirlo en el tipo de red que sea la del laboratorio (si
  es «pública», también ahí). Si no se quiere tocar, se usa el arranque a mano.
- **Red.** Comprobar que los dos portátiles están en la misma wifi y que la IP es la de ese
  adaptador. Algunas redes aíslan a los clientes entre sí; entonces el aviso no llega nunca
  y se usa el arranque a mano.
- **Puerto.** Por defecto es el 50555. Si está ocupado, se cambia en los dos lados: `--puerto`
  en `rival_movil.py` e `IP:PUERTO` en `--aviso-rival` de la demo.

## 5. Colocar el rival

- **Posición:** (4,6; −2,2) en el plano del circuito. Es 1,2 m a la izquierda del tramo en
  el que retrocede nuestro robot (y = −1), cerca del punto donde empieza a retroceder
  (x = 4,75).
- **Orientación:** mirando hacia la salida (hacia −x), es decir, en el mismo sentido en el
  que retrocede nuestro robot. Avanza hacia delante.
- **Espacio:** dejar libres al menos 0,75 m por delante, hasta (3,85; −2,2), y medio metro a
  los lados.
- **Torreta:** centrada. El script no la mueve.

## 6. El día de la demo

1. Robot rival encendido, conectado y en su posición.
2. Alejandro lanza:
   ```
   python rival/rival_movil.py
   ```
   El robot se conecta, muestra su batería y espera: `Listo. Esperando el aviso de la demo...`.
3. Javier lanza la demo:
   ```
   python demo.py --aviso-rival <IP de Alejandro>
   ```
4. Al empezar el retroceso de la rotonda, la demo manda el aviso y el rival arranca solo.
   Alejandro sigue al robot de cerca con Ctrl+C a mano.
5. **Si el aviso no llega**, la consola de la demo muestra `ARRANCAR RIVAL 2 AHORA` y Alejandro
   pulsa **Enter**. El momento es cuando nuestro robot, ya 1 m a la izquierda, empieza a
   retroceder y su torreta gira hacia el rival con la luz ámbar.
6. El rival avanza 0,75 m en unos 15 s, se para solo y el script termina.

## 7. Opciones

| Opción | Por defecto | Qué hace |
|---|---|---|
| `--distancia M` | 0,75 | Metros que avanza; negativo, hacia atrás |
| `--velocidad V` | 0,05 | m/s; nunca más de 0,1 |
| `--retraso S` | 0 | Segundos de espera tras el aviso antes de arrancar |
| `--modo aviso` | sí | Arranca con el aviso de la demo o con Enter |
| `--modo enter` | | Solo con Enter |
| `--modo ya` | | Cuenta atrás de 3 s y arranca, para probar el movimiento |
| `--conexion wifi` | networking | Wifi directo en lugar de la red del laboratorio |
| `--sin-robot` | | Solo espera el aviso, sin conectar el robot |
| `--enviar IP` | | Manda un aviso de prueba a ese portátil y sale |

Si se cambian la velocidad o la distancia, hay que cambiarlas también en `RIVALES` de
`circuito.py` (`VELOCIDAD_RIVAL_MOVIL`, `punto` y `hasta`). Nuestro robot usa esos datos
para prever cómo se mueve el rival en la imagen.

## 8. Seguridad

- **Velocidad:** el script no pasa de 0,1 m/s.
- **Paradas:** el robot se para solo si el script deja de mandar órdenes durante 0,5 s, y
  Ctrl+C lo para en cualquier momento.
- **Tiempo máximo:** si no llega al destino en el doble del tiempo previsto más 5 s, se para.
- **Acompañamiento:** coger el robot siempre por la base, nunca por la cabeza, y que alguien
  lo siga de cerca.

## 9. Problemas frecuentes

| Problema | Solución |
|---|---|
| `Falta el número de serie del robot rival` | Rellenar `serial` en `config_rival.json` |
| No conecta en networking | Repetir `conectar_rival.py`: pestaña en el router y botón rojo antes del QR |
| No conecta en wifi directo | El portátil tiene que estar en la wifi `RMEP-...` del rival |
| `Address already in use` al esperar el aviso | Otro programa usa el puerto: `--puerto 50556` y `--aviso-rival IP:50556` |
| El rival se mueve hacia el lado contrario | Está mal orientado: girarlo, o usar `--distancia -0.75` |
| `sin odometría` | Avanza por tiempo (distancia / velocidad); la distancia puede variar unos centímetros |
