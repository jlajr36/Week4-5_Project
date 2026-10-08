# EECE 5496 Project 4.2 Report: MediaPipe–SysML Integration for Robotic Arm Control

## 1. System Architecture & Setup

The objective of this project was to implement a Hardware-in-the-Loop (HIL) and Software-in-the-Loop (SIL) control framework for a 5-Degree-of-Freedom (5-DOF) physical robotic arm using real-time human hand gestures. The control architecture consists of three main components:

1. **User Interface (MediaPipe Front-End):** A GitHub-hosted web interface captures webcam video and converts hand gestures into five joint-angle values for the Base, Shoulder, Elbow, Wrist, and Claw. The values are sent through MQTT to `validatecontrolsignals/roboticarm/ja`.

2. **System of Interest (SysML Activity Model):** The executable SysML activity model receives the joint-angle values, validates them, and forwards valid commands to the physical controller.

3. **Robotic Arm Hardware:** The physical robotic arm receives valid commands from `transmitcontrolsignals/roboticarm/ja` and uses the joint-angle values to control the servo motors.

The communication path is: **MediaPipe Interface → `validatecontrolsignals/roboticarm/ja` → SysML Validation → `transmitcontrolsignals/roboticarm/ja` → Robotic Arm**

---

## 2. SysML Model Updates & Validation Logic

The SysML activity model was updated to support the MediaPipe interface and validate incoming joint-angle commands.

The primary updates include:

- **Interface Launch Action:** The previous interface launch process was updated to use the GitHub-hosted MediaPipe User-Gesture Interface.
- **Joint Angle Boundary Verification:** Each incoming joint-angle value is checked to ensure it is within **0° to 180°**.
- **Claw Limit:** The claw command is checked to ensure it does not exceed **168°**.
- **MQTT Communication:** The model receives commands from `validatecontrolsignals/roboticarm/ja` and publishes valid commands to `transmitcontrolsignals/roboticarm/ja`.
- **Decision Gateway Routing:** Valid commands continue to the transmission path, while invalid commands are prevented from being transmitted to the robotic arm.

These checks provide a validation layer between the gesture interface and the physical hardware.

---

## 3. Task 1 Physical Manipulation Trajectory

The integrated system was demonstrated using **Task 1: Slide the Object**. The sequence moves the arm to the object at Position O, grips the object, moves it to Position A, returns to Position O, moves it to Position B, returns to Position O, and finally returns to the home position.

| Step | Motion Phase | Joint Angles `[Base, Shoulder, Elbow, Wrist, Claw]` | Operational Description |
| :---: | :--- | :--- | :--- |
| **1** | Start at Home | `[90.0, 90.0, 90.0, 90.0, 90.0]` | Initial home position |
| **2** | Approach Object (Pos O) | `[0.0, 110.0, 0.0, 90.0, 90.0]` | Move the arm to the object |
| **3** | Grip Object | `[0.0, 110.0, 0.0, 90.0, 166.0]` | Close the claw to grip the object |
| **4** | Slide to Pos A | `[50.0, 110.0, 0.0, 90.0, 166.0]` | Move the object to Position A |
| **5** | Slide Back to Pos O | `[0.0, 110.0, 0.0, 90.0, 166.0]` | Return the object to Position O |
| **6** | Slide Forward to Pos B | `[0.0, 151.0, 44.0, 90.0, 166.0]` | Move the object to Position B |
| **7** | Slide Back to Pos O | `[0.0, 110.0, 0.0, 90.0, 166.0]` | Return the object to Position O |
| **8** | Return Home & Release | `[90.0, 90.0, 90.0, 90.0, 90.0]` | Return to the home position and release the object |

The claw angle used while holding the object was **166°**, below the specified **168°** maximum.

---

## 4. Physical Testing & Validation Results

The system was tested by sending joint-angle commands from the MediaPipe interface through the SysML activity model to the physical robotic arm.

The test demonstrated that the commands were received by the SysML model, validated, and transmitted to the robotic arm. The arm successfully performed all eight steps of Task 1, including gripping the object, moving it to Positions A and B, returning to Position O, and returning home.

The SysML model served as a validation layer between the interface and physical arm.

---

## 5. Conclusion

This project demonstrated an integrated control system connecting a MediaPipe hand-gesture interface, an executable SysML activity model, MQTT communication, and a physical 5-DOF robotic arm.

The SysML model validated incoming joint-angle commands before transmission to the robotic arm. The system successfully performed Task 1, demonstrating the control path from hand gesture input, through SysML validation, to physical robotic-arm movement.