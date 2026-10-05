import struct
import math
import tkinter as tk
import paho.mqtt.client as mqtt


# ============================================================
# MQTT CONFIGURATION
# ============================================================

BROKER = "broker.emqx.io"
PORT = 1883

SUBSCRIBE_TOPIC = "transmitcontrolsignals/roboticarm/orange_bird"


# ============================================================
# GUI CONFIGURATION
# ============================================================

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 650

GAUGE_SIZE = 200


# ============================================================
# APPLICATION STATE
# ============================================================

mqtt_connected = False

last_values = [
    90.0,
    90.0,
    90.0,
    90.0,
    90.0
]


# ============================================================
# MQTT CALLBACKS
# ============================================================

def on_connect(client, userdata, flags, rc):

    global mqtt_connected

    if rc == 0:

        mqtt_connected = True

        print("=" * 60)
        print("MQTT CONNECTED")
        print("=" * 60)

        print(f"Broker : {BROKER}:{PORT}")
        print(f"Topic  : {SUBSCRIBE_TOPIC}")

        client.subscribe(
            SUBSCRIBE_TOPIC,
            qos=0
        )

        root.after(
            0,
            update_status,
            "MQTT: Connected — Waiting for data",
            "#55ff55"
        )

    else:

        mqtt_connected = False

        print(
            f"MQTT connection failed. Return code: {rc}"
        )

        root.after(
            0,
            update_status,
            f"MQTT: Connection failed ({rc})",
            "#ff5555"
        )


def on_disconnect(client, userdata, rc):

    global mqtt_connected

    mqtt_connected = False

    print(
        f"MQTT disconnected. rc={rc}"
    )

    root.after(
        0,
        update_status,
        "MQTT: Disconnected",
        "#ff5555"
    )


def on_message(client, userdata, msg):

    global last_values

    print("\n" + "=" * 60)
    print("MESSAGE RECEIVED")
    print("=" * 60)

    print(f"Topic: {msg.topic}")
    print(f"Payload size: {len(msg.payload)} bytes")
    print(f"Raw bytes: {msg.payload!r}")

    # --------------------------------------------------------
    # EXPECTED PAYLOAD
    #
    # 5 × float32
    # 5 × 4 bytes
    # = 20 bytes
    # --------------------------------------------------------

    if len(msg.payload) != 20:

        print(
            f"ERROR: Expected 20 bytes, "
            f"received {len(msg.payload)}"
        )

        root.after(
            0,
            update_status,
            f"ERROR: Expected 20 bytes, got {len(msg.payload)}",
            "#ff5555"
        )

        return

    try:

        # ----------------------------------------------------
        # Decode the five little-endian float32 values
        # ----------------------------------------------------

        values = struct.unpack(
            "<5f",
            msg.payload
        )

        last_values = list(values)

        print("Decoded angles:")

        for i, value in enumerate(values, 1):

            print(
                f"Angle {i}: {value:.1f}°"
            )

        # ----------------------------------------------------
        # Update GUI on Tkinter's main thread
        # ----------------------------------------------------

        root.after(
            0,
            update_angles,
            values
        )

    except struct.error as e:

        print(
            f"ERROR decoding payload: {e}"
        )

        root.after(
            0,
            update_status,
            "ERROR: Invalid payload",
            "#ff5555"
        )


# ============================================================
# STATUS
# ============================================================

def update_status(text, color):

    status_label.config(
        text=text,
        fg=color
    )


# ============================================================
# UPDATE ALL GAUGES
# ============================================================

def update_angles(values):

    for i, value in enumerate(values):

        # Safety clamp for display
        value = max(
            0.0,
            min(180.0, value)
        )

        angle_labels[i].config(
            text=f"{value:.1f}°"
        )

        draw_gauge(
            gauge_canvases[i],
            value
        )

    update_status(
        "MQTT: Receiving angle data",
        "#55ff55"
    )


# ============================================================
# DRAW GAUGE
# ============================================================

def draw_gauge(canvas, angle):

    canvas.delete("all")

    width = GAUGE_SIZE
    height = GAUGE_SIZE

    center_x = width / 2
    center_y = height / 2

    radius = 78

    # ========================================================
    # BACKGROUND CIRCLE
    # ========================================================

    canvas.create_oval(
        center_x - radius,
        center_y - radius,
        center_x + radius,
        center_y + radius,

        outline="#333333",
        width=14
    )


    # ========================================================
    # COLORED ANGLE ARC
    # ========================================================

    # 0° to 180°
    #
    # Start at 180° on the canvas and sweep clockwise.
    # This creates a nice left-to-right servo-style gauge.

    extent = angle

    # Determine color based on angle

    if angle < 60:

        arc_color = "#55ff55"

    elif angle < 120:

        arc_color = "#ffcc44"

    else:

        arc_color = "#ff5555"


    canvas.create_arc(
        center_x - radius,
        center_y - radius,
        center_x + radius,
        center_y + radius,

        start=180,
        extent=extent,

        style=tk.ARC,

        outline=arc_color,
        width=14
    )


    # ========================================================
    # TICK MARKS
    # ========================================================

    for tick_angle in range(0, 181, 30):

        theta = math.radians(180 - tick_angle)

        outer_radius = 91
        inner_radius = 82

        x1 = (
            center_x +
            inner_radius * math.cos(theta)
        )

        y1 = (
            center_y -
            inner_radius * math.sin(theta)
        )

        x2 = (
            center_x +
            outer_radius * math.cos(theta)
        )

        y2 = (
            center_y -
            outer_radius * math.sin(theta)
        )

        canvas.create_line(
            x1,
            y1,
            x2,
            y2,

            fill="#666666",
            width=2
        )


    # ========================================================
    # 0° LABEL
    # ========================================================

    canvas.create_text(
        18,
        center_y + 18,

        text="0°",

        fill="#777777",

        font=("Arial", 9, "bold")
    )


    # ========================================================
    # 90° LABEL
    # ========================================================

    canvas.create_text(
        center_x,
        center_y - 92,

        text="90°",

        fill="#777777",

        font=("Arial", 9, "bold")
    )


    # ========================================================
    # 180° LABEL
    # ========================================================

    canvas.create_text(
        width - 18,
        center_y + 18,

        text="180°",

        fill="#777777",

        font=("Arial", 9, "bold")
    )


    # ========================================================
    # POINTER
    # ========================================================

    theta = math.radians(
        180 - angle
    )

    pointer_length = 62

    end_x = (
        center_x +
        pointer_length * math.cos(theta)
    )

    end_y = (
        center_y -
        pointer_length * math.sin(theta)
    )


    canvas.create_line(
        center_x,
        center_y,
        end_x,
        end_y,

        fill="#eeeeee",
        width=5
    )


    # ========================================================
    # CENTER DOT
    # ========================================================

    canvas.create_oval(
        center_x - 8,
        center_y - 8,
        center_x + 8,
        center_y + 8,

        fill="#eeeeee",
        outline=""
    )


    # ========================================================
    # LARGE ANGLE VALUE
    # ========================================================

    canvas.create_text(
        center_x,
        center_y + 40,

        text=f"{angle:.1f}°",

        fill="#ffffff",

        font=("Arial", 17, "bold")
    )


# ============================================================
# CREATE MQTT CLIENT
# ============================================================

client = mqtt.Client()

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title(
    "5-Axis MQTT Subscriber"
)

root.geometry(
    f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
)

root.minsize(
    1100,
    600
)

root.configure(
    bg="#111111"
)


# ============================================================
# TITLE
# ============================================================

title_label = tk.Label(
    root,

    text="5-AXIS MQTT ANGLE MONITOR",

    font=("Arial", 24, "bold"),

    bg="#111111",
    fg="#eeeeee"
)

title_label.pack(
    pady=(20, 2)
)


subtitle_label = tk.Label(
    root,

    text="Live robotic arm joint positions",

    font=("Arial", 11),

    bg="#111111",
    fg="#888888"
)

subtitle_label.pack(
    pady=(0, 5)
)


# ============================================================
# TOPIC
# ============================================================

topic_label = tk.Label(
    root,

    text=f"MQTT TOPIC: {SUBSCRIBE_TOPIC}",

    font=("Courier New", 9),

    bg="#111111",
    fg="#6f9f6f"
)

topic_label.pack(
    pady=(0, 12)
)


# ============================================================
# GAUGE AREA
# ============================================================

gauge_frame = tk.Frame(
    root,
    bg="#111111"
)

gauge_frame.pack(
    fill="both",
    expand=True,

    padx=20,
    pady=5
)


gauge_canvases = []

angle_labels = []


# ============================================================
# CREATE FIVE GAUGES
# ============================================================

for i in range(5):

    column = tk.Frame(
        gauge_frame,

        bg="#1a1a1a",

        width=210,
        height=320
    )

    column.pack(
        side="left",

        fill="both",
        expand=True,

        padx=6,
        pady=5
    )

    column.pack_propagate(False)


    # --------------------------------------------------------
    # AXIS NAME
    # --------------------------------------------------------

    name_label = tk.Label(
        column,

        text=f"AXIS {i + 1}",

        font=("Arial", 12, "bold"),

        bg="#1a1a1a",
        fg="#eeeeee"
    )

    name_label.pack(
        pady=(12, 0)
    )


    # --------------------------------------------------------
    # GAUGE
    # --------------------------------------------------------

    canvas = tk.Canvas(
        column,

        width=GAUGE_SIZE,
        height=GAUGE_SIZE,

        bg="#1a1a1a",

        highlightthickness=0
    )

    canvas.pack(
        pady=(5, 0)
    )

    gauge_canvases.append(
        canvas
    )


    # --------------------------------------------------------
    # ANGLE VALUE
    # --------------------------------------------------------

    angle_label = tk.Label(
        column,

        text="90.0°",

        font=("Arial", 15, "bold"),

        bg="#1a1a1a",
        fg="#55ff55"
    )

    angle_label.pack(
        pady=(0, 8)
    )

    angle_labels.append(
        angle_label
    )


# ============================================================
# STATUS
# ============================================================

status_label = tk.Label(
    root,

    text="MQTT: Connecting...",

    font=("Arial", 11, "bold"),

    bg="#111111",
    fg="#ffcc44"
)

status_label.pack(
    pady=(4, 3)
)


# ============================================================
# INFO
# ============================================================

info_label = tk.Label(
    root,

    text=(
        "0–180°  |  5 × float32  |  "
        "20-byte payload  |  Live MQTT subscriber"
    ),

    font=("Courier New", 9),

    bg="#111111",
    fg="#666666"
)

info_label.pack(
    pady=(0, 12)
)


# ============================================================
# INITIAL GAUGES
# ============================================================

for i in range(5):

    draw_gauge(
        gauge_canvases[i],
        90.0
    )


# ============================================================
# CONNECT TO MQTT
# ============================================================

def connect_mqtt():

    print("=" * 60)
    print("5-AXIS MQTT ANGLE MONITOR")
    print("=" * 60)

    print(f"Broker : {BROKER}:{PORT}")
    print(f"Topic  : {SUBSCRIBE_TOPIC}")

    print("=" * 60)

    try:

        client.connect(
            BROKER,
            PORT,
            60
        )

        client.loop_start()

    except Exception as e:

        print(
            f"ERROR connecting to MQTT: {e}"
        )

        update_status(
            "MQTT: Connection failed",
            "#ff5555"
        )


# ============================================================
# CLOSE APPLICATION
# ============================================================

def close_application():

    print("Closing subscriber...")

    try:
        client.disconnect()
    except Exception:
        pass

    try:
        client.loop_stop()
    except Exception:
        pass

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    close_application
)


# ============================================================
# START
# ============================================================

root.after(
    100,
    connect_mqtt
)


root.mainloop()