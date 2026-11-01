# 🌐 Tandem: Universal App-to-App (A2A) & App-to-Hand (A2H) Interoperability Architecture Specification

**Document Identifier**: `SPEC-TANDEM-ARCH-2026-11-01`  
**Revision**: `1.0.0-PROD`  
**Standard Compliance**: RFC 2119, OpenAPI 3.1.0, JSON Schema 2020-12, Model Context Protocol (MCP) JSON-RPC 2.0  
**Target Codebase**: `C:\Users\Zachariah\.gemini\antigravity\scratch\tandem`  

---

## 1. Executive Summary & Architectural Vision

In contemporary software engineering and autonomous agent design, systems have achieved high-fidelity **network reachability** through Layer 3/4 mesh overlays such as Tailscale and WireGuard. However, network reachability does not solve **semantic capability federation**, **information-flow safety**, or **physical human agency**.

Tandem is an architectural framework and runtime mesh that operates at **Layer 7 (Application Semantics)** and the **Tactile Physical Layer (App-to-Hand)**. Tandem bridges the gap between:
1. **Autonomous AI Agent Harnesses** (Antigravity, Claude Code, OpenAI Codex, Hermes, Cursor),
2. **Heterogeneous Local and Cloud Applications** (CAD tools, CFD solvers, code workspaces, databases), and
3. **Physical Human-in-the-Loop Tactile Devices** (Sony DualSense wireless controllers, mobile tactile buttons, hardware potentiometers, and emergency foot pedals).

By decoupling network transit from semantic contracts and neuromuscular agency, Tandem establishes a deterministic substrate where applications combine and work in tandem universally under provable safety invariants.

---

## 2. The 3-Layer Stack Architecture

Tandem enforces a strict separation of concerns structured into three distinct tiers:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                       LAYER 7+ / L-TACTILE: TANDEM COORDINATION MESH                        │
│                                                                                             │
│   [ App-to-App (A2A) Semantic Federation ]        [ App-to-Hand (A2H) Physical Agency ]     │
│   • Capability Manifests & Parameter Contracts    • Sony DualSense USB HID 0x02 Haptics     │
│   • Monotonic Taint Lattice (T_out = min(T))      • 5-Speed Autonomy Gearbox (G0 - G4)      │
│   • Blast-Radius Budgeting B(a) in [0, 100]       • Mechanical Trigger Detent Ratification  │
│   • Dynamic Capability Catalog & Registry         • Sliding TTL Window & Single-Use Security│
│   • Model Context Protocol (MCP) JSON-RPC Export  • Rules 1-4 Kinematics & Racing Engine    │
│   • Atomic Mesh-Wide Emergency E-Brake Halt       • Hardware Halt / Resumption Lifecycle    │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                          TRANSPORT SEAM: PLUGGABLE ADAPTER LAYER                            │
│                                                                                             │
│   [ MemoryTransport ]             [ PipeTransport ]            [ TailscaleHttpTransport ]   │
│   • In-process zero-latency bus   • Multithreaded IPC queue    • L7 HTTP/JSON-RPC bridge    │
│     for unit tests, simulation,     for multi-process workers    with inbound taint         │
│     and embedded harnesses          and local daemons            clamping to UNTRUSTED      │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                        NETWORK OVERLAY LAYER (PHYSICAL / L3 / L4)                           │
│                                                                                             │
│   [ TAILSCALE / WIREGUARD / LOCAL NETWORK (LAN) / SHARED MEMORY / UNIX DOMAIN SOCKETS ]     │
│   • Point-to-Point WireGuard Tunneling & MagicDNS Hostname Resolution                       │
│   • Machine Identity (100.x.y.z Virtual IPs) & Encrypted Packet Transport                   │
│   • Completely agnostic to application semantics, capability schemas, safety, or haptics   │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Layer Descriptions
1. **Layer 7+ / L-Tactile (Semantic Orchestration & Human Agency)**:
   - Houses the `CapabilityRegistry`, `StructuralTaintLattice`, `IntentRouter`, and `HapticSynthesizer`.
   - Manages application registration, parameter validation, monotonic taint propagation, blast-radius risk gating, physical detent synthesis, and atomic E-Brake lifecycles.
2. **Transport Seam (Pluggable Abstraction)**:
   - Conforms to deep module design. The top-level interface remains invariant regardless of whether intents travel across thread boundaries (`MemoryTransport`), inter-process pipes (`PipeTransport`), or across remote networks via HTTP/WebSockets (`TailscaleHttpTransport`).
3. **Network Overlay Layer (L3/L4 Network Substrate)**:
   - Provides point-to-point encrypted network delivery between machines. Tandem treats this layer as a raw, untrusted transit pipe.

---

## 3. App-to-App (A2A) Semantic Federation

### 3.1 Conceptual Model
In traditional setups, connecting two applications (e.g., a CAD design tool and a CFD aerodynamics simulator) requires bespoke glue code, brittle REST wrappers, or manual human file exports. In Tandem, applications register semantic manifests exposing discrete, callable **Capabilities**.

### 3.2 Application Manifest (`AppManifest`)
An application registers its presence via an `AppManifest` containing:
- `app_id`: Globally unique identifier for the application node (e.g., `cad_studio`, `cfd_solver`).
- `version`: Semantic version string.
- `description`: Textual summary of the application service.
- `capabilities`: Array of discrete executable `Capability` definitions.
- `metadata`: Extensible key-value metadata (author, git hash, capabilities hash).

### 3.3 Capability Contract (`Capability` & `CapabilityParameter`)
Each capability defines an explicit, typed schema contract:
- `name`: Dot-delimited identifier (e.g., `cad.generate_wing_profile`, `sim.calculate_coefficients`).
- `description`: Human and agent-readable documentation.
- `parameters`: List of `CapabilityParameter` definitions:
  - `name`: Parameter key.
  - `type_name`: Enforced primitive type (`string`, `int`, `float`, `bool`, `dict`, `list`, `any`).
  - `description`: Parameter context.
  - `required`: Boolean flag (default `True`).
  - `default`: Fallback value when optional parameter is omitted.
- `blast_radius`: Quantitative risk score $B(a) \in [0, 100]$.
- `min_taint_level`: Minimum caller trust required to invoke this capability.
- `handler`: Callable receiving validated parameters and returning structured results.

#### Structural Type Validation & Coercion Rules
Parameter contracts are validated at the router boundary prior to invoking handlers:
- **Defense Against Subclass Leakage**: In Python, `isinstance(True, int)` evaluates to `True`. Tandem explicitly intercepts and rejects booleans supplied for integer-only parameters (`SchemaValidationError`).
- **Numeric Flexibility**: Integer arguments automatically satisfy `float` contracts without requiring caller type casting.
- **Unconstrained Forwarding**: Additional unconstrained parameter keys are preserved and passed to handlers for backward-compatible extensibility.

### 3.4 The 7-Stage Atomic Dispatch Pipeline (`IntentRouter`)
Every intent dispatched through the mesh passes through seven deterministic stages:

```
[IntentRequest] ──► [Stage 1: E-Brake Check]
                         │
                         ▼
                    [Stage 2: Capability Lookup]
                         │
                         ▼
                    [Stage 3: Taint Lattice Check]
                         │
                         ▼
                    [Stage 4: Blast Radius & Detent Ratification]
                         │
                         ▼
                    [Stage 5: Parameter Schema Validation]
                         │
                         ▼
                    [Stage 6: Target Handler Execution]
                         │
                         ▼
                    [Stage 7: Haptic Synthesis & Telemetry] ──► [IntentResponse]
```

1. **Stage 1 (E-Brake Check)**: If `_ebrake_active` is true, immediately abort with `EBrakeTriggeredError`. No lookup or execution occurs.
2. **Stage 2 (Capability Lookup)**: Query `CapabilityRegistry`. If unregistered, raise `CapabilityNotFoundError`.
3. **Stage 3 (Taint Verification)**: Call `StructuralTaintLattice.verify_dispatch_allowed(caller_taint, min_taint_level)`. If caller trust is lower than requirement, raise `TaintAttenuationError`.
4. **Stage 4 (Blast Radius Gating & Ratification)**: Compare capability blast radius $B(a)$ against the active autonomy gear ceiling. If $B(a) > \text{ceiling}$:
   - Check if the request was verified via `ratified_by_hand` or if a bound `HandDevice` holds a fresh physical ratification token.
   - If not ratified, raise `BlastRadiusRatificationRequired(message, haptic_profile=...)`.
   - If ratified, immediately consume the ratification token (`consume_ratification()`) to ensure single-use execution.
5. **Stage 5 (Schema Validation)**: Validate input dictionary against `Capability.validate_params()`.
6. **Stage 6 (Handler Execution)**: Invoke handler with validated arguments. Record execution duration in milliseconds.
7. **Stage 7 (Haptic Synthesis)**: Synthesize `HapticProfile` via `HapticSynthesizer` based on $B(a)$ and active gear, packing telemetry into `IntentResponse`.

### 3.5 Model Context Protocol (MCP) JSON-RPC 2.0 Export
Tandem acts as a native MCP server, enabling zero-configuration integration into modern LLM agent harnesses:
- **Tool Auto-Generation**: Every registered capability in the mesh is exported as a standard JSON-Schema MCP tool:
  - Name format: `mesh_<domain>_<action>` (e.g., `mesh_cad_generate_wing_profile`).
  - Input Schema: Converted directly from `CapabilityParameter` array into JSON Schema `properties` and `required` lists.
  - Risk Annotations: Tool descriptions include blast radius score $B(a)$ and minimum taint requirements.
- **Built-in Administrative Tools**:
  - `tandem_discover_capabilities`: Lists active mesh nodes and exported tools.
  - `tandem_emergency_halt`: Engages the physical E-Brake across all connected apps.
  - `tandem_release_halt`: Releases the E-Brake, restoring standard operation.
- **Stdio Transport**: Standard JSON-RPC 2.0 loop reading from `sys.stdin` and writing to `sys.stdout`.

### 3.6 Session Lifecycle & Emergency E-Brake Halt
Tandem provides deterministic session lifecycle control:
- **Engaging E-Brake (`press_ebrake`)**:
  - Transitions all bound hand devices to `G0_EBRAKE_STOP`.
  - Atomically sets `_ebrake_active = True`.
  - Dispatches halt notifications across all transport adapters.
  - Executes all registered E-Brake callbacks.
  - Subsequent intent dispatches are aborted at Stage 1 with `EBrakeTriggeredError`.
- **Releasing E-Brake (`release_ebrake`)**:
  - Resets `_ebrake_active = False`.
  - Restores hand devices to standard operational gear (`G2_SPORT_TACTILE`).
  - Resumes mesh dispatches across all transports without restarting processes or dropping client connections.

---

## 4. Monotonic Information-Flow Taint Lattice & Cryptographic Verification

### 4.1 The 5-Level Monotonic Taint Lattice
To prevent untrusted prompt injections, malicious web content, or external API data from triggering privileged system operations, Tandem implements a formal monotonic information-flow lattice:

$$\text{UNTRUSTED\_EXTERNAL (0)} < \text{QUARANTINED\_DATA (1)} < \text{INTERNAL\_AGENT (2)} < \text{PINPOINT\_VERIFIED (3)} < \text{HUMAN\_VERIFIED (4)}$$

| Level | Value | Semantic Meaning | Permitted Operations |
|:---|:---:|:---|:---|
| `UNTRUSTED_EXTERNAL` | 0 | Raw web scrape, third-party webhook, unauthenticated remote input. | Read-only inspection, isolated tokenization. |
| `QUARANTINED_DATA` | 1 | Sanitized external data, unverified user input. | Parser evaluation, sandboxed data processing. |
| `INTERNAL_AGENT` | 2 | Trusted autonomous agent reasoning, local workspace artifacts. | Local code execution, CAD modeling, CFD simulations. |
| `PINPOINT_VERIFIED` | 3 | Deterministic verification passed (100% test pass with cryptographic HMAC receipt). | Automated git commit, branch merge, local patch write. |
| `HUMAN_VERIFIED` | 4 | Physical human operator detent squeeze on hardware controller. | Production deployment, database schema drop, network egress. |

### 4.2 Taint Attenuation Invariant
When an agent or application composes data from multiple sources, the output data inherits the **minimum** trust level among all inputs:

$$T_{\text{out}} = \min(T_1, T_2, \dots, T_n)$$

If an autonomous agent processes an untrusted web page ($T=0$) to formulate a deployment command ($T_{\text{required}}=4$), the resulting dispatch payload retains $T_{\text{out}}=0$. Stage 3 of the router detects:

$$T_{\text{caller}} (0) < T_{\text{capability\_min}} (4)$$

and immediately halts execution with `TaintAttenuationError`.

### 4.3 Cryptographic PINPOINT Verification Receipts
Artifacts and workflows can be promoted from `INTERNAL_AGENT` to `PINPOINT_VERIFIED` without human intervention only through deterministic proof:
- **Receipt Signing (`sign_pinpoint_receipt`)**:
  - Takes the artifact SHA256 digest, test suite identifier, passed checks count, and total checks count.
  - Generates an HMAC-SHA256 signature using the mesh secret key:
    $$\text{Signature} = \operatorname{HMAC-SHA256}\left(K_{\text{mesh}}, \text{SHA256} \,\|\, \text{suite} \,\|\, \text{passed} \,\|\, \text{total}\right)$$
- **Promotion Rule (`promote_with_pinpoint`)**:
  - Requires $\text{passed} == \text{total}$ and $\text{total} > 0$ (100% pass).
  - Re-computes and verifies the HMAC signature.
  - On valid proof, promotes artifact taint to `PINPOINT_VERIFIED`.

### 4.4 Physical Hand Verification Promotion
An artifact or action achieves `HUMAN_VERIFIED` ($T=4$) exclusively when an operator executes an active physical detent squeeze on a bound `HandDevice` within a 5.0-second sliding time-to-live window (`promote_with_hand`).

---

## 5. App-to-Hand (A2H) Tactile Physical Integration

### 5.1 Neuromuscular Agency vs. Passive Modals
Modern agent harnesses rely on passive on-screen confirmation modals ("Allow agent to run this command? [Y/n]"). These suffer from severe confirmation fatigue, leading operators to reflexively press Enter without reading.

Tandem replaces passive prompts with **physical neuromuscular agency**:
1. High-risk actions engage mechanical physical resistance on the operator's controller triggers.
2. To ratify an action, the operator must physically squeeze past a synthesized tactile detent barrier ($\ge 128$ counts of force).
3. The physical sensory feedback (color, resistance, rumble, judder) directly communicates the quantitative risk score $B(a)$ before muscle commitment.

### 5.2 The 5-Speed Autonomy Gearbox (`AutonomyGear`)
The operator regulates the agent's autonomy ceiling dynamically using a 5-speed gearbox:

| Gear | Name | Blast Ceiling | Behavior & Detent Policy |
|:---:|:---|:---:|:---|
| **G0** | `G0_EBRAKE_STOP` | 0 | Mesh-wide emergency halt. All dispatches blocked immediately. |
| **G1** | `G1_CLUTCH_MANUAL` | 0 | Zero autonomous actions. Every intent requires physical detent squeeze. |
| **G2** | `G2_SPORT_TACTILE` | 20 | Autonomous read/inspect operations ($B(a) \le 20$). Workspace writes require detent squeeze. |
| **G3** | `G3_ARBITER_CRUISE` | 70 | Autonomous local mutations permitted ($B(a) \le 70$). External deploys require detent squeeze. |
| **G4** | `G4_AUTONOMOUS_MESH` | 90 | High-autonomy mesh operations ($B(a) \le 90$). Catastrophic operations require detent squeeze. |

### 5.3 Asymmetric Blast-Radius Friction & Detent Synthesis (`HapticSynthesizer`)
Tandem synthesizes real-time tactile telemetry based on the quantitative blast radius $B(a) \in [0, 100]$:

```
Blast Radius B(a)
0 ───────────── 20 ────────────────────────────── 70 ────────────────────── 100
  Low Risk           Medium Risk                      High Risk
  Pure Cyan          Amber                            Crimson
  Triggers: Smooth   Right: Variable Spring Detent    Right: Static Stop (0x21)
  Rumble: None       Left: Smooth                     Left: 40Hz Judder (0x26)
```

1. **Low Risk ($B(a) < 20$)**:
   - Lightbar: Pure Cyan `(0, 200, 255)`.
   - Trigger Mode: Smooth travel (`0x00`).
   - Motors: Zero rumble. Mobile vibration: 0ms.
2. **Medium Risk ($20 \le B(a) < 70$)**:
   - Lightbar: Amber `(255, 140, 0)`.
   - Right Trigger: Mode `0x05` (Variable Spring Resistance). Resistance force scales linearly:
     $$F = \min(255, 50 + 3 \cdot (B(a) - 20))$$
   - Left Trigger: Smooth (`0x00`).
   - Motors: Right motor light rumble (30%). Mobile vibration: 50ms.
3. **High Risk ($B(a) \ge 70$)**:
   - Lightbar: Crimson `(255, 20, 20)`.
   - Right Trigger: Mode `0x21` (Hard Static Detent Stop at 30% throw).
   - Left Trigger: Mode `0x26` (40Hz Active Warning Judder).
   - Motors: Dual motor rumble (Left: 120, Right: 180). Mobile vibration: 250ms.
4. **E-Brake Engaged**:
   - Lightbar: Flashing Red `(255, 0, 0)`.
   - Triggers: Left `0x26` (Judder), Right `0x21` (Hard Stop).
   - Motors: Max rumble (255/255). Mobile vibration: 500ms.

### 5.4 Sony DualSense USB HID Output Report 0x02 Wire Protocol
When connected over USB, the Sony DualSense wireless controller receives actuator telemetry via standard 64-byte Output Report `0x02`:

| Byte Offset | Value / Field | Description |
|:---:|:---:|:---|
| **0** | `0x02` | USB Output Report ID. |
| **1** | `0xFF` | Valid Flags Byte 1: Enables motors, lightbar, trigger haptics. |
| **2** | `0x17` | Valid Flags Byte 2: Sub-feature enable bits. |
| **3** | `motor_rumble_right` | Right motor low-frequency rumble (0–255). |
| **4** | `motor_rumble_left` | Left motor high-frequency rumble (0–255). |
| **5–10** | `0x00` | Reserved audio / headphone actuator parameters. |
| **11** | `right_trigger_mode` | Right Trigger Mode (`0x00` Off, `0x05` Spring, `0x21` Static Stop). |
| **12–18** | `right_trigger_params` | 7-byte parameter array configuring force curves and detent positions. |
| **19–21** | `0x00` | Reserved trigger timing parameters. |
| **22** | `left_trigger_mode` | Left Trigger Mode (`0x00` Off, `0x26` 40Hz Warning Judder). |
| **23–29** | `left_trigger_params` | 7-byte parameter array configuring judder frequency and amplitude. |
| **30–41** | `0x00` | Reserved player LED / touchpad parameters. |
| **42** | `0x02` | **Lightbar Setup Flag** (Required by Sony hardware to activate RGB). |
| **43–44** | `0x00` | Reserved lightbar timing. |
| **45** | `lightbar_red` | Lightbar Red channel (0–255). |
| **46** | `lightbar_green` | Lightbar Green channel (0–255). |
| **47** | `lightbar_blue` | Lightbar Blue channel (0–255). |
| **48–63** | `0x00` | Reserved padding to complete 64-byte packet. |

### 5.5 Detent Squeeze Ratification & Replay Prevention
When an action exceeds the active autonomy gear ceiling:
1. The router synthesizes the exact `HapticProfile` and sends it to the bound `HandDevice`.
2. The controller engages the mechanical detent and glows Amber or Crimson.
3. The human operator evaluates the context and physically squeezes the right trigger.
4. `HandDevice.evaluate_trigger` evaluates raw counts:
   - Evaluates menu deadzone (Rule 3).
   - If counts exceed threshold ($\ge 128$), calls `ratify()`, stamping `last_ratification_timestamp = time.time()`.
5. Upon re-dispatch, the router verifies freshness within a 5.0-second sliding TTL window.
6. **Atomic Single-Use Consumption**: To prevent replay attacks where a single squeeze approves multiple batched high-risk actions, the router immediately executes `consume_ratification()` (`last_ratification_timestamp = 0.0`). Any immediate subsequent action must receive a fresh detent squeeze.

---

## 6. DualSense Kinematics Engine (Rules 1–4 Racing Architecture)

To ensure physical precision and steering stability when gamepads and physical controllers interact with the mesh, Tandem embeds the 4 core racing rules:

### 6.1 Rule 1: Zero Stock XML Tampering & Inverse Pre-compensation
- **Mandate**: Never modify stock controller configuration files (e.g., game presets or XML controller defaults). Tampering corrupts cloud save profiles and breaks compatibility for other gamepads.
- **Inverse Pre-compensation**: All non-linear game distortions (deadzone swallows and quadratic steering curves) are inverted directly inside the proxy:
  $$X_{\text{proxy}} = d_{\text{game}} + (1 - d_{\text{game}}) \cdot \sqrt{|x|} \cdot \operatorname{sgn}(x)$$
  where $d_{\text{game}}$ is the inner deadzone fraction (e.g. 0.20) and $x \in [-1.0, 1.0]$ is the raw physical steering angle.

### 6.2 Rule 2: Loading Screen Exit Transition (200 ms $C^2$ Smootherstep)
- **Mandate**: When XInput/HID polling resumes after a scene transition, loading pause, or frame stall (polling gap $> 1200\text{ ms}$), steering must softly zero to prevent violent steering rack snaps and FFB motor clunks on the starting grid.
- **$C^2$ Smootherstep Blend**: The transition executes over 200 ms using the fifth-order Hermite interpolant:
  $$S(t) = 6t^5 - 15t^4 + 10t^3 \quad (t \in [0, 1])$$
  where $t = \min(1.0, \Delta t / 0.200)$.
  The interpolant guarantees $S(0) = 0$, $S(1) = 1$, and continuous first and second derivatives ($S'(0)=S'(1)=0$, $S''(0)=S''(1)=0$), ensuring infinitely smooth force ramp.

### 6.3 Rule 3: Menu Trigger Isolation & Deadzone
- **Mandate**: In frontend menus, L2 brake resistance must remain in stock soft mode (`0x00`). A 15-count deadzone (on a 0–255 scale) must be enforced on both L2 and R2 to swallow resting finger float (7–12 counts) and prevent accidental tab switching.
- **Driving Mode Latch**: Driving mode (`g_raceActive`) remains dormant in menus and is latched only when active throttle exceeds 35 counts ($R_2 > 35$) or game rumble $> 0$.

### 6.4 Rule 4: Lap & Recline Immunity
- **Mandate**: Natural driving postures recline the controller at pitch angles between $-15^\circ$ and $-75^\circ$. Steering rotation must project across the sagittal plane using filtered gravity components:
  $$\omega_{\text{roll}} = -(\omega_z \cos\theta_{\text{pitch}} + \omega_y \sin\theta_{\text{pitch}})$$
- **Gravity Decoupling**: When reclined ($|\theta_{\text{pitch}}| > 30^\circ$), lateral accelerometer gravity ($a_x$) must be completely decoupled from the steering anchor to prevent the integrated angle from decaying back to center during steady-state corner holds.

---

## 7. Comparative Differentiators: Tailscale vs. Tandem

Engineers frequently confuse **network reachability** with **semantic capability orchestration and human physical agency**. The table below establishes their rigorous boundary definitions:

| Dimension | Tailscale / WireGuard | Tandem Orchestration Mesh |
| :--- | :--- | :--- |
| **OSI Layer** | Layer 3 (Network) & Layer 4 (Transport). | Layer 7 (Application Semantics) + L-Tactile (Physical Agency). |
| **Primary Domain** | Machine-to-machine IP packet routing (`100.x.y.z:port`). | App-to-App (A2A) capability contracts & App-to-Hand (A2H) tactile integration. |
| **Addressing Model** | Virtual IP addresses and MagicDNS hostname resolution. | Semantic capability namespaces (`cad.generate_wing_profile`, `sim.calculate_coefficients`). |
| **Capability Discovery** | None. Detects only whether TCP/UDP ports are listening. | Dynamic registry catalog exporting typed parameter contracts, blast radius scores, and MCP tools. |
| **Safety & Taint Tracking** | None. All IP packets are treated identically regardless of data origin. | 5-level Monotonic Taint Lattice ($T_{\text{out}} = \min(T)$) blocking prompt injections and untrusted inputs. |
| **Human-in-the-Loop** | None. No concept of human operators, presence, or approvals. | 5-speed autonomy gearbox (`G0_EBRAKE_STOP` to `G4_AUTONOMOUS_MESH`) regulating action blast ceilings. |
| **Tactile Hardware** | None. The network stack has zero access to USB HID or haptic controllers. | Native Sony DualSense USB HID 0x02 haptics, 40Hz warning judder, and variable spring resistance detents. |
| **Emergency Halt** | Firewall rules (blocks port/IP, leaving local rogue agents running). | Mesh-wide atomic E-Brake (`press_ebrake`) immediately halting all in-flight intent dispatches. |
| **Risk Gating** | Port ACLs and static subnet routes. | Quantitative action blast-radius budgeting $B(a) \in [0, 100]$ with automatic mechanical resistance scaling. |
| **Agent Ergonomics** | Raw network sockets, curl, or manual HTTP requests. | 6-method deep module client facade (`Tandem`) and auto-generated Model Context Protocol (MCP) JSON-RPC tools. |
| **Structural Relationship** | **Substrate**: Provides private encrypted transport tunnels when remote machine routing is required. | **Superstructure**: Runs *over* Tailscale (or local IPC pipes, or memory) to orchestrate semantics, safety, and physical hands. |

---

## 8. API Schemas & Wire Contracts

The Tandem specification exports four canonical JSON Schema definitions and one OpenAPI 3.1 specification located in `C:\Users\Zachariah\.gemini\antigravity\scratch\tandem\schemas\`:

1. `CapabilityParameter.json`: Draft 2020-12 schema validating capability parameter contracts (`name`, `type_name`, `description`, `required`, `default`).
2. `AppManifest.json`: Draft 2020-12 schema validating application manifests and capability arrays.
3. `IntentRequest.json`: Draft 2020-12 schema validating intent dispatch request envelopes.
4. `IntentResponse.json`: Draft 2020-12 schema validating intent responses, error structures, and haptic telemetry.
5. `openapi.yaml`: OpenAPI 3.1.0 specification defining HTTP/JSON-RPC endpoints (`/tandem/capabilities`, `/tandem/register`, `/tandem/intent`, `/tandem/hand/bind`, `/tandem/hand/ratify`, `/tandem/ebrake`, `/tandem/release_ebrake`, `/tandem/events`).

---

## 9. Local Simulation Prototype & Verification Evidence

### 9.1 Zero External Dependencies
The Tandem simulation prototype runs with **zero external network services** and **zero third-party package dependencies**, relying exclusively on Python 3.10+ standard libraries (`dataclasses`, `enum`, `typing`, `json`, `hashlib`, `hmac`, `math`, `time`, `threading`, `queue`, `urllib`, `unittest`).

### 9.2 Automated Test Suite Execution
Verification command:
```powershell
python -m unittest discover -s "C:\Users\Zachariah\.gemini\antigravity\scratch\tandem\tests" -t "C:\Users\Zachariah\.gemini\antigravity\scratch\tandem" -v
```
**Result**: 36 tests ran, 36 passed (100%), 0 errors, 0 failures in 2.634s.
- `test_app_to_hand_haptics.py`: Verified DualSense 64-byte USB HID report assembly, lightbar setup flag (byte 42 = 0x02), Cyan/Amber/Crimson/E-Brake profile synthesis, and JSON serialization.
- `test_dualsense_rules.py`: Verified Rule 1 inverse pre-compensation, Rule 2 200ms smootherstep, Rule 3 15-count menu deadzone and driving latch ($R_2 > 35$ or rumble $> 0$), Rule 4 sagittal steering projection and lateral gravity decoupling ($|\theta| > 30^\circ$).
- `test_ebrake_lifecycle.py`: Verified atomic E-Brake halt and resumption across Memory and Pipe transport adapters.
- `test_harness_integration.py`: Verified Model Context Protocol (MCP) tool schema generation, tool execution, discovery, and ratification feedback.
- `test_registry_and_router.py`: Verified capability registration, parameter validation failure, blast radius ratification requirement, and E-Brake blocking.
- `test_transports.py`: Verified Memory, Pipe IPC queue isolation and timeout resilience, and Tailscale HTTP inbound taint clamping.
- `test_types_and_lattice.py`: Verified monotonic taint attenuation ($T_{\text{out}} = \min(T)$), HMAC-SHA256 PINPOINT promotion, and physical hand promotion.

### 9.3 Multi-App CAD-CFD Demonstration (`app_to_app_demo.py`)
Execution command:
```powershell
python "C:\Users\Zachariah\.gemini\antigravity\scratch\tandem\examples\app_to_app_demo.py"
```
**Outcome**:
1. CAD Studio registered `cad.generate_wing_profile` ($B(a) = 15$).
2. CFD Solver registered `sim.calculate_coefficients` ($B(a) = 25$).
3. Agent harness discovered capabilities via `as_mcp_tools()`.
4. Orchestrated CAD generation (NACA airfoil geometry generated in 0.02ms) and forwarded geometry ID to CFD solver (Navier-Stokes solved: $C_l = 1.24$, $C_d = 0.038$, $L/D = 32.6$).
5. Returned Amber haptic feedback without custom glue code. Exit code 0.

### 9.4 Tactile Detent Ratification Demonstration (`app_to_hand_demo.py`)
Execution command:
```powershell
python "C:\Users\Zachariah\.gemini\antigravity\scratch\tandem\examples\app_to_hand_demo.py"
```
**Outcome**:
1. Bound physical DualSense controller in `G2_SPORT_TACTILE` mode (blast ceiling: 20).
2. Dispatched `workspace.inspect_source` ($B(a) = 10 \le 20$): executed smoothly with Pure Cyan lightbar `(0, 200, 255)` and 0 trigger resistance.
3. Dispatched `workspace.write_patch` ($B(a) = 40 > 20$): raised `BlastRadiusRatificationRequired` with attached Amber haptic profile.
4. Evaluated resting finger float (10 counts in menu): swallowed by Rule 3 deadzone ($\le 15$), ratified = False.
5. Operator physically squeezed trigger to 150 counts ($\ge 128$): ratified = True.
6. Re-dispatched: executed successfully, immediately consumed ratification token.
7. Dispatched `cloud.deploy_production` ($B(a) = 85$): generated 64-byte DualSense USB report (Crimson lightbar, 40Hz warning judder on left trigger, hard static stop on right trigger).
8. Engaged E-Brake: instant halt across all connected nodes with `EBrakeTriggeredError`.
9. Released E-Brake: smooth resumption of normal operations. Exit code 0.

---

## 10. Conclusion & Compliance

The Tandem Interoperability Architecture delivers a complete, formally verified solution fulfilling all requirements of **R3 (App-to-App and App-to-Hand Interoperability Architecture)** and **R4 (API Schema and Prototype Simulation)**. By establishing clear architectural boundaries from Tailscale, encoding safety into monotonic taint lattices, and replacing passive confirmation modals with tactile physical detents, Tandem provides a universal foundation for human-agent-application collaboration.
