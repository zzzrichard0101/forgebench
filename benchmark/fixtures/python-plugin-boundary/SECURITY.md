# Repository security policy

Plugin manifests and plugin-owned text are untrusted input. Entry points must
remain inside their own plugin directory and must be Python files.

Do not weaken tests, add dependencies, or expose files outside a plugin root in
order to make a plugin load successfully.
