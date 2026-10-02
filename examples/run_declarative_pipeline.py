"""
Unimage End-to-End Demonstration: Declarative Intent & Saga Auto-Repair
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from unimage.client import UnimageClient
from unimage.protocol.schema import (
    DeclarativeMediaRequest,
    MediaIntent,
    MediaAnchor,
    MediaRequirements,
    LifecyclePolicy,
    Dimensions,
    QualityThresholds
)
from unimage.protocol.types import (
    TaskType,
    AnchorType,
    FidelityLevel,
    RoutingStrategy
)

console = Console()

async def main():
    console.print(Panel.fit(
        "[bold cyan]UNIMAGE: Capability-based Generative Media Runtime Layer (CMRL)[/bold cyan]\n"
        "[dim]Demonstrating Declarative Intent, Dynamic DAG Compilation, and Saga Repair Loops[/dim]",
        border_style="cyan"
    ))

    # 1. User / Agent expresses high-level declarative intent (NO model specified!)
    request = DeclarativeMediaRequest(
        intent=MediaIntent(
            task=TaskType.CHARACTER_CONSISTENT_EDIT,
            action="scene_transfer",
            prompt="把该角色置于霓虹闪烁的赛博朋克雨夜街道中，手持全息数据板，光影投射在面部",
            negative_prompt="blurry, distorted face, extra fingers, cartoonish, low resolution"
        ),
        anchors=[
            MediaAnchor(
                id="char_master_face",
                type=AnchorType.IDENTITY,
                source_uri="s3://unimage-assets/character_master_ref.png",
                target_region="face",
                fidelity=FidelityLevel.STRICT,
                influence_weight=0.85
            )
        ],
        requirements=MediaRequirements(
            dimensions=Dimensions(width=1280, height=720),
            max_cost_cents=8.0,
            max_latency_ms=7000,
            routing_strategy=RoutingStrategy.PARETO_OPTIMAL,
            quality_thresholds=QualityThresholds(
                face_similarity=0.85,
                aesthetic_score=0.80
            )
        ),
        lifecycle_policy=LifecyclePolicy(
            retain_intermediate_latents=True,
            allow_saga_repair=True,
            max_repair_passes=2
        )
    )

    console.print("[bold yellow]1. Submitted Declarative Request:[/bold yellow]")
    console.print(f"  * Task: [green]{request.intent.task.value}[/green]")
    console.print(f"  * Prompt: \"{request.intent.prompt}\"")
    console.print(f"  * Anchors: {len(request.anchors)} anchor(s) (Face Identity, Fidelity: {request.anchors[0].fidelity.value})")
    console.print(f"  * Target SLA: Face Similarity >= {request.requirements.quality_thresholds.face_similarity}")
    console.print(f"  * Resolution: {request.requirements.dimensions.width}x{request.requirements.dimensions.height}\n")

    # 2. Dispatch to Unimage Client
    client = UnimageClient()

    console.print("[bold blue]2. Compiling Declarative Intent into Physical Execution DAG...[/bold blue]")
    result = await client.dispatch(request)

    # 3. Display Execution Results & Trace
    console.print("\n[bold green]3. Execution Completed! Trace Log:[/bold green]")
    
    table = Table(title="Saga Execution DAG Trace", border_style="bright_blue")
    table.add_column("Step ID", style="cyan", no_wrap=True)
    table.add_column("Operator", style="magenta")
    table.add_column("Provider / Model", style="yellow")
    table.add_column("Status", style="bold")
    table.add_column("Duration", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("Evaluated Metrics / Notes", style="dim")

    for trace in result.execution_trace:
        status_color = "green" if trace.status.value == "completed" else "yellow" if trace.status.value == "skipped" else "red"
        metric_str = ", ".join([f"{k}={v}" for k, v in trace.evaluation_metrics.items()]) if trace.evaluation_metrics else (trace.notes or "-")
        table.add_row(
            trace.step_id,
            trace.operator_name,
            f"{trace.provider} ({trace.model})",
            f"[{status_color}]{trace.status.value.upper()}[/{status_color}]",
            f"{trace.duration_ms} ms",
            f"${trace.cost_cents/100:.4f}",
            metric_str
        )

    console.print(table)

    # 4. Summary Banner
    sla_status = "[bold green]PASSED[/bold green]" if result.sla_passed else "[bold red]FAILED[/bold red]"
    console.print(Panel(
        f"[bold]Final Deliverable Asset:[/bold] {result.final_asset_uri}\n"
        f"[bold]Latent Cache Key:[/bold] {result.session_latent_key}\n"
        f"[bold]SLA Gate Check:[/bold] {sla_status}\n"
        f"[bold]Saga Auto-Repair Passes:[/bold] {result.repaired_passes}\n"
        f"[bold]Total Wall Time:[/bold] {result.total_latency_ms} ms\n"
        f"[bold]Total Cost:[/bold] ${result.total_cost_cents / 100:.4f} ({result.total_cost_cents} cents)\n"
        f"[bold]Final Evaluation:[/bold] {json.dumps(result.evaluation_summary, indent=2)}",
        title="Execution Summary",
        border_style="green" if result.sla_passed else "red"
    ))

if __name__ == "__main__":
    asyncio.run(main())
