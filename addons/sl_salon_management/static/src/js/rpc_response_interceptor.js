/** @odoo-module */

// Intercepts fetch responses and rejects the Promise when server returns
// a JSON payload with {result: false, error: ...} so callers' .catch()
// handlers are triggered and UI can display the error.
(function () {
    if (typeof window === 'undefined' || !window.fetch) {
        return;
    }
    const _originalFetch = window.fetch.bind(window);
    window.fetch = function (...args) {
        return _originalFetch(...args).then(function (response) {
            // clone so we don't consume the original response body
            let cloned = response.clone();
            return cloned.json().then(function (json) {
                if (json && json.result === false) {
                    try {
                        // show a user-friendly alert; website JS may handle more
                        alert(json.error || 'Server validation error');
                    } catch (e) {
                        // ignore UI errors
                    }
                    return Promise.reject(new Error(json.error || 'Server validation error'));
                }
                return response;
            }).catch(function () {
                // not a JSON response or parsing failed -> proceed as normal
                return response;
            });
        });
    };
})();
