# -*- coding: utf-8 -*-

import gobject
import util
import weakref

import gui.main
import ops.system


class Mediator(object):

    # FIXME: Assumes callbacks are methods, not other callable objects.

    def __init__(self, logging=False):
        self.logging = logging
        self.eventsNoted = []
        self.timeoutsAdded = []
        self._listeners = {}


    def clearLog(self):
        self.eventsNoted = []
        self.timeoutsAdded = []


    def addTimeout(self, timeout, callback):
        assert not isinstance(callback, weakref.ProxyTypes)
        assert not isinstance(callback, util.WeakMethod)

        weakMethod = util.WeakMethod(callback)

        # FIXME: callback probably doesn't get collected.

        def callbackWrapper():
            try:
                return weakMethod()
            except ReferenceError:
                return False

        gobject.timeout_add(timeout, callbackWrapper)

        if self.logging:
            self.timeoutsAdded.append((timeout, weakMethod))


    def addListener(self, listener, *eventClasses):
        assert not isinstance(listener, weakref.ProxyTypes)
        assert not isinstance(listener, util.WeakMethod)

        # FIXME!
        proxy = util.WeakMethod(listener, self._listenerFinalized)
        for eventClass in eventClasses:
            self._listeners.setdefault(eventClass, []).append(proxy)


    def removeListener(self, listener, *eventClasses):
        for eventClass in eventClasses:
            for weakMethod in self._listeners[eventClass]:
                if weakMethod.isSameMethod(listener):
                    self._listeners[eventClass].remove(weakMethod)


    def hasListener(self, listener, eventClass):
        for weakMethod in self._listeners.get(eventClass, ()):
            if weakMethod.isSameMethod(listener):
                return True
        return False


    def noteEvent(self, event):
        if self.logging:
            self.eventsNoted.append(event)
        for listener in self._listeners.get(event.__class__, ()):
            listener(event)


    def _listenerFinalized(self, proxy):
        for l in self._listeners.itervalues():
            if proxy in l:
                l.remove(proxy)


