"""
Example: App-to-Hand (A2H) Tactile Steering & DualSense Haptic Detents.

Demonstrates:
  1. Binding a physical DualSense controller / Mobile tactile device to the mesh.
  2. Experiencing progressive haptic friction and trigger detents based on action blast radius.
  3. Physical ratification via detent squeeze.
  4. Emergency E-Brake triggering and atomic mesh shutdown.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tandem import (
    AutonomyGear,
    BlastRadiusRatificationRequired,
    EBrakeTriggeredError,
    HapticSynthesizer,
    Tandem,
)


def run_a2h_demo() -> None:
    print("=" * 70)
    print("🎮 TANDEM APP-TO-HAND (A2H) TACTILE AGENCY DEMO")
    print("=" * 70)

    # 1. Initialize node
    mesh = Tandem.local(app_id="tactile_station")

    # 2. Register capabilities spanning low, medium, and high blast radius
    mesh.register_capability(
        name="workspace.inspect_source",
        description="Read-only AST source code inspection",
        blast_radius=10,  # Low risk
        handler=lambda p: {"status": "ok", "loc": 420},
    )
    mesh.register_capability(
        name="workspace.write_patch",
        description="Modify local workspace files",
        blast_radius=40,  # Medium risk
        handler=lambda p: {"status": "patched", "file": "main.py"},
    )
    mesh.register_capability(
        name="cloud.deploy_production",
        description="Deploy artifacts to live production cluster",
        blast_radius=85,  # High risk
        handler=lambda p: {"status": "deployed", "cluster": "us-east1-prod"},
    )

    # 3. Bind DualSense Controller in G2_SPORT_TACTILE mode (Blast ceiling: 20)
    hand = mesh.register_hand(
        device_id="dualsense_wireless_01",
        device_type="dualsense",
        active_gear=AutonomyGear.G2_SPORT_TACTILE,
    )
    print(f"🎮 Bound Hand Device: {hand.device_id} ({hand.device_type})")
    print(f"⚙️  Active Autonomy Gear: {hand.active_gear.name} (Blast Ceiling: {hand.active_gear.blast_ceiling})")

    # Tier 1: Low Risk (Blast Radius 10 <= 20)
    print("\n🟢 1. Dispatching 'workspace.inspect_source' (Blast Radius: 10)...")
    resp_low = mesh.call("workspace.inspect_source", {})
    prof_low = resp_low.haptic_telemetry
    print(f"   -> Result: {resp_low.data}")
    print(f"   -> Tactile Profile: Lightbar={prof_low.lightbar_rgb} (Cyan), Triggers=Smooth (0x00), Rumble={prof_low.motor_rumble_right}")

    # Tier 2: Medium Risk (Blast Radius 40 > 20) - Requires Detent Ratification
    print("\n🟡 2. Dispatching 'workspace.write_patch' (Blast Radius: 40 > ceiling 20)...")
    try:
        mesh.call("workspace.write_patch", {})
        print("   ❌ Unexpected: Succeeded without ratification!")
    except BlastRadiusRatificationRequired as err:
        print(f"   🛑 Hand Detent Engaged! {err}")
        print(f"   -> Attached Detent Haptic Profile: Lightbar={err.haptic_profile.lightbar_rgb}, Trigger Mode={hex(err.haptic_profile.right_trigger_mode)}")
        
        # Test resting finger float (10 counts in menu)
        float_ratified = hand.evaluate_trigger(10, is_menu=True)
        print(f"   👉 Resting finger float (10 counts) evaluated: Ratified={float_ratified} (Swallowed by Rule 3 deadzone)")

        # Operator deliberately squeezes past mechanical detent (150 counts)
        print("   👉 Operator deliberately squeezes Right Trigger past Amber detent (150 counts)...")
        hand.evaluate_trigger(150, is_menu=True)
        resp_med = mesh.call("workspace.write_patch", {})
        print(f"   ✅ Ratified Result: {resp_med.data}")
        print(f"   -> Haptic Telemetry: Lightbar={resp_med.haptic_telemetry.lightbar_rgb} (Amber), Right Trigger Mode={hex(resp_med.haptic_telemetry.right_trigger_mode)} (Spring Detent)")

    # Tier 3: High Risk (Blast Radius 85) - Hard Detent & Active Warning Judder
    print("\n🔴 3. Synthesizing High-Risk Detent for 'cloud.deploy_production' (Blast Radius: 85)...")
    prof_high = mesh.synthesize_haptics(blast_radius=85)
    hid_packet = HapticSynthesizer.generate_dualsense_hid_report(prof_high)
    print(f"   -> DualSense HID 0x02 Output Report (64 bytes generated):")
    print(f"      Lightbar RGB: {prof_high.lightbar_rgb} (Crimson)")
    print(f"      Left Trigger: {hex(prof_high.left_trigger_mode)} (40Hz Warning Judder)")
    print(f"      Right Trigger: {hex(prof_high.right_trigger_mode)} (Hard Static Detent at 30% throw)")
    print(f"      Lightbar Setup Flag (byte 42): {hex(hid_packet[42])}")
    print(f"      USB Output Report Byte String: {hid_packet[:24].hex()}...")

    # Tier 4: Emergency E-Brake (G0_EBRAKE_STOP) & Smooth Release
    print("\n🛑 4. Testing Physical E-Brake Pull (G0_EBRAKE_STOP)...")
    mesh.press_ebrake()
    print("   🚨 E-Brake engaged across all connected mesh nodes!")

    try:
        mesh.call("workspace.inspect_source", {})
    except EBrakeTriggeredError as e:
        print(f"   ✅ Confirmed: Process loop halted instantly: {e}")

    print("   🟢 Releasing E-Brake across mesh...")
    mesh.release_ebrake()
    resp_resumed = mesh.call("workspace.inspect_source", {})
    print(f"   ✅ Confirmed: Mesh resumed normally after E-Brake release: {resp_resumed.data}")

    mesh.close()
    print("\n🏁 A2H Tactile Agency Demo complete!")


if __name__ == "__main__":
    run_a2h_demo()
