export function getURLParameterByName(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}



export function loadStateFromHash() {
    // TODO: verify that the hash data makes sense?
    return JSON.parse(decodeURIComponent(document.location.hash).slice(1));
}


export function setHashFromState(state) {
    let hash = JSON.stringify({
        layout: state.data.dashboardLayout,
        content: state.data.dashboardContent,
        cardType: state.data.dashboardCardType
    })
    document.location.hash = hash;
}


export function debounce(func, wait, immediate) {
    var timeout;
    return function() {
	var context = this, args = arguments;
	var later = function() {
	    timeout = null;
	    if (!immediate) func.apply(context, args);
	};
	var callNow = immediate && !timeout;
	clearTimeout(timeout);
	timeout = setTimeout(later, wait);
	if (callNow) func.apply(context, args);
    };
};
