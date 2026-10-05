import struct
import math
import tkinter as tk
import paho.mqtt.client as mqtt


# ============================================================
# MQTT CONFIGURATION
# ============================================================

BROKER = "broker.emqx.io"
PORT = 1883

VALIDATE_TOPIC = "validatecontrolsignals/roboticarm/orange_bird"
TRANSMIT_TOPIC = "transmitcontrolsignals/roboticarm/orange_bird"


# ============================================================
# SAFETY LIMITS
# ============================================================

MIN_ANGLE = 0.0
MAX_ANGLE = 180.0

EXPECTED_PAYLOAD_SIZE = 20


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

        print("=" * 60)
        print("MQTT VALIDATION MIDDLEWARE CONNECTED")
        print("=" * 60)

        print(f"Broker   : {BROKER}:{PORT}")
        print(f"Input    : {VALIDATE_TOPIC}")
        print(f"Output   : {TRANSMIT_TOPIC}")
        print("=" * 60)

        client.subscribe(
            VALIDATE_TOPIC,
            qos=0
        )

        root.after(
            0,
            update_status,
            "MQTT: Connected — Validation active",
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


# ============================================================
# MESSAGE VALIDATION
# ============================================================

def validate_angles(payload):

    """
    Validate one MQTT payload.

    Returns:
        (True, values)  if valid
        (False, None)   if invalid

    IMPORTANT:
    No corrected/clamped values are produced.
    An invalid value causes the entire packet to be rejected.
    """

    # --------------------------------------------------------
    # Check payload size
    # --------------------------------------------------------

    if len(payload) != EXPECTED_PAYLOAD_SIZE:

        print(
            f"REJECTED: Expected "
            f"{EXPECTED_PAYLOAD_SIZE} bytes, "
            f"received {len(payload)} bytes"
        )

        return False, None


    # --------------------------------------------------------
    # Decode five little-endian float32 values
    # --------------------------------------------------------

    try:

        values = struct.unpack(
            "<5f",
            payload
        )

    except struct.error as e:

        print(
            f"REJECTED: Unable to decode payload: {e}"
        )

        return False, None


    # --------------------------------------------------------
    # Validate every angle
    # --------------------------------------------------------

    for i, value in enumerate(values, 1):

        # Reject NaN and infinity
        if not math.isfinite(value):

            print(
                f"REJECTED: Angle {i} is not finite: {value}"
            )

            return False, None


        # Reject values outside the safety range
        if value < MIN_ANGLE or value > MAX_ANGLE:

            print(
                f"REJECTED: Angle {i} is outside "
                f"the allowed range: {value:.6f}°"
            )

            return False, None


    # --------------------------------------------------------
    # Everything passed
    # --------------------------------------------------------

    return True, values


# ============================================================
# MQTT MESSAGE RECEIVED
# ============================================================

def on_message(client, userdata, msg):

    print("\n" + "=" * 60)
    print("MESSAGE RECEIVED")
    print("=" * 60)

    print(f"Topic        : {msg.topic}")
    print(f"Payload size : {len(msg.payload)} bytes")
    print(f"Raw bytes    : {msg.payload!r}")


    # ========================================================
    # VALIDATE
    # ========================================================

    valid, values = validate_angles(
        msg.payload
    )


    # ========================================================
    # REJECT INVALID MESSAGE
    # ========================================================

    if not valid:

        print()
        print("!!! VALIDATION FAILED !!!")
        print("NOT PUBLISHING TO TRANSMIT TOPIC")
        print("=" * 60)

        root.after(
            0,
            update_status,
            "REJECTED — Invalid angle data",
            "#ff5555"
        )

        return


    # ========================================================
    # VALID MESSAGE
    # ========================================================

    print()
    print("VALIDATION PASSED")
    print("-" * 60)

    for i, value in enumerate(values, 1):

        print(
            f"Angle {i}: {value:.1f}°"
        )


    # ========================================================
    # FORWARD ORIGINAL PAYLOAD
    # ========================================================

    try:

        result = client.publish(
            TRANSMIT_TOPIC,

            # IMPORTANT:
            # Forward the original bytes exactly as received.
            msg.payload,

            qos=0
        )


        if result.rc == mqtt.MQTT_ERR_SUCCESS:

            print()
            print("TRANSMISSION ACCEPTED")
            print(
                f"Published → {TRANSMIT_TOPIC}"
            )
            print(
                f"Bytes transmitted: {len(msg.payload)}"
            )
            print("=" * 60)

            root.after(
                0,
                update_status,
                "VALID — Transmitted",
                "#55ff55"
            )

        else:

            print()
            print(
                f"ERROR: MQTT publish failed. "
                f"Return code: {result.rc}"
            )

            root.after(
                0,
                update_status,
                "ERROR — Transmission failed",
                "#ff5555"
            )


    except Exception as e:

        print()
        print(
            f"ERROR publishing: {e}"
        )

        root.after(
            0,
            update_status,
            "ERROR — Transmission failed",
            "#ff5555"
        )


# ============================================================
# GUI STATUS
# ============================================================

def update_status(text, color):

    status_label.config(
        text=text,
        fg=color
    )


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title(
    "5-Axis MQTT Validation Middleware"
)

root.geometry(
    "800x500"
)

root.minsize(
    700,
    450
)

root.configure(
    bg="#111111"
)


# ============================================================
# TITLE
# ============================================================

title_label = tk.Label(
    root,

    text="5-AXIS MQTT VALIDATION GATEWAY",

    font=("Arial", 22, "bold"),

    bg="#111111",
    fg="#eeeeee"
)

title_label.pack(
    pady=(30, 10)
)


# ============================================================
# DESCRIPTION
# ============================================================

description_label = tk.Label(
    root,

    text=(
        "Validates robotic arm angle commands before transmission"
    ),

    font=("Arial", 11),

    bg="#111111",
    fg="#888888"
)

description_label.pack(
    pady=(0, 25)
)


# ============================================================
# INPUT TOPIC
# ============================================================

input_label = tk.Label(
    root,

    text=f"INPUT\n{VALIDATE_TOPIC}",

    font=("Courier New", 10, "bold"),

    bg="#1a1a1a",
    fg="#ffcc44",

    padx=20,
    pady=15
)

input_label.pack(
    fill="x",
    padx=50,
    pady=5
)


# ============================================================
# ARROW
# ============================================================

arrow_label = tk.Label(
    root,

    text="↓",

    font=("Arial", 28, "bold"),

    bg="#111111",
    fg="#888888"
)

arrow_label.pack(
    pady=5
)


# ============================================================
# VALIDATION RULE
# ============================================================

validation_label = tk.Label(
    root,

    text=(
        "VALIDATION\n"
        "5 × float32  •  20 bytes  •  "
        "0° ≤ every angle ≤ 180°"
    ),

    font=("Courier New", 10, "bold"),

    bg="#222222",
    fg="#55ff55",

    padx=20,
    pady=15
)

validation_label.pack(
    fill="x",
    padx=50,
    pady=5
)


# ============================================================
# ARROW
# ============================================================

arrow_label_2 = tk.Label(
    root,

    text="↓",

    font=("Arial", 28, "bold"),

    bg="#111111",
    fg="#888888"
)

arrow_label_2.pack(
    pady=5
)


# ============================================================
# OUTPUT TOPIC
# ============================================================

output_label = tk.Label(
    root,

    text=f"OUTPUT\n{TRANSMIT_TOPIC}",

    font=("Courier New", 10, "bold"),

    bg="#1a1a1a",
    fg="#55ff55",

    padx=20,
    pady=15
)

output_label.pack(
    fill="x",
    padx=50,
    pady=5
)


# ============================================================
# STATUS
# ============================================================

status_label = tk.Label(
    root,

    text="MQTT: Connecting...",

    font=("Arial", 12, "bold"),

    bg="#111111",
    fg="#ffcc44"
)

status_label.pack(
    pady=(25, 10)
)


# ============================================================
# SAFETY INFORMATION
# ============================================================

safety_label = tk.Label(
    root,

    text=(
        "INVALID DATA IS NEVER FORWARDED\n"
        "No clamping • No correction • Entire packet rejected"
    ),

    font=("Arial", 10, "bold"),

    bg="#111111",
    fg="#ff5555"
)

safety_label.pack(
    pady=5
)


# ============================================================
# CREATE MQTT CLIENT
# ============================================================

client = mqtt.Client()

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message


# ============================================================
# CONNECT TO MQTT
# ============================================================

def connect_mqtt():

    print("=" * 60)
    print("5-AXIS MQTT VALIDATION MIDDLEWARE")
    print("=" * 60)

    print(f"Broker : {BROKER}:{PORT}")
    print(f"Input  : {VALIDATE_TOPIC}")
    print(f"Output : {TRANSMIT_TOPIC}")

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

    print("Closing validation middleware...")

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