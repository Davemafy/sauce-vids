"""Guard source film plans from being overwritten by output receipts."""
from pathlib import Path

def receipt_path(output, film_plan=None):
    output=Path(output)
    candidate=output.with_suffix(".json")
    if film_plan is not None and candidate.resolve()==Path(film_plan).resolve():
        return output.with_name(output.stem+".receipt.json")
    return candidate
