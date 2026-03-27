"""
love_core.voice
---------------
Voice I/O primitives.

    from love_core.voice.speak import Speaker, speak
    from love_core.voice.listen import Listener, listen
"""

from love_core.voice.speak  import Speaker, speak
from love_core.voice.listen import Listener, listen

__all__ = ["Speaker", "speak", "Listener", "listen"]
