"""Sauce Vids native Hermes tool registration."""
from pathlib import Path
from . import tools, schemas, director, autopilot, studio_tools

def register(ctx):
    for name, handler, schema in (
        ("sauce_capture", tools.capture, schemas.CAPTURE),
        ("sauce_render", tools.render, schemas.RENDER),
        ("sauce_inspect", tools.inspect, schemas.INSPECT),
        ("sauce_scout", director.scout, schemas.SCOUT),
        ("sauce_plan", director.plan, schemas.PLAN),
        ("sauce_review", director.review, schemas.REVIEW),
        ("sauce_auto", autopilot.run, schemas.AUTO),
        ("sauce_compose", studio_tools.compose, schemas.COMPOSE),
        ("sauce_preview", studio_tools.preview, schemas.PREVIEW),
        ("sauce_render_project", studio_tools.render_project, schemas.RENDER_PROJECT),
    ):
        ctx.register_tool(name=name, toolset="sauce_vids", schema=schema, handler=handler)
    ctx.register_skill("sauce-director", str(Path(__file__).parent / "skills" / "sauce-director" / "SKILL.md"))
