"""
Ralph Speak Command
==================

Text-to-speech control for voice feedback.
"""

import sys
from pathlib import Path

import click

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..utils.output import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_header,
    create_table,
)


def get_tts_manager():
    """Get TTS manager instance."""
    try:
        from integrations.tts.manager import TTSManager
        return TTSManager()
    except ImportError:
        print_error("TTS module not available. Make sure you're in an Auto-Claude project.")
        raise SystemExit(1)


@click.command()
@click.argument("text", required=False)
@click.option("--auto-on", is_flag=True, help="Enable auto-speak for phase announcements")
@click.option("--auto-off", is_flag=True, help="Disable auto-speak")
@click.option("--auto-status", is_flag=True, help="Show auto-speak status")
@click.option("--list-voices", is_flag=True, help="List available TTS voices")
@click.option("--set-voice", help="Set default voice")
@click.option("--engine", type=click.Choice(["piper", "macos", "system", "auto"]), help="Set TTS engine")
@click.option("--status", is_flag=True, help="Show TTS status")
@click.pass_context
def speak(
    ctx,
    text: str | None,
    auto_on: bool,
    auto_off: bool,
    auto_status: bool,
    list_voices: bool,
    set_voice: str | None,
    engine: str | None,
    status: bool,
) -> None:
    """
    Speak text using TTS or manage TTS settings.

    TEXT is the text to speak. If not provided, use options to manage TTS.

    Examples:
        ralph speak "Build completed"        # Speak text
        ralph speak --status                 # Show TTS status
        ralph speak --list-voices            # List available voices
        ralph speak --engine piper           # Set TTS engine
        ralph speak --auto-on                # Enable auto-announcements
    """
    config = ctx.obj.get("config") if ctx.obj else None

    # Handle status
    if status:
        show_tts_status()
        return

    # Handle list voices
    if list_voices:
        list_available_voices()
        return

    # Handle auto-speak settings
    if auto_on or auto_off or auto_status:
        handle_auto_speak(config, auto_on, auto_off, auto_status)
        return

    # Handle engine/voice settings
    if engine or set_voice:
        handle_settings(config, engine, set_voice)
        return

    # Speak text
    if text:
        tts = get_tts_manager()
        if tts.speak(text):
            print_success("Spoken")
        else:
            print_error("Failed to speak. Check TTS configuration with 'ralph speak --status'")
            raise SystemExit(1)
    else:
        # No text and no options - show help
        ctx.invoke(speak, help=True)


def show_tts_status() -> None:
    """Show TTS status and configuration."""
    print_header("TTS Status")

    try:
        tts = get_tts_manager()
        status = tts.get_status()

        table = create_table()
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        enabled_str = "[green]Enabled[/green]" if status["enabled"] else "[red]Disabled[/red]"
        table.add_row("Status", enabled_str)
        table.add_row("Active Provider", status.get("active_provider") or "[dim]None[/dim]")
        table.add_row("Provider Info", status.get("active_provider_info") or "[dim]N/A[/dim]")
        table.add_row("Available Providers", ", ".join(status.get("available_providers", [])) or "[dim]None[/dim]")

        console.print(table)

        # Config details
        config = status.get("config", {})
        if config:
            console.print()
            console.print("[bold]Configuration:[/bold]")
            console.print(f"  Max Length: {config.get('max_length', 'N/A')} characters")
            console.print(f"  Announce Phases: {config.get('announce_phases', False)}")
            console.print(f"  Announce Subtasks: {config.get('announce_subtasks', False)}")
            console.print(f"  Announce QA: {config.get('announce_qa', False)}")

    except Exception as e:
        print_error(f"Could not get TTS status: {e}")


def list_available_voices() -> None:
    """List available TTS voices."""
    print_header("Available TTS Voices")

    # Piper voices
    console.print("[bold]Piper Voices:[/bold]")
    piper_voices = [
        ("alba", "Scottish English female"),
        ("lessac", "American English female"),
        ("amy", "British English female"),
        ("jenny", "American English female"),
        ("ryan", "British English male"),
    ]
    for voice_id, description in piper_voices:
        console.print(f"  - {voice_id}: {description}")

    # macOS voices
    console.print()
    console.print("[bold]macOS Voices (if available):[/bold]")
    macos_voices = [
        ("Samantha", "American English female"),
        ("Alex", "American English male"),
        ("Daniel", "British English male"),
        ("Karen", "Australian English female"),
    ]
    for voice_id, description in macos_voices:
        console.print(f"  - {voice_id}: {description}")

    console.print()
    print_info("Set voice with: ralph speak --set-voice <voice>")


def handle_auto_speak(config, auto_on: bool, auto_off: bool, auto_status: bool) -> None:
    """Handle auto-speak settings."""
    if auto_status:
        if config:
            enabled = config.tts.auto_speak
            status_str = "[green]Enabled[/green]" if enabled else "[red]Disabled[/red]"
            console.print(f"Auto-speak: {status_str}")
        else:
            console.print("Auto-speak: [dim]Not configured[/dim]")
        return

    if auto_on:
        if config:
            config.tts.auto_speak = True
            config.save()
            print_success("Auto-speak enabled")
            print_info("Phase announcements will be spoken automatically")
        else:
            print_warning("No config file found. Run 'ralph init' first.")
        return

    if auto_off:
        if config:
            config.tts.auto_speak = False
            config.save()
            print_success("Auto-speak disabled")
        else:
            print_warning("No config file found. Run 'ralph init' first.")
        return


def handle_settings(config, engine: str | None, voice: str | None) -> None:
    """Handle TTS settings changes."""
    if not config:
        print_warning("No config file found. Run 'ralph init' first.")
        return

    if engine:
        config.tts.provider = engine
        print_success(f"TTS engine set to: {engine}")

    if voice:
        config.tts.voice = voice
        print_success(f"TTS voice set to: {voice}")

    if engine or voice:
        config.save()
