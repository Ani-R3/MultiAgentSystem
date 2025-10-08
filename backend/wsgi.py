"""
This is the production entrypoint for the Gunicorn server.
It ensures that gevent's monkey patching is applied BEFORE any other modules
are imported, which is critical to prevent the RecursionError with SSL.
"""
import gevent.monkey
gevent.monkey.patch_all()

from .app import app

# This is the application object that Gunicorn will run.
# The variable must be named 'application' for some platforms, but 'app' works for Render.
if __name__ == "__main__":
    app.run()
