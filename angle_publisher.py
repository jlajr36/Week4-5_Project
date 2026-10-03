import struct
import tkinter as tk
import paho.mqtt.client as mqtt


# ============================================================
# MQTT CONFIGURATION
# ============================================================

BROKER = "test.mosquitto.org"
PORT = 1883
SEND_TOPIC = "validatecontrolsignals/roboticarm/orange_bird"

# Publish interval: 1 second
SEND_INTERVAL_MS = 1000

# Initial slider values
INITIAL_VALUES = [90.0, 90.0, 90.0, 90.0, 90.0]

# Safety limits
MIN_ANGLE = 0.0
MAX_ANGLE = 180.0


# ============================================================
# APPLICATION STATE
# ============================================================

mqtt_connected = False
mqtt_connecting = False


# ============================================================
# MQTT CALLBACKS
# ============================================================

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    global mqtt_connecting

    mqtt_connecting = False

    if rc == 0:
        mqtt_connected = True

        root.after(
            0,
            update_mqtt_status,
            True,
            "MQTT: Connected"
        )

        root.after(
            0,
            update_connect_button
        )

        print(f"Connected to {BROKER}:{PORT}")

    else:
        mqtt_connected = False

        root.after(
            0,
            update_mqtt_status,
            False,
            f"MQTT: Connection failed (code {rc})"
        )

        root.after(
            0,
            update_connect_button
        )

        print(f"Connection failed. Return code: {rc}")


def on_disconnect(client, userdata, rc):
    global mqtt_connected
    global mqtt_connecting

    mqtt_connected = False
    mqtt_connecting = False

    root.after(
        0,
        update_mqtt_status,
        False,
        "MQTT: Disconnected"
    )

    root.after(
        0,
        update_connect_button
    )

    if rc == 0:
        print("Disconnected normally.")
    else:
        print(f"Disconnected. rc={rc}")


def on_publish(client, userdata, mid):
    print(f"Published. Message ID: {mid}")


# ============================================================
# CREATE MQTT CLIENT
# ============================================================

client = mqtt.Client()

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish


# ============================================================
# GET CURRENT SLIDER VALUES
# ============================================================

def get_values():
    """
    Read all five sliders and enforce the 0–180 degree limits.
    """

    values = []

    for slider in sliders:
        value = float(slider.get())

        # Safety clamp
        value = max(MIN_ANGLE, min(MAX_ANGLE, value))

        values.append(value)

    return values


# ============================================================
# PUBLISH FIVE ANGLES
# ============================================================

def publish_angles():
    """
    Publish all five current slider values.

    Format:
        5 × little-endian float32
        20 bytes total

    This exactly matches the original HTML:
        setFloat32(..., true)

    and the original Python:
        struct.pack("<5f", ...)
    """

    if not mqtt_connected:
        return

    values = get_values()

    # --------------------------------------------------------
    # Convert five floats into 20-byte payload
    # --------------------------------------------------------

    payload = struct.pack("<5f", *values)

    # --------------------------------------------------------
    # Publish
    # --------------------------------------------------------

    try:
        result = client.publish(
            SEND_TOPIC,
            payload,
            qos=0
        )

        if result.rc == mqtt.MQTT_ERR_SUCCESS:

            print("\n" + "=" * 50)
            print("PUBLISHED")
            print("=" * 50)

            for i, value in enumerate(values, 1):
                print(f"Angle {i}: {value:.1f}°")

            print(f"Raw bytes: {payload!r}")
            print(f"Bytes: {len(payload)}")

        else:

            print(
                f"Publish error. Return code: {result.rc}"
            )

    except Exception as e:

        print(f"ERROR publishing: {e}")


# ============================================================
# PERIODIC PUBLISH LOOP
# ============================================================

def periodic_publish():
    """
    Publish once every second while MQTT is connected.

    The loop continues regardless of connection state so that
    connecting/disconnecting does not require restarting it.
    """

    if mqtt_connected:
        publish_angles()

    root.after(
        SEND_INTERVAL_MS,
        periodic_publish
    )


# ============================================================
# CONNECT
# ============================================================

def connect_mqtt():
    global mqtt_connected
    global mqtt_connecting

    if mqtt_connected or mqtt_connecting:
        return

    mqtt_connecting = True

    update_mqtt_status(
        False,
        "MQTT: Connecting..."
    )

    update_connect_button()

    print(f"Connecting to {BROKER}:{PORT}...")

    try:
        # Start MQTT networking
        client.loop_start()

        client.connect(
            BROKER,
            PORT,
            60
        )

    except Exception as e:
        mqtt_connecting = False
        mqtt_connected = False

        update_mqtt_status(
            False,
            f"MQTT: Connection failed — {e}"
        )

        update_connect_button()

        print(f"ERROR connecting to MQTT: {e}")

# ============================================================
# DISCONNECT
# ============================================================

def disconnect_mqtt():
    global mqtt_connected
    global mqtt_connecting

    if not mqtt_connected and not mqtt_connecting:
        return

    print("Disconnecting MQTT...")

    mqtt_connecting = False
    mqtt_connected = False

    try:
        client.disconnect()
    except Exception:
        pass

    try:
        client.loop_stop()
    except Exception:
        pass

    update_mqtt_status(
        False,
        "MQTT: Disconnected"
    )

    update_connect_button()


# ============================================================
# CONNECT / DISCONNECT BUTTON
# ============================================================

def toggle_connection():

    if mqtt_connected or mqtt_connecting:
        disconnect_mqtt()
    else:
        connect_mqtt()


# ============================================================
# MQTT STATUS DISPLAY
# ============================================================

def update_mqtt_status(connected, text):

    if connected:

        status_label.config(
            text=text,
            foreground="#55ff55"
        )

    else:

        if "Connecting" in text:

            status_label.config(
                text=text,
                foreground="#ffcc44"
            )

        else:

            status_label.config(
                text=text,
                foreground="#ff5555"
            )


# ============================================================
# BUTTON TEXT
# ============================================================

def update_connect_button():

    if mqtt_connected:

        connect_button.config(
            text="DISCONNECT",
            bg="#d9463f",
            activebackground="#b8362f"
        )

    elif mqtt_connecting:

        connect_button.config(
            text="CONNECTING...",
            bg="#777777",
            activebackground="#777777"
        )

    else:

        connect_button.config(
            text="CONNECT",
            bg="#2a9d5c",
            activebackground="#22824c"
        )


# ============================================================
# SLIDER CHANGED
# ============================================================

def slider_changed(value):
    """
    Slider changes do NOT publish.

    They only update the displayed angle.

    The periodic timer publishes the values once per second.
    """

    for i, slider in enumerate(sliders):

        current_value = float(slider.get())

        value_labels[i].config(
            text=f"{current_value:.1f}°"
        )


# ============================================================
# RESET TO 90 DEGREES
# ============================================================

def reset_sliders():

    for slider in sliders:
        slider.set(90.0)

    for label in value_labels:
        label.config(text="90.0°")

    print("All angles reset to 90°.")


# ============================================================
# SEND NOW
# ============================================================

def send_now():

    if not mqtt_connected:

        update_mqtt_status(
            False,
            "MQTT: Disconnected — nothing sent"
        )

        return

    publish_angles()


# ============================================================
# GUI
# ============================================================

root = tk.Tk()

root.title(
    "5-Axis MQTT Angle Controller"
)

root.geometry(
    "900x750"
)

root.minsize(
    700,
    700
)

root.configure(
    bg="#111111"
)


# ============================================================
# TITLE
# ============================================================

title_label = tk.Label(
    root,
    text="5-Axis MQTT Angle Controller",
    font=("Arial", 22, "bold"),
    bg="#111111",
    fg="#eeeeee"
)

title_label.pack(
    pady=(20, 5)
)


subtitle_label = tk.Label(
    root,
    text="Five 0–180° controls • Publishing at 1 Hz",
    font=("Arial", 11),
    bg="#111111",
    fg="#aaaaaa"
)

subtitle_label.pack(
    pady=(0, 15)
)


# ============================================================
# MQTT TOPIC
# ============================================================

topic_label = tk.Label(
    root,
    text=f"Topic: {SEND_TOPIC}",
    font=("Courier New", 10),
    bg="#111111",
    fg="#6f9f6f"
)

topic_label.pack(
    pady=(0, 10)
)


# ============================================================
# SLIDER AREA
# ============================================================

slider_frame = tk.Frame(
    root,
    bg="#111111"
)

slider_frame.pack(
    fill="both",
    expand=True,
    padx=30,
    pady=10
)


sliders = []
value_labels = []


for i in range(5):

    # --------------------------------------------------------
    # Column
    # --------------------------------------------------------

    column = tk.Frame(
        slider_frame,
        bg="#1a1a1a",
        width=130,
        height=400
    )

    column.pack(
        side="left",
        fill="both",
        expand=True,
        padx=8,
        pady=5
    )

    column.pack_propagate(False)


    # --------------------------------------------------------
    # Angle title
    # --------------------------------------------------------

    name_label = tk.Label(
        column,
        text=f"ANGLE {i + 1}",
        font=("Arial", 12, "bold"),
        bg="#1a1a1a",
        fg="#eeeeee"
    )

    name_label.pack(
        pady=(15, 5)
    )


    # --------------------------------------------------------
    # Current angle
    # --------------------------------------------------------

    value_label = tk.Label(
        column,
        text=f"{INITIAL_VALUES[i]:.1f}°",
        font=("Arial", 16, "bold"),
        bg="#1a1a1a",
        fg="#55ff55"
    )

    value_label.pack(
        pady=(0, 5)
    )

    value_labels.append(
        value_label
    )


    # --------------------------------------------------------
    # Vertical slider
    # --------------------------------------------------------

    slider = tk.Scale(
        column,

        from_=MAX_ANGLE,
        to=MIN_ANGLE,

        resolution=0.1,

        orient=tk.VERTICAL,

        length=280,
        width=30,
        sliderlength=35,

        showvalue=False,

        command=slider_changed,

        bg="#1a1a1a",
        fg="#eeeeee",
        troughcolor="#333333",

        activebackground="#2d7dfa",

        highlightthickness=0,
        bd=0
    )

    slider.set(
        INITIAL_VALUES[i]
    )

    slider.pack(
        fill="both",
        expand=True,
        padx=10
    )

    sliders.append(
        slider
    )


    # --------------------------------------------------------
    # Range
    # --------------------------------------------------------

    range_label = tk.Label(
        column,
        text="0° ← 180°",
        font=("Arial", 9),
        bg="#1a1a1a",
        fg="#888888"
    )

    range_label.pack(
        pady=(5, 10)
    )


# ============================================================
# BUTTONS
# ============================================================

button_frame = tk.Frame(
    root,
    bg="#111111"
)

button_frame.pack(
    pady=10
)


# ------------------------------------------------------------
# Connect / Disconnect
# ------------------------------------------------------------

connect_button = tk.Button(
    button_frame,

    text="CONNECT",

    command=toggle_connection,

    font=("Arial", 11, "bold"),

    bg="#2a9d5c",
    fg="white",

    activebackground="#22824c",
    activeforeground="white",

    padx=25,
    pady=10,

    relief="flat",
    cursor="hand2"
)

connect_button.pack(
    side="left",
    padx=6
)


# ------------------------------------------------------------
# Send Now
# ------------------------------------------------------------

send_button = tk.Button(
    button_frame,

    text="SEND NOW",

    command=send_now,

    font=("Arial", 11, "bold"),

    bg="#2d7dfa",
    fg="white",

    activebackground="#1f66d6",
    activeforeground="white",

    padx=25,
    pady=10,

    relief="flat",
    cursor="hand2"
)

send_button.pack(
    side="left",
    padx=6
)


# ------------------------------------------------------------
# Reset
# ------------------------------------------------------------

reset_button = tk.Button(
    button_frame,

    text="RESET TO 90°",

    command=reset_sliders,

    font=("Arial", 11, "bold"),

    bg="#444444",
    fg="white",

    activebackground="#555555",
    activeforeground="white",

    padx=25,
    pady=10,

    relief="flat",
    cursor="hand2"
)

reset_button.pack(
    side="left",
    padx=6
)


# ============================================================
# STATUS
# ============================================================

status_label = tk.Label(
    root,

    text="MQTT: Disconnected",

    font=("Arial", 11, "bold"),

    bg="#111111",
    fg="#ff5555"
)

status_label.pack(
    pady=(5, 5)
)


# ============================================================
# INFO
# ============================================================

info_label = tk.Label(
    root,

    text=(
        "Range: 0–180°   |   "
        "Update rate: 1 Hz   |   "
        "Payload: 5 × little-endian float32   |   "
        "20 bytes"
    ),

    font=("Courier New", 9),

    bg="#111111",
    fg="#777777"
)

info_label.pack(
    pady=(0, 15)
)


# ============================================================
# START PERIODIC PUBLISH TIMER
# ============================================================

root.after(
    SEND_INTERVAL_MS,
    periodic_publish
)


# ============================================================
# CLOSE APPLICATION
# ============================================================

def close_application():

    print("Closing application...")

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
# START GUI
# ============================================================

print("=" * 60)
print("5-AXIS MQTT ANGLE CONTROLLER")
print("=" * 60)
print(f"Broker       : {BROKER}:{PORT}")
print(f"Topic        : {SEND_TOPIC}")
print("Update rate  : 1 Hz")
print("Initial vals : 90, 90, 90, 90, 90")
print("=" * 60)

root.mainloop()