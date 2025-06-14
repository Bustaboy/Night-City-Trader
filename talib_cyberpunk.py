# Minimal TA-Lib replacement
def version(): return "1.0.0-cyberpunk"
def __getattr__(name): return lambda *args, **kwargs: 0
