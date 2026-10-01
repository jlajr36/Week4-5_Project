# Week 4 Report: Software-in-the-Loop (SIL) Validation
## 1. System Architecture & MQTT Facilitation (Task 1)

The Phase 1 Software-in-the-Loop (SIL) simulation establishes two-way communication between a Python control signal publisher, a SysML Model representing the System of Interest (SoI), and a Python receiving subscriber. Facilitated by the public broker `test.mosquitto.org:1883`, the SysML SoI subscribes to 20-byte payloads (five Float32 joint angles) on topic `validatecontrolsignals/roboticarm`, validates angles against tolerance bands, and publishes approved signals on topic `transmitcontrolsignals/roboticarm`.

<p align="center">
  <img src="robot_act_model.png" alt="Task 1 Base SysML Activity Diagram" width="340"><br>
  <em>Figure 1: Task 1 Base SysML Activity Diagram Workflow for Gesture Control SIL</em>
</p>

## 2. Signal Range Validation Logic & Decision Flow (Task 2)

To ensure physical joint safety, an Opaque Action evaluates received control signals against required limits before transmission. A Decision Gateway then routes execution based on the boolean result `valid`:

| Joint Parameter | Validation Logic Condition |
| :--- | :--- |
| **Joint Angle 1** | `gestureAngle1 >= 0 && gestureAngle1 <= 1` |
| **Joint Angle 2** | `gestureAngle2 >= 1 && gestureAngle2 <= 2` |
| **Joint Angle 3** | `gestureAngle3 >= 2 && gestureAngle3 <= 3` |
| **Joint Angle 4** | `gestureAngle4 >= 3 && gestureAngle4 <= 4` |
| **Joint Angle 5** | `gestureAngle5 >= 4 && gestureAngle5 <= 5` |

### Decision Node Branching Execution:
* **`[valid == true]`**: Control proceeds to `MQTTPublishMessage`, sending the 20-byte payload to the subscriber on `transmitcontrolsignals/roboticarm`.
* **`[valid == false]`**: Control bypasses `MQTTPublishMessage`, executing `MQTTCloseConnection` and looping to the Merge Node to fetch new signals.

<p align="center">
  <img src="zoomed_on_val.png" alt="Task 2 Validation Guard Logic Detail" width="340"><br>
  <em>Figure 2: Task 2 Validation Guard Logic Detail & Decision Node Branching</em>
</p>

## 3. End-to-End Experimental Verification & Console Proof

Software-in-the-Loop execution was confirmed by matching SysML model console logs with Python subscriber output. The generated values satisfied all joint bounds, triggering signal dispatch and bit-for-bit reception.

<div align="center">
  <table border="0" style="border: none;">
    <tr>
      <td align="center" style="border: none;"><img src="producted_values.png" width="210" alt="SysML Console Output"></td>
      <td align="center" style="border: none;"><img src="rec_values.png" width="210" alt="Python Subscriber Output"></td>
    </tr>
  </table>
  <em>Figure 3 & 4: Side-by-Side Console Output — SysML Produced Array vs. Python Received Array</em>
</div>

<br>

### Verification Results Table

| Parameter | SysML Produced Value | Python Received Value | Validation Status |
| :--- | :--- | :--- | :--- |
| **Joint Angle 1** | `0.9062` | `0.906` | **PASSED** |
| **Joint Angle 2** | `1.1878` | `1.188` | **PASSED** |
| **Joint Angle 3** | `2.0994` | `2.099` | **PASSED** |
| **Joint Angle 4** | `3.9964` | `3.996` | **PASSED** |
| **Joint Angle 5** | `4.0597` | `4.060` | **PASSED** |

## 4. Conclusion

The Phase 1 SIL project successfully demonstrates end-to-end gesture control signal transmission and tolerance verification. Tasks 1 and 2 are fully accomplished, establishing a robust, verified baseline for Phase 2 Hardware-in-the-Loop (HIL) deployment.
