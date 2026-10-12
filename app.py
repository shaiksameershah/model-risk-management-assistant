from __future__ import annotations
import argparse
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from mrm.extract import extract_inventory
from mrm.validate import apply_guards
from mrm.report import write_json, write_markdown, write_csv
from mrm.schema import InventoryRecord, FieldValue

console = Console()


def _review(record: InventoryRecord) -> InventoryRecord:
    while True:
        stated = sum(1 for v in record.model_dump().values()
                     if isinstance(v, dict) and v.get("status") == "stated")
        inferred = sum(1 for v in record.model_dump().values()
                       if isinstance(v, dict) and v.get("status") == "inferred")
        console.print(f"\n[bold]Stated:[/bold] {stated}  "
                      f"[bold]Inferred:[/bold] {inferred}  "
                      f"[bold]Missing:[/bold] {len(record.missing_information)}  "
                      f"[bold]Contradictions:[/bold] {len(record.contradictions)}")
        action = Prompt.ask("[o]pen [e]dit [a]ccept [q]uit", default="a").lower()
        if action == "a":
            record.human_review_status = "reviewed"
            return record
        if action == "q":
            raise SystemExit(0)
        if action == "o":
            console.print_json(record.model_dump_json())
        if action == "e":
            field = Prompt.ask("field name")
            if not hasattr(record, field):
                console.print(f"[red]unknown field {field}[/red]")
                continue
            new_value = Prompt.ask("new value")
            evidence = Prompt.ask("evidence (verbatim from source, or 'manual')")
            setattr(record, field, FieldValue(
                value=new_value, status="stated",
                evidence=[evidence], confidence=1.0,
            ))
            record.human_review_status = "corrected"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to model description")
    parser.add_argument("--case-id", default=None)
    parser.add_argument("--no-review", action="store_true")
    args = parser.parse_args()

    source = Path(args.input).read_text()
    case_id = args.case_id or Path(args.input).stem

    console.print(f"[bold]Extracting[/bold] {case_id} ...")
    record = extract_inventory(source)
    record = apply_guards(record, source)

    if not args.no_review:
        record = _review(record)

    j = write_json(record, case_id)
    m = write_markdown(record, case_id)
    c = write_csv(record, case_id)
    console.print(f"[green]Wrote[/green] {j}\n[green]Wrote[/green] {m}\n[green]Wrote[/green] {c}")


if __name__ == "__main__":
    main()
