---
name: tandem-a2h
description: Universal App-to-App (A2A) and App-to-Hand (A2H) orchestration mesh for agent harnesses and tactile devices. Use when coordinating heterogeneous applications, querying capability schemas, binding DualSense/mobile physical controllers, enforcing blast-radius haptic detents, or operating at Layer 7 above network overlays like Tailscale.
---

# 🌐 Tandem: Universal App-to-App (A2A) & App-to-Hand (A2H) Coordination Mesh

Tandem is a deep, ergonomic architectural framework and runtime mesh that enables AI agent harnesses (Antigravity, Harness², Claude Code, OpenCode, Codex, Cursor), local/cloud applications, and physical human-in-the-loop devices to combine and work in tandem universally.

---

## 1. Why Tailscale is Not Enough: The Architectural Difference

Engineers frequently confuse **network reachability** with **semantic capability orchestration and human physical agency**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TANDEM ORCHESTRATION LAYER                           │
│                                                                             │
│  [ App-to-App (A2A) ]                     [ App-to-Hand (A2H) ]             │
│  • Capability Schemas & Type Contracts    • DualSense USB HID 0x02 Haptics  │
│  • Monotonic Taint Lattice (T_out=min(T)) • 5-Speed Autonomy Gearbox        │
│  • Blast-Radius Budgeting [0, 100]        • Tactile Trigger Detents         │
│  • Standard MCP JSON-RPC 2.0 Export       • Instant Hardware E-Brake Halt   │
├─────────────────────────────────────────────────────────────────────────────┤
│                         TRANSPORT SEAM ADAPTERS                             │
│  [ In-Memory Bus ]   [ Local IPC / Pipes ]   [ L7 HTTP / WS Bridge ]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                          NETWORK OVERLAY LAYER                              │
│                                                                             │
│  [ TAILSCALE / WIREGUARD / LAN ]                                            │
│  • Machine Identity & 100.x.y.z Virtual IPs                                 │
│  • Point-to-Point WireGuard Encryption & MagicDNS Routing                   │
│  • Layer 3 / 4 Packet Tunnel (Zero Application or Semantic Awareness)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Dimension | Tailscale / WireGuard (L3/L4) | Tandem Mesh (L7 Semantic + L-Tactile) |
| :--- | :--- | :--- |
| **Domain** | Machine-to-machine IP routing (`100.x.y.z:port`) | App-to-App (A2A) schemas & App-to-Hand (A2H) physical agency |
| **Capability Discovery** | None (only open TCP/UDP ports) | Dynamic semantic catalog with JSON-Schema parameter contracts |
| **Safety / Taint Tracking** | None (all packets treated equally) | Monotonic Taint Lattice (`UNTRUSTED_EXTERNAL` to `HUMAN_VERIFIED`) |
| **Human-in-the-Loop** | None | Physical trigger detents, tactile vibration, lightbars, e-brakes |
| **Risk Gating** | Port ACLs / firewall rules | Dynamic action blast-radius scoring $B(a) \in [0, 100]$ |
| **Agent Ergonomics** | Raw network sockets / curl | 3-line Python facade, auto-generated MCP tool definitions |

---

## 2. Core Pillars

### Pillar A: App-to-App (A2A) Semantic Federation
- Applications register an `AppManifest` exposing discrete `Capability` objects.
- Each capability defines typed parameter contracts (`CapabilityParameter`), minimum required caller taint level, and a blast radius risk score $B(a) \in [0, 100]$.
- Invoking another app's capability is a single ergonomic call:
  ```python
  response = mesh.call("cad.generate_wing_profile", {"camber_percent": 4.0})
  ```

### Pillar B: App-to-Hand (A2H) Physical Agency & Tactile Detents
- Physical devices (`HandDevice`) bind directly to the mesh:
  - **Sony DualSense Wireless Controller**: USB HID Report 0x02 generates active 40Hz judder, variable spring resistance, and static detents on adaptive triggers with lightbar setup flags (byte 42 = 0x02).
  - **DualSense Kinematics & Rules**:
    - **Rule 1 Pre-compensation**: Inverse function $X_{\text{proxy}} = d_{\text{game}} + (1 - d_{\text{game}}) \cdot \sqrt{|x|} \cdot \operatorname{sgn}(x)$ eliminates deadzone swallows.
    - **Rule 2 Smootherstep Transition**: 200 ms $C^2$ smootherstep blend $S(t) = 6t^5 - 15t^4 + 10t^3$ softly zeroes frame 0 on stall recovery (>1200 ms).
    - **Rule 3 Menu Deadzone**: 15-count deadzone swallows resting finger float (7-12 counts); driving mode latches only when $R_2 > 35$ or rumble $> 0$.
    - **Rule 4 Lap & Recline Immunity**: Sagittal projection $\omega_{\text{roll}} = -(\omega_z \cos(\theta) + \omega_y \sin(\theta))$ decouples lateral gravity ($a_x$) when $|\theta_{\text{pitch}}| > 30^\circ$.
  - **Mobile Phones**: iOS Shortcuts Action Button / Android Quick Settings webhook triggers.
  - **Tactile Sliders & Foot Pedals**: Physical potentiometers controlling agent speed.
  - **Physical E-Brake (`G0_EBRAKE_STOP`) & Release**: Pulling the e-brake immediately broadcasts an atomic halt across all connected apps; releasing resets the mesh smoothly.
- **Asymmetric Blast-Radius Friction**:
  - $B(a) < 20$ (Read/Inspect): Pure Cyan lightbar `(0, 200, 255)`, zero trigger friction.
  - $20 \le B(a) < 70$ (Local Mutation): Amber lightbar `(255, 140, 0)`, variable spring resistance detent (mode `0x05`).
  - $B(a) \ge 70$ (External Egress / Deploy): Crimson lightbar `(255, 20, 20)`, hard static resistance stop (mode `0x21`) on right trigger + active warning judder (mode `0x26`) on left trigger.
  - **Detent Squeeze Ratification**: High-risk actions throw `BlastRadiusRatificationRequired` (carrying the exact `HapticProfile`) unless the human deliberately squeezes the trigger past the mechanical detent!

### Pillar C: Universal Agent Harness Ergonomics (`/codebase-design`)
- Conforms to deep module design:
  - **Small Interface**: High-leverage client facade (`connect`, `register_app`, `register_hand`, `call`, `press_ebrake`, `release_ebrake`, `as_mcp_tools`).
  - **Deep Implementation**: Hides schema validation, taint promotion, blast-radius detents, transport serialization, and DualSense USB byte manipulation.
  - **Clean Seam**: Pluggable `TransportAdapter` (`MemoryTransport`, `PipeTransport`, `TailscaleHttpTransport`).
- Auto-generates standard Model Context Protocol (MCP) tool schemas for instant plug-and-play in Antigravity, Claude Code, Cursor, OpenCode, Codex, or Harness².

---

## 3. Structural Invariants (`/principle-encode-lessons-in-structure`)

Rules are encoded directly into types and runtime guards, never left as fragile prompt prose:
1. **Taint Attenuation Invariant**:
   $$T_{\text{out}} = \min(T_1, \dots, T_n)$$
   Calling an internal capability with `UNTRUSTED_EXTERNAL` taint raises `TaintAttenuationError` at the router boundary.
2. **Blast Radius Gating Invariant**:
   If $B(a) > \text{gear.blast\_ceiling}$, dispatch raises `BlastRadiusRatificationRequired(message, haptic_profile=...)` unless ratified by detent squeeze. Fresh ratification is consumed immediately to enforce single-use security.
3. **E-Brake Halt & Resumption Invariant**:
   When E-Brake is engaged, any dispatch immediately fails with `EBrakeTriggeredError`. Releasing E-Brake restores standard operation across all connected transports without process restarts.

---

## 4. Quickstart Guide

### Python API Integration
```python
from tandem import Tandem, AutonomyGear, CapabilityParameter

# 1. Initialize local mesh node
mesh = Tandem.local(app_id="my_agent")

# 2. Register capabilities
mesh.register_capability(
    name="data.summarize",
    description="Summarize dataset metrics",
    parameters=[CapabilityParameter(name="dataset_id", type_name="string", description="ID")],
    blast_radius=10,
    handler=lambda p: {"rows": 1000, "status": "ok"},
)

# 3. Bind tactile DualSense controller
mesh.register_hand("dualsense_01", device_type="dualsense", active_gear=AutonomyGear.G2_SPORT_TACTILE)

# 4. Dispatch with haptic feedback
resp = mesh.call("data.summarize", {"dataset_id": "sales_q3"})
print(resp.data)
```

### Running as an MCP Server
Add Tandem to your agent's MCP config:
```json
{
  "mcpServers": {
    "tandem-mesh": {
      "command": "python",
      "args": ["-m", "tandem.harness.mcp_server"],
      "cwd": "C:\\Users\\Zachariah\\.gemini\\antigravity\\scratch\\tandem"
    }
  }
}
```

### Running Automated Test Suite
```powershell
python -m unittest discover -s "C:\Users\Zachariah\.gemini\antigravity\scratch\tandem\tests" -t "C:\Users\Zachariah\.gemini\antigravity\scratch\tandem" -v
```
