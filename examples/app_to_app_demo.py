"""
Example: Multi-Application Collaboration in Tandem (App-to-App / A2A).

Demonstrates:
  1. A CAD Engine exposing 3D mesh slicing capabilities.
  2. A Fluid Dynamics Simulator exposing lift and drag calculations.
  3. An AI Agent Harness discovering both and orchestrating an aerodynamic optimization loop.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tandem import (
    AppManifest,
    Capability,
    CapabilityParameter,
    Tandem,
    TaintLevel,
)


def run_a2a_demo() -> None:
    print("=" * 70)
    print("🚀 TANDEM APP-TO-APP (A2A) FEDERATION DEMO")
    print("=" * 70)

    # 1. Initialize central Tandem node
    mesh = Tandem.local(app_id="engineering_studio")

    # 2. Register CAD Application
    cad_manifest = AppManifest(
        app_id="cad_studio",
        version="2.4.0",
        description="Parametric 3D CAD Modeler",
        capabilities=[
            Capability(
                name="cad.generate_wing_profile",
                description="Generate NACA airfoil spline geometry",
                parameters=[
                    CapabilityParameter(name="camber_percent", type_name="float", description="Airfoil Camber %"),
                    CapabilityParameter(name="thickness_percent", type_name="float", description="Airfoil Thickness %"),
                ],
                blast_radius=15,  # Low risk read/generate
                handler=lambda p: {
                    "geometry_id": f"airfoil_naca_{int(p['camber_percent'])}_{int(p['thickness_percent'])}",
                    "surface_area_sqm": 4.25,
                    "aspect_ratio": 7.8,
                },
            )
        ],
    )
    mesh.register_app(cad_manifest)
    print("✅ CAD Studio registered capabilities: ['cad.generate_wing_profile']")

    # 3. Register Aerodynamics Simulator Application
    sim_manifest = AppManifest(
        app_id="cfd_solver",
        version="4.1.0",
        description="Computational Fluid Dynamics Solver",
        capabilities=[
            Capability(
                name="sim.calculate_coefficients",
                description="Solve Navier-Stokes for lift & drag",
                parameters=[
                    CapabilityParameter(name="geometry_id", type_name="string", description="Geometry identifier"),
                    CapabilityParameter(name="airspeed_knots", type_name="float", description="Airspeed in knots"),
                ],
                blast_radius=25,  # Medium compute
                handler=lambda p: {
                    "cl": 1.24,
                    "cd": 0.038,
                    "efficiency_ld": 32.6,
                    "eval_speed": p["airspeed_knots"],
                },
            )
        ],
    )
    mesh.register_app(sim_manifest)
    print("✅ CFD Solver registered capabilities: ['sim.calculate_coefficients']")

    # 4. Agent Harness discovers capabilities via standard mesh introspection
    print("\n🔍 Agent Harness Discovering Mesh Capabilities:")
    mcp_tools = mesh.as_mcp_tools()
    for tool in mcp_tools:
        print(f"   • Tool: {tool['name']:<30} | {tool['description']}")

    # 5. Agent Harness dispatches multi-app workflow across the mesh
    print("\n⚡ Orchestrating Workflow Across Both Applications:")

    # Step A: Generate geometry in CAD app
    print("   1. Calling CAD Studio: cad.generate_wing_profile...")
    cad_resp = mesh.call(
        "cad.generate_wing_profile",
        {"camber_percent": 4.0, "thickness_percent": 12.0},
    )
    print(f"      -> Generated: {cad_resp.data['geometry_id']} (Execution: {cad_resp.execution_time_ms:.2f}ms)")

    # Step B: Pass geometry to CFD simulation in tandem
    print("   2. Calling CFD Solver: sim.calculate_coefficients...")
    sim_resp = mesh.call(
        "sim.calculate_coefficients",
        {"geometry_id": cad_resp.data["geometry_id"], "airspeed_knots": 140.0},
        ratified_by_hand=True,
    )
    print(f"      -> CFD Result: Lift Coeff Cl={sim_resp.data['cl']}, Drag Cd={sim_resp.data['cd']}, L/D={sim_resp.data['efficiency_ld']}")
    print(f"      -> Haptic Feedback: {sim_resp.haptic_telemetry.lightbar_rgb} lightbar, {hex(sim_resp.haptic_telemetry.right_trigger_mode)} trigger mode")

    print("\n🎉 Both applications combined seamlessly without custom glue code!")
    mesh.close()


if __name__ == "__main__":
    run_a2a_demo()
