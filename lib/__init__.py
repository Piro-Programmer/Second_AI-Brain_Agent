import sys

# Windows consoles default to cp1252; LLM summaries often contain characters it can't
# encode (e.g. non-breaking hyphens), which crashed the pipeline on a plain print().
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
