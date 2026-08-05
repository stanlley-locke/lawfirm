// Generic, reusable dashboard auto-refresh poller.
//
// Pages opt in by calling window.DashboardAutoRefresh.start({...}). The
// poller only ever touches the specific DOM nodes a page's `onData`
// callback decides to update, so it never disrupts scroll position, open
// dropdowns/collapses, or in-progress form input elsewhere on the page.
(function (window, document) {
    'use strict';

    function formatTime(date) {
        try {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return date.toString();
        }
    }

    function resolveEl(target) {
        if (!target) return null;
        return typeof target === 'string' ? document.querySelector(target) : target;
    }

    function start(options) {
        var url = options.url;
        var intervalMs = options.intervalMs || 20000;
        var onData = typeof options.onData === 'function' ? options.onData : function () {};
        var lastUpdatedEl = resolveEl(options.lastUpdatedEl);
        var indicatorEl = resolveEl(options.indicatorEl) || lastUpdatedEl;

        var timer = null;
        var inFlight = false;

        function setIndicatorState(state) {
            if (!indicatorEl) return;
            indicatorEl.classList.remove('is-refreshing', 'is-error');
            if (state === 'refreshing') indicatorEl.classList.add('is-refreshing');
            if (state === 'error') indicatorEl.classList.add('is-error');
        }

        function tick() {
            if (inFlight || document.hidden || !url) return;
            inFlight = true;
            setIndicatorState('refreshing');

            fetch(url, { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function (response) {
                    if (response.status === 401 || response.status === 403 || response.redirected) {
                        stop();
                        return null;
                    }
                    if (!response.ok) throw new Error('Dashboard refresh request failed: ' + response.status);
                    var contentType = response.headers.get('content-type') || '';
                    if (contentType.indexOf('application/json') === -1) {
                        stop();
                        return null;
                    }
                    return response.json();
                })
                .then(function (data) {
                    if (!data) return;
                    onData(data);
                    if (lastUpdatedEl) {
                        lastUpdatedEl.textContent = 'Updated ' + formatTime(new Date());
                    }
                    setIndicatorState('idle');
                })
                .catch(function (err) {
                    console.error('Dashboard auto-refresh failed:', err);
                    setIndicatorState('error');
                })
                .finally(function () {
                    inFlight = false;
                });
        }

        function stop() {
            if (timer !== null) {
                clearInterval(timer);
                timer = null;
            }
        }

        // Refresh promptly again when the tab regains focus/visibility,
        // rather than waiting out a stale interval.
        document.addEventListener('visibilitychange', function () {
            if (!document.hidden) tick();
        });

        timer = setInterval(tick, intervalMs);

        return { stop: stop, refreshNow: tick };
    }

    window.DashboardAutoRefresh = { start: start };
})(window, document);
