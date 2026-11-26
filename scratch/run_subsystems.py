import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.subsystem_synthesizer import run_subsystem_recovery

output_dir = Path("output/nav2_pipeline")
model = run_subsystem_recovery(
    nodes_json_path=output_dir / "nodes.json",
    communication_graph_path=output_dir / "communication_graph.json",
    launches_json_path=output_dir / "launches.json",
    output_path=output_dir / "subsystem_model.json"
)

print(f"Recovered {len(model.subsystems)} subsystems.")
for s in model.subsystems:
    print(f"  - Subsystem: {s.name} ({len(s.nodes)} nodes, role={s.architectural_role}, cohesion={s.intra_cohesion_score}, coupling={s.inter_coupling_score})")
    for n in s.nodes:
        print(f"      * {n}")
print("\nReference comparison:")
print(model.reference_comparison)
