import struct
import tkinter as tk
import paho.mqtt.client as mqtt


# ============================================================
# MQTT CONFIGURATION
# ============================================================

BROKER = "test.mosquitto.org"
PORT = 1883
SEND_TOPIC = "validatecontrolsignals/roboticarm/orange_bird"


# Initial slider values
INITIAL_VALUES = [90.0, 90.0, 90.0, 90.0, 90.0]

# Safety limits
MIN_ANGLE = 0.0
MAX_ANGLE = 180.0


# ============================================================
# APPLICATION STATE
# ============================================================

mqtt_connected = False


# ============================================================
# MQTT CALLBACKS
# ============================================================

def on_connect(client, userdata, flags, rc):
    global mqtt_connected

    if rc == 0:
        mqtt_connected = True
        root.after(0, update_mqtt_status, True, "MQTT: Connected")
        print(f"Connected to {BROKER}:{PORT}")
    else:
        mqtt_connected = False
        root.after(
            0,
            update_mqtt_status,
            False,
            f"MQTT: Connection failed (code {rc})"
        )
        print(f"Connection failed. Return code: {rc}")


def on_disconnect(client, userdata, rc):
    global mqtt_connected

    mqtt_connected = False

    root.after(
        0,
        update_mqtt_status,
        False,
        "MQTT: Disconnected (Reconnecting...)"
    )

    if rc == 0:
        print("Disconnected normally.")
    else:
        print(
            f"Disconnected unexpectedly. rc={rc}. "
            "Attempting to reconnect..."
        )


def on_publish(client, userdata, mid):
    # Optional: uncomment if you want to trace every
    # published message ID in the console.
    #
    # print(f"Published. Message ID: {mid}")

    pass


# ============================================================
# CREATE MQTT CLIENT & START BACKGROUND LOOP
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
        value = max(
            MIN_ANGLE,
            min(MAX_ANGLE, value)
        )

        values.append(value)

    return values


# ============================================================
# PUBLISH FIVE ANGLES
# ============================================================

def publish_angles():
    """
    Publish all five current slider values once.
    This function is called when SEND ANGLES is clicked.
    """

    if not mqtt_connected:
        print("Cannot send angles: MQTT is not connected.")
        return

    values = get_values()

    # Five little-endian float32 values
    payload = struct.pack(
        "<5f",
        *values
    )

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
# MQTT STATUS DISPLAY
# ============================================================

def update_mqtt_status(connected, text):

    if connected:

        status_label.config(
            text=text,
            foreground="#55ff55"
        )

    else:

        if (
            "Reconnecting" in text
            or "Connecting" in text
        ):
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
# SLIDER CHANGED
# ============================================================

def slider_changed(value):

    for i, slider in enumerate(sliders):

        current_value = float(
            slider.get()
        )

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
        label.config(
            text="90.0°"
        )

    print("All angles reset to 90°.")


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
    text="Five 0–180° controls • Click SEND ANGLES to publish",
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
    # ANGLE NAME
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
    # CURRENT VALUE
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
    # SLIDER
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
    # RANGE
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


# ============================================================
# RESET BUTTON
# ============================================================

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
# SEND BUTTON
# ============================================================

send_button = tk.Button(
    button_frame,
    text="SEND ANGLES",
    command=publish_angles,
    font=("Arial", 11, "bold"),
    bg="#2d7dfa",
    fg="white",
    activebackground="#1f66d1",
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
    pady=(5, 5)
)


# ============================================================
# INFO
# ============================================================

info_label = tk.Label(
    root,
    text=(
        "Range: 0–180°   |   "
        "Manual sending   |   "
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
# STARTUP MQTT CONNECTION
# ============================================================

try:

    client.loop_start()

    client.connect(
        BROKER,
        PORT,
        60
    )

except Exception as e:

    print(
        f"Initial connection error: {e}"
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
print("Send mode    : Manual")
print("Initial vals : 90, 90, 90, 90, 90")
print("=" * 60)


root.mainloop()