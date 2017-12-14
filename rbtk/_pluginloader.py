"""Loads plugins from :mod:`porcupine.plugins`."""
# many things are wrapped in try/except here to allow writing Porcupine
# plugins using Porcupine, so Porcupine must run if the plugins are
# broken

import importlib
import logging
import pkgutil
import random

import toposort

from rbtk.plugins import __path__ as plugin_paths

log = logging.getLogger(__name__)

def load(shuffle=False):
    # contains names like 'fullscreen', not 'porcupine.plugins.fullscreen'
    plugin_names = {
        name for finder, name, is_pkg in pkgutil.iter_modules(plugin_paths)
        if not name.startswith('_')
    }
    log.info("found %d plugins", len(plugin_names))

    plugin_infos = {}    # {name: (setup_before, setup_after, setup_func)}
    for name in plugin_names.copy():
        log.debug("importing %s", name)
        try:
            module = importlib.import_module('rbtk.plugins.' + name)
            setup_before = set(getattr(module, 'setup_before', []))
            setup_after = set(getattr(module, 'setup_after', []))
            setup = module.setup
        except Exception:
            log.exception("problem with importing %s", name)
            continue

        # now we know that the plugin is ok, we can add its stuff to
        # dependencies and setup_funcs
        plugin_infos[name] = (setup_before, setup_after, setup)

    # setup_before and setup_after may contain names of plugins that are
    # not installed because they are for controlling the loading order,
    # not for requiring dependencies
    def valid_name(name):
        return name in plugin_infos

    dependencies = {name: set() for name in plugin_infos}
    for name, (setup_before, setup_after, setup) in plugin_infos.items():
        dependencies[name].update(filter(valid_name, setup_after))
        for reverse_dependency in filter(valid_name, setup_before):
            dependencies[reverse_dependency].add(name)

    # the toposort will partially work even if there's a circular
    # dependency, the CircularDependencyError is raised after doing
    # everything possible (see source code)
    loading_order = []
    try:
        for names in map(list, toposort.toposort(dependencies)):
            if shuffle:
                random.shuffle(names)
            else:
                names.sort()
            loading_order.extend(names)
    except toposort.CircularDependencyError as e:
        parts = map("{} depends on {}".format, e.data.items())
        log.error("circular dependency: %s", ', '.join(parts))

    for name in loading_order:
        *junk, setup = plugin_infos[name]
        log.debug("running %s.setup()", name)
        try:
            setup()
        except Exception:
            log.exception("%s.setup() doesn't work", name)
