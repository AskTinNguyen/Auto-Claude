"""Voice metadata data structure for TTS providers."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class VoiceInfo:
    """Voice metadata returned by TTS providers.

    Attributes:
        id: Short identifier (e.g., "lessac", "Samantha")
        name: Display name for UI
        language: Language code (e.g., "en_US", "en-GB")
        provider: Provider name (e.g., "piper", "macos", "system")
        quality: Quality level (e.g., "medium", "high") if applicable
        installed: Whether the voice is currently installed
        filename: Voice file path (for file-based voices like Piper)
        metadata: Additional provider-specific metadata
    """
    id: str
    name: str
    language: str
    provider: str
    quality: Optional[str] = None
    installed: bool = True
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'language': self.language,
            'provider': self.provider,
            'quality': self.quality,
            'installed': self.installed,
            'filename': self.filename,
            'metadata': self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceInfo':
        """Create VoiceInfo from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            language=data['language'],
            provider=data['provider'],
            quality=data.get('quality'),
            installed=data.get('installed', True),
            filename=data.get('filename'),
            metadata=data.get('metadata', {})
        )
