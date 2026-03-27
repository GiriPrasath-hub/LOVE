"""
love_core.commands
------------------
Built-in command modules.  Import and call register_all() to load
any module's commands into a registry.

    from love_core.commands import browser, apps, system

    browser.register_all(registry=my_registry)
    apps.register_all(registry=my_registry)
    system.register_all(registry=my_registry)
"""

from love_core.commands import browser, apps, system

__all__ = ["browser", "apps", "system"]
