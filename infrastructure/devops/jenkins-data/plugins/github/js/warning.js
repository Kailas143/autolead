var InlineWarning = (function () {
    'use strict';
    var exports = {};
    var options = {
        id: '',    // id of element to bind
        url: '',   // url of check method
        input: ''  // checkbox to test for checked
    };

    exports.setup = function (opts) {
        options = opts;
        return exports;
    };

    exports.start = function () {
        // Ignore when GH trigger unchecked
        if (!document.querySelector(options.input).checked) {
            return;
        }
        var frequency = 10;
        var decay = 2;
        var lastResponseText;
        var fetchData = function () {
            fetch(options.url).then((rsp) => {
                rsp.text().then((responseText) => {
                    if (responseText !== lastResponseText) {
                        document.getElementById(options.id).innerHTML = responseText;
                        lastResponseText = responseText;
                        frequency = 10;
                    } else {
                        frequency *= decay;
                    }
                    setTimeout(fetchData, frequency * 1000);
                });
            });
        };
        fetchData();
    };

    return exports;
})();

document.addEventListener('DOMContentLoaded', function() {
    var warningElement = document.getElementById('gh-hooks-warn');

    if (warningElement) {
        var url = warningElement.getAttribute('data-url');
        var input = warningElement.getAttribute('data-input');

        if (url && input) {
            InlineWarning.setup({
                id: 'gh-hooks-warn',
                url: url,
                input: input
            }).start();
        } else {
            console.error('URL or Input is null');
        }
    } else {
        console.error('Element with ID "gh-hooks-warn" not found');
    }
});