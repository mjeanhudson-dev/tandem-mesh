# 🌐 Tandem: Universal App-to-App (A2A) & App-to-Hand (A2H) Orchestration Mesh

> **Architectural Paradigm**: Where Tailscale connects machines at Layer 3/4 via WireGuard IPs, Tandem connects applications and physical hands at Layer 7 and the Tactile Human-in-the-Loop Layer.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-25%20passed%20%28100%25%29-brightgreen.svg)]()
[![Architecture](https://img.shields.io/badge/design-Deep%20Module-orange.svg)]()

---

## 🎯 1. The Core Problem: Why Tailscale is Not Enough

Tailscale is magnificent at solving **machine-to-machine network reachability**. It creates a WireGuard mesh, assigns virtual IPs (`100.x.y.z`), and provides end-to-end packet encryption.

However, Tailscale stops at Layer 4 (TCP/UDP ports). When building modern multi-agent systems and multi-device suites, you encounter questions Tailscale cannot answer:
1. **Semantic Capability Discovery**: Does that IP host a CAD renderer, an LLM agent, a flight simulator, or an IDE?
2. **Schema & Contract Negotiation**: What arguments and types does that service accept, and what invariants are enforced?
3. **Information-Flow Safety**: If an untrusted web scraper sends data to that port, can it accidentally trigger a high-privilege local command or prompt injection?
4. **Physical Tactile Agency (App-to-Hand / A2H)**: Where is the human operator? How does the human feel mechanical resistance before a destructive deploy fires? How does the operator pull a physical E-Brake to instantly halt all running agents?

**Tandem runs over Tailscale (or local IPC, pipes, and memory)**, providing the semantic, safety, and physical tactile layer that makes applications, agent harnesses, and physical devices combine seamlessly.

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

---

## 🏛️ 2. Architectural Pillars

### A. Deep Module Design (`/codebase-design`)
Per Ousterhout and Feathers:
- **Small Interface**: Callers and agent harnesses interact with a 6-method facade:
  ```python
  mesh = Tandem.local(app_id="studio")
  mesh.register_app(manifest)
  mesh.register_hand(device)
  response = mesh.call(capability_name, params)
  mesh.press_ebrake()
  tools = mesh.as_mcp_tools()
  ```
- **Deep Implementation**: Hides capability registry catalogs, structural type coercion, monotonic taint lattices, blast-radius risk calculations, DualSense USB HID 0x02 report generation, and transport dispatch.
- **Clean Seam (`TransportAdapter`)**: Supports zero-latency `MemoryTransport`, queue-backed `PipeTransport`, and networked `TailscaleHttpTransport`.

### B. Encode Lessons in Structure (`/principle-encode-lessons-in-structure`)
Rather than relying on fragile prompt instructions ("please verify permissions before invoking tool X"), invariants are enforced by type structures and boundary exceptions:
- **`TaintAttenuationError`**: Raised if a caller with `UNTRUSTED_EXTERNAL` taint attempts to invoke an `INTERNAL_AGENT` or `PINPOINT_VERIFIED` capability.
- **`BlastRadiusRatificationRequired`**: Raised if an action's risk $B(a)$ exceeds the active autonomy gear ceiling without physical hand ratification.
- **`EBrakeTriggeredError`**: Raised immediately across all transports if the emergency brake is active.
- **`SchemaValidationError`**: Raised before handler execution if parameters deviate from the declared contract.

### C. App-to-Hand (A2H) Tactile Steering & Blast-Radius Friction
Connects human physical hands directly into agent execution loops:
- **DualSense Wireless Controller Support**:
  - $B(a) < 20$ (Read/Inspect): Pure Cyan lightbar `(0, 200, 255)`, zero trigger friction (mode `0x00`).
  - $20 \le B(a) < 70$ (Local Workspace Mutation): Amber lightbar `(255, 140, 0)`, variable spring resistance detent (mode `0x05`).
  - $B(a) \ge 70$ (External Egress / Deploy): Crimson lightbar `(255, 20, 20)`, hard static stop (mode `0x21`) on right trigger + active 40Hz warning judder (mode `0x26`) on left trigger.
  - **Detent Squeeze Ratification**: High-risk actions halt and demand that the human physically squeeze past the mechanical detent to ratify the operation.
- **Emergency E-Brake (`G0_EBRAKE_STOP`)**: Pulling the e-brake halts all background processes and agents immediately.

---

## 🚀 3. Quickstart & Usage

### 1. Minimal App-to-App Setup
```python
from tandem import Tandem, CapabilityParameter

mesh = Tandem.local(app_id="orchestrator")

# Register an image analysis app
mesh.register_capability(
    name="vision.detect_objects",
    description="Detect bounding boxes in image",
    parameters=[CapabilityParameter(name="image_id", type_name="string", description="Asset ID")],
    blast_radius=15,
    handler=lambda p: {"objects": ["wing", "flap", "rudder"]},
)

# Dispatch across the mesh
resp = mesh.call("vision.detect_objects", {"image_id": "frame_042"})
print(resp.data)  # {'objects': ['wing', 'flap', 'rudder']}
```

### 2. Plug into Any Agent Harness via MCP
Any agent harness (Antigravity, Claude Code, Cursor, Codex, OpenCode, Harness²) can use Tandem via standard MCP:
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

---

## 🧪 4. Verification Suite

All 25 automated unit and structural tests pass with 100% success:

```powershell
python -m unittest discover -s "C:\Users\Zachariah\.gemini\antigravity\scratch\tandem\tests" -t "C:\Users\Zachariah\.gemini\antigravity\scratch\tandem" -v
```

### Test Coverage Highlights
- `test_types_and_lattice.py`: Monotonic taint propagation, PINPOINT cryptographic HMAC signatures, parameter type validation.
- `test_registry_and_router.py`: Capability catalog queries, schema coercion, blast-radius detents, e-brake callbacks.
- `test_app_to_hand_haptics.py`: Haptic synthesis across all 3 risk tiers, DualSense 64-byte USB Output Report 0x02 encoding.
- `test_harness_integration.py`: MCP tool export, dynamic tool routing, deep module deletion test.
- `test_transports.py`: In-memory bus, multithreaded queue pipe, Tailscale HTTP network payload taint clamping.

---

## 📂 5. Demos Included

Run the App-to-App federation demo:
```powershell
python "C:\Users\Zachariah\.gemini\antigravity\scratch\tandem\examples\app_to_app_demo.py"
```

Run the App-to-Hand tactile agency demo:
```powershell
python "C:\Users\Zachariah\.gemini\antigravity\scratch\tandem\examples\app_to_hand_demo.py"
```
