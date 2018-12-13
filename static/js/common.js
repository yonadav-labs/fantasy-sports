function inIframe () {
    try {
        return window.self !== window.top;
    } catch (e) {
        return true;
    }
}
if(inIframe()) {
    $('body').toggleClass('d-none');
} else {
    $('.container-fluid').remove();
    // $('body').toggleClass('d-none');
    $('.lineups-container').toggleClass('container');
    $('.lineups-container').toggleClass('container-iframe');
}
