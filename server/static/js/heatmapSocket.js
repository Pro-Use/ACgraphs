$(document).ready(function() {
    namespace = '/graphSock';
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);



    socket.on('connect', function() {
                console.log('I\'m connected!');
            });

    socket.on('update-heatmap', function(msg) {
        console.log(msg)
        console.log('Updating heatmap')
        addPoint(msg.lat, msg.lng);
    });

    var screen_num = 2;
    var current_bg = null

    socket.on('update-bg', function(msg) {
        console.log(msg)
        if (msg.screens.includes(screen_num)) {
            $("#bg_"+msg.bg).show();
            if (current_bg != null) {
                $("#bg_"+current_bg).hide();
            }
            current_bg = msg.bg;
        }
    });

    for (i = 0; i < 11; i++) {
        $('body').append('<div id=bg_'+i+' class=page-bg></div>');
        $("#bg_"+i).css("background-image", "url('static/images/b"+i+"_"+screen_num+".jpg')")
    }

    $('body').css('cursor', 'none');
 });